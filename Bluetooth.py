import bluetooth

# Bluetooth UUID and address setup
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)

print("Waiting for connection...")
client_socket, address = server_socket.accept()
print(f"Connected to {address}")

try:
    while True:
        data = client_socket.recv(1024)  # Receive up to 1024 bytes
        if not data:
            break
        print(f"Received: {data.decode('utf-8')}")
except KeyboardInterrupt:
    print("Stopping server...")
finally:
    client_socket.close()
    server_socket.close()
