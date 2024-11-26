import asyncio
from bleak import BleakClient
#d8:3a:dd:1a:a8:e4
# Replace with the Arduino's MAC address
ARDUINO_MAC_ADDRESS = "XX:XX:XX:XX:XX:XX"
CHARACTERISTIC_UUID = "2A57"  # Same as on Arduino

async def read_data():
    async with BleakClient(ARDUINO_MAC_ADDRESS) as client:
        print("Connected to Arduino!")
        
        def notification_handler(sender, data):
            print(f"Received: {data.decode('utf-8')}")

        # Start receiving notifications
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        await asyncio.sleep(30)  # Keep receiving for 30 seconds
        await client.stop_notify(CHARACTERISTIC_UUID)

asyncio.run(read_data())
