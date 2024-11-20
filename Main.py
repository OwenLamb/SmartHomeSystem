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

#-------------------SETUP Bluetooth-------------
from bluepy import btle  
import time
#Use terminal command "sudo hcitool lescan" to find MAC
mac_address = "92:32:7E:F5:B4:3F"
SERVICE_UUID = "180F" # These two need configured the same as Arduino
CHARACTERISTIC_UUID = "2A19"

#Sometimes need to turn bluetooth off then on if it crashes here
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
def byte_array_to_int(value):
    # Raw data is hexstring of int values, as a series of bytes, in little endian byte order
    # values are converted from bytes -> bytearray -> int
    # e.g., b'\xb8\x08\x00\x00' -> bytearray(b'\xb8\x08\x00\x00') -> 2232
    value = bytearray(value)
    value = int.from_bytes(value, byteorder="little", signed=True)
    return value

def WriteAudioFile():
	#Placeholder, this just reads the data from bluetooth once.
	BlueData = 0
	while(BlueData != '9999'):
	    BlueCHAR = service.getCharacteristics(CHARACTERISTIC_UUID)[0]
	    BlueData = BlueCHAR.read()
	    BlueData = byte_array_to_int(BlueData)
	    print(f"Data: {BlueData}")

def SpeechToText():
	#change the .wav file with whatever the file we write to is called
	GoogleSR=sr.AudioFile('HelloWorld.wav')
	with GoogleSR as source:
		audio = r.record(source)
	try:
		s = r.recognize_google(audio)
		print("Text: "+s)
		return s
	except Exception as e:
		print("Exception: "+str(e))


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
    while(1):
	BlueCHAR = service.getCharacteristics(CHARACTERISTIC_UUID)[0]
	BlueData = BlueCHAR.read()
	BlueData = byte_array_to_int(BlueData)
    
	if(BlueData == '9999'):
	    GPIO.output(blue, False)
	    WriteAudioFile()
	    GPIO.output(blue, True)
    
	    GPIO.output(green, False)
	    Text = SpeechToText()
	    GPIO.output(green, True)
    
	    GPIO.output(red, False)
	    Response = GenerateAI(Text)
	    GPIO.output(red, True)
	
	    #Response = "Hello World"
	    os.system(f'espeak "{Response}"')
	
if __name__ == "__main__":
    main()
