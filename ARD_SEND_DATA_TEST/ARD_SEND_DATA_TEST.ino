#include <ArduinoBLE.h>
#include <SPI.h>
#include <Wire.h>

// BLE Service and Characteristic
BLEService customService("180F"); // Custom BLE Service
BLECharacteristic customCharacteristic("2A19", BLERead | BLEWrite, 20);

void setup() {
  Serial.begin(9600);
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
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
  // Wait for a BLE central to connect
  BLEDevice central = BLE.central();

  // If central is connected to peripheral
  if (central) {
    Serial.print("Connected to central MAC: ");
    Serial.println(central.address());  // Central's BT address:

    digitalWrite(LED_BUILTIN, HIGH);  // Turn on the LED to indicate the connection

    while (central.connected()) {
      // Example hardcoded data to simulate SD card contents
      String simulatedData[] = {
        "Data chunk 1",
        "Data chunk 2",
        "Data chunk 3",
        "Data chunk 4",
        "Data chunk 5",
        "9999"  // This is a termination signal to indicate the end
      };
      
      // Send data chunks over BLE
      for (int i = 0; i < 6; i++) {
        String dataChunk = simulatedData[i];
        customCharacteristic.writeValue(dataChunk.c_str());  // Send as a C-style string
        Serial.print("Sent data: ");
        Serial.println(dataChunk);
        delay(1000); // Wait a second between sends
      }

      // Break the loop to stop sending data after one cycle
      break;
    }

    digitalWrite(LED_BUILTIN, LOW);  // When the central disconnects, turn off the LED
    Serial.print("Disconnected from central MAC: ");
    Serial.println(central.address());
  }
}
