#--------------SETUP GOOGLE SR--------------
import speech_recognition as sr
r = sr.Recognizer()

#---------------SETUP AI--------------------
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# Define the template for the assistant
template = """
{user_input}
"""
# Initialize the model
model = OllamaLLM(model="tinyllama")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

#--
def byte_array_to_string(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232
    value = bytearray(value)
    value = value.decode('utf-8')
    return value

#-------------------SETUP Bluetooth-------------
from bluepy import btle  
import time
import wave  # Import wave module to write WAV files

#Use terminal command "sudo hcitool lescan" to find MAC
# Define a notification handler class
class MyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
    
    def handleNotification(self, cHandle, data):
        # This method gets called whenever a notification is received
        print("Notification received:", data)
        dataString = byte_array_to_string(data)
        print("Data (converted to string):", dataString)

# Set up the BLE device with the delegate
nano_sense = btle.Peripheral(mac_address)
nano_sense.setDelegate(MyDelegate())

# Enable notifications for the characteristic
BlueCHAR = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]
nano_sense.writeCharacteristic(BlueCHAR.getHandle() + 1, b'\x01\x00', withResponse=True)

# Loop to wait for notifications
while True:
    if nano_sense.waitForNotifications(1.0):
        continue

mac_address = "92:32:7E:F5:B4:3F"
SERVICE_UUID = "180F" # These two need configured the same as Arduino
CHARACTERISTIC_UUID = "2A19"

#Sometimes need to turn bluetooth off then on if it crashes here idk why
print("Connecting…")
nano_sense = btle.Peripheral(mac_address)
 
print("Discovering Services…")
_ = nano_sense.services
bleService = nano_sense.getServiceByUUID(SERVICE_UUID)
 
print("Discovering Characteristics…")
_ = bleService.getCharacteristics()

#--------------------SETUP Text to Speech------------
import os

#--------------------SETUP GPIO-----------------
import RPi.GPIO as GPIO 
from time import sleep 
GPIO.setwarnings(False) 

red = 2
blue = 3
green = 4

GPIO.setmode(GPIO.BCM) 
GPIO.setup(red, GPIO.OUT)
GPIO.setup(blue, GPIO.OUT)
GPIO.setup(green, GPIO.OUT)
#For some reason true = false idk why
#Turn off LEDs
GPIO.output(red, True)
GPIO.output(blue, True)
GPIO.output(green, True)


#-------------------Create needed functions----------------------
#def byte_array_to_string(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232
 #   value = bytearray(value)
  #  value = value.decode('utf-8')
   # return value

def WriteAudioFile():
    # Set up WAV file parameters
    file_name = "received_audio.wav"
    sample_rate = 44000
    channels = 1
    sample_width = 1

    # Open a new WAV file
    with wave.open(file_name, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)

        print("Receiving audio data...")
        BlueCHAR = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]

        # Continuously read data until receiving the termination marker
        while True:
            BlueData = BlueCHAR.read()
            BlueString = byte_array_to_string(BlueData)
            if BlueString == "9999":  # Check for termination marker
                print("End of transmission received.")
                break
            
            # Write the raw audio data to the WAV file
            print(BlueString)
            wav_file.writeframes(BlueData)
        
        print(f"Audio data saved to {file_name}")

def SpeechToText():
    # Change the .wav file with whatever the file we write to is called
    GoogleSR = sr.AudioFile('received_audio.wav')
    with GoogleSR as source:
        audio = r.record(source)
    try:
        s = r.recognize_google(audio)
        print("Text: " + s)
        return s
    except Exception as e:
        print("Exception: " + str(e))
        return ""

def GenerateAI(user_input):
    # Prepare the input as a mapping
    formatted_input = {"user_input": user_input}

    # Generate a response from the model
    result = chain.invoke(formatted_input)

    # Print the result
    print(result.strip())
    return result.strip()
     
#---------------------Main---------------------------
def main():
    while True:
        BlueCHAR = bleService.getCharacteristics(CHARACTERISTIC_UUID)[0]
        print("Blue Char: ", BlueCHAR)  # Use a comma to print the object directly
        BlueData = BlueCHAR.read()
        print("Blue Data (raw bytes): ", BlueData)  # Use a comma for raw byte data
        BlueDataString = byte_array_to_string(BlueData)
        print("Blue Data (converted to string): " + BlueDataString)  # Proper string concatenation

        #GPIO.output(blue, False)
        WriteAudioFile()  # Write the audio data to a WAV file
        #GPIO.output(blue, True)
            
        #GPIO.output(green, False)
        #Text = SpeechToText()  # Convert the audio file to text
        #GPIO.output(green, True)
            
        #GPIO.output(red, False)
        #Response = GenerateAI(Text)  # Generate a response using AI
        #GPIO.output(red, True)
        
        # Use text-to-speech to respond
        #os.system(f'espeak "{Response}"')

if __name__ == "__main__":
    main()
