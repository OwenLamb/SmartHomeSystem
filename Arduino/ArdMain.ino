#include <SD.h>
#include <SPI.h>
#include <Wire.h>
#include <ArduinoBLE.h>

#define SD_ChipSelectPin 10
#define I2C_Start_Saving 01
#define I2C_Stop_Saving 03

// BLE Service and Characteristic
BLEService customService("180F");  // Custom BLE Service
BLECharacteristic customCharacteristic("2A19", BLERead | BLEWrite, 20);

File sFile;
boolean fileOpen = false;
unsigned int blocksWritten = 0;
void receiveEvent();
boolean stopListening = false;

void setup() {
  pinMode(A0, INPUT);
  pinMode(6, OUTPUT);
  pinMode(2, INPUT_PULLUP);


  SD.begin(SD_ChipSelectPin);

  Wire.begin(8);
  Wire.onReceive(receiveEvent);

  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1)
      ;
  }

  // Setup BLE
  BLE.setLocalName("ArduinoBLE");
  BLE.setAdvertisedService(customService);
  customService.addCharacteristic(customCharacteristic);
  BLE.addService(customService);

  BLE.advertise();
  Serial.print("Peripheral device MAC: ");
  Serial.println(BLE.address());
  Serial.println("Waiting for connections…");
}

void loop() {


  // Everything is driven by the I2C data receive callback.
  // When the first block is received, it will create a new WAV file with the
  // appropriate header and set the file position for samples.

  // Then, every received byte is written to the data section of the WAV.
  // When a "stop" byte comes over the wire -- defined above, (an odd number
  // because our 12-bit samples are never odd), it stops listening and fixes
  // the WAV file to accurately show the new filesize.
}

///////////////////////////////////////////////////////////////////
/////////////  WRITE FILE HEADER FOR WAVE//////////////////////////
///////////////////////////////////////////////////////////////////
void createSDFile(const char* filename, unsigned int sampleRate) {
  //wipe file from previous run
  if (SD.exists(filename)) { SD.remove(filename); }

  if (sFile == NULL) {
    Serial.println("failed to open for writing");
    return;
  } else {

    sFile = SD.open(filename, O_CREAT | O_WRITE);
    //if(sFile.fileSize() > 44 ){ sFile.truncate(44);}
    if (!sFile) {
      Serial.println("failed to open for writing");
      return;
    } else {

      //Serial.print("Sr: ");
      //Serial.println(sampleRate);
      sFile.seek(0);
      byte data[] = { 16, 0, 0, 0, 1, 0, 1, 0, lowByte(sampleRate), highByte(sampleRate) };
      sFile.write((byte*)"RIFF    WAVEfmt ", 16);
      sFile.write((byte*)data, 10);
      //unsigned int byteRate = (sampleRate/8)*monoStereo*8;
      //byte blockAlign = monoStereo * (bps/8);
      //it's okay just to hardcode this stuff:
      data[0] = 0;
      data[1] = 0;
      data[2] = lowByte(sampleRate);
      data[3] = highByte(sampleRate);  //Should be byteRate
      data[4] = 0;
      data[5] = 0;
      data[6] = 1;  //BlockAlign
      data[7] = 0;
      data[8] = 8;
      data[9] = 0;
      sFile.write((byte*)data, 10);
      sFile.write((byte*)"data    ", 8);
      //Serial.print("siz");
      //Serial.println(sFile.size());
      //should be the 44 bytes of the file header and the first data block intro
      sFile.close();
    }
  }
}

// This function goes back and fixes the WAV header at the end
void finalizeSDFile(const char* filename) {
  //disable();

  unsigned long fSize = 0;


  sFile = SD.open(filename, O_READ | O_WRITE);

  if (!sFile) {
    Serial.println("failed");
    return;
  }
  fSize = sFile.size() - 8;
  //fix filesize info in the wav file for the actual final count
  //write filesize:
  sFile.seek(4);
  byte data[4] = { lowByte(fSize), highByte(fSize), (byte)(fSize >> 16), (byte)(fSize >> 24) };
  sFile.write(data, 4);
  sFile.seek(40);
  fSize = fSize - 36;
  //write the amount of it that is the raw samples, minus metadata/headers:
  data[0] = lowByte(fSize);
  data[1] = highByte(fSize);
  data[2] = (byte)(fSize >> 16);
  data[3] = (byte)(fSize >> 24);
  sFile.write((byte*)data, 4);
  sFile.close();

  /* check our work and print to serial monitor
    sFile = SD.open(filename);

    if(ifOpen()){

            while (fPosition() < 44) {
              Serial.print(sFile.read(),HEX);
              Serial.print(":");
            }
            Serial.println("");

        //Serial.println(sFile.size());
        sFile.close();
    }*/
}



///////////////////////////////////////////////////////////////////
/////////////  I2C Stuff                 //////////////////////////
///////////////////////////////////////////////////////////////////
void requestEvent() {
  // nothing for now
  return;
}

void receiveEvent(int howMany) {
  //this function will include the logic of "which part" of the file we are on
  // We want to receive a 8 KB data burst from the STM
  // 11/25 the arduino library is way too small for that

  if (stopListening) return;  //for debug, we only ever want one transmission

  while (0 < Wire.available())  // loop through all in 'stream' buffer
  {
    byte b = Wire.read();  // receive byte
    //handle I2C control sequences (we define these)
    if (b == I2C_Start_Saving && sFile == NULL) {
      createSDFile("file.wav", 44000);
      continue;
    } else if (b == I2C_Stop_Saving || blocksWritten > 127) {
      finalizeSDFile("file.wav");
      stopListening = true;
      sendFile("file.wav");
      break;
    }
    //otherwise process as normal:
    if (sFile != NULL) {
      sFile.print(b);
      blocksWritten++;
      //Serial.print((char)b);
    } else {
      Serial.println("Heard data but no file ready");
      createSDFile("file.wav", 44000);
      break;  //according to docs we don't have to flush the buffer
    }
  }
}

void sendFile(const char* filename) {
  bool stopSending = false;
  while (!stopSending) {
    // Wait for a BLE central to connect
    BLEDevice central = BLE.central();

    // If central is connected to peripheral
    if (central) {
      Serial.print("Connected to central MAC: ");
      Serial.println(central.address());  // Central's BT address:

      sFile = SD.open(filename);

      //send start command
      customCharacteristic.writeValue("3");

      while (central.connected()) {
        if (ifOpen()) {
          int i = 0;
          while (i != sFile.fileSize()) {
            customCharacteristic.writeValue(sFile.read());
            ++i;
          }
          //Send termination signal
          customCharacteristic.writeValue("9999");
          sFile.close();
        }
      }
      Serial.print("Disconnected from central MAC: ");
      Serial.println(central.address());
    }
  }
}
