import socket
import os

os.system('cls')

dns = {
    "172.17.4.135": 'sathwik',
    "172.17.8.231": 'nagavendra',
    "": 'renanjit',
    "": 'sweekruth',
    "": 'afnan',
    "": 'ruthuraj',
    "": 'mayank',
    "": 'sahil',
    "": 'sankalpa',
    "172.17.11.102": 'karthik'
}

IP = '172.17.4.135'
PORT = 5050
ADDR = IP, PORT
H_SIZE = 10

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
print(f"Connected to\t{ADDR}")

connected = True
while connected:
    message = input("you: ")
    if message == 'quit':
        client.close()
        connected = False
    else:
        msg_size = len(message)
        client.send(str(msg_size).encode())
        client.send(message.encode())
        size = client.recv(H_SIZE).decode()
        reply = client.recv(int(size)).decode()
        reply = reply.split(';')
        for text in reply:
            if len(text.split(':')) > 1 and text.split(':')[1] != ' ':
                print("\t\t\t", text)
            