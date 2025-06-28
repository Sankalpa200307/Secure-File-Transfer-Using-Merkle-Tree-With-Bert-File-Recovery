'''
22AIE203 - DSA2 
Merkle Tree Project
By Amritha and Saran
'''

import os
import csv
import socket
import datetime
import base64
from hashlib import sha256
from cryptography.fernet import Fernet

# Setting the IP address the server, needs to be set
IP = socket.gethostbyname(socket.gethostname())
# sets a fixed port number
PORT = 4455
# combines the IP address and port number 
ADDR = (IP,PORT)

# Buffer size for sending and receiving data
# over the network is 102400 bytes (100 KB)
SIZE = 102400 
KEY = 'epVKiOHn7J0sZcJ4-buWQ5ednv3csHdQHfvEKk0qVvk='

# Function to encrypt data using Fernet symmetric encryption
def encrypt_data(data):
    fernet = Fernet(KEY)
    if isinstance(data, str):
        data = data.encode('utf-8')
    encMessage = fernet.encrypt(data)
    return encMessage

# Function to decrypt data using Fernet symmetric encryption
def decrypt_data(data):
    fernet = Fernet(KEY)
    if isinstance(data, str):
        data = data.encode('utf-8')
    decMessage = fernet.decrypt(data)
    return decMessage

# Function to break a file into chunks for building the merkle tree
def chunk_file(file_path, chunk_size):
    chunks = []
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if chunk:
                    chunks.append(chunk)
                else:
                    break
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding='latin-1') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if chunk:
                        chunks.append(chunk)
                    else:
                        break
        except:
            with open(file_path, "r", encoding='cp1252', errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if chunk:
                        chunks.append(chunk)
                    else:
                        break
    return chunks

# Function to create a Merkle tree from file chunks and 
# returns the root hash value of the tree
def merkle_tree(chunks):
    if len(chunks) == 1:
        return sha256(chunks[0].encode()).hexdigest()

    mid = len(chunks) // 2
    left_hash = merkle_tree(chunks[:mid])
    right_hash = merkle_tree(chunks[mid:])
    print(f"Left Chunk:{chunks[:mid]}, Left Hash: {left_hash}\nRight Chunk:{chunks[mid:]}, Right Hash: {right_hash}\n")

    return sha256(left_hash.encode() + right_hash.encode()).hexdigest()

def log_to_csv(log_data):
    with open("logs.csv", mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(log_data)

# Function to send large data in chunks
def send_large_data(conn, data):
    # Send the length of data first
    data_length = len(data)
    conn.send(str(data_length).encode())
    
    # Wait for acknowledgment
    conn.recv(1024)
    
    # Send data in chunks
    chunk_size = 8192  # 8KB chunks
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        conn.send(chunk)
        # Wait for acknowledgment
        conn.recv(1024)

# Function to receive large data in chunks
def receive_large_data(conn):
    # Receive the length of data first
    data_length = int(conn.recv(1024).decode())
    conn.send(b"OK")  # Send acknowledgment
    
    # Receive data in chunks
    received_data = b""
    chunk_size = 8192  # 8KB chunks
    
    while len(received_data) < data_length:
        chunk = conn.recv(min(chunk_size, data_length - len(received_data)))
        if not chunk:
            break
        received_data += chunk
        conn.send(b"OK")  # Send acknowledgment
    
    return received_data

def upload_file(conn, addr):
    try:
        # Create the received data directory if it doesn't exist
        os.makedirs("Recieved data", exist_ok=True)
        
        # Receive the filename
        filename = conn.recv(SIZE).decode()
        print(f"Filename: {filename} received")
        conn.send("filename recieved".encode()) # Acknowledgemt 

        # Receive, decrypt the file data and store it in a file in the "Recieved data" 
        # folder of the server with the filename
        encrypted_data_base64 = receive_large_data(conn).decode()
        encrypted_data = base64.b64decode(encrypted_data_base64)
        decrypted_data = decrypt_data(encrypted_data)
        if isinstance(decrypted_data, bytes):
            try:
                decrypted_data = decrypted_data.decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try other common encodings
                try:
                    decrypted_data = decrypted_data.decode('latin-1')
                except:
                    decrypted_data = decrypted_data.decode('cp1252', errors='ignore')
        
        with open("Recieved data/"+ filename, 'w', encoding='utf-8') as f:
            f.write(decrypted_data)

        # Receive the root hash value of the merkle tree created in the client
        hash_val = conn.recv(SIZE).decode()
        print(f"Hash value {hash_val}")

        # Create chunks from the received file and calculate the Merkle tree root hash
        ch = chunk_file("Recieved data/"+ filename, 1024)
        hash2 = merkle_tree(ch)
        print(f"Hash value: {hash2}")

        # Compare the calculated hash with the received hash value
        if hash2 == hash_val:
            conn.send("True".encode())
            log_data = [str(datetime.datetime.now().date()),str(datetime.datetime.now().time()), str(addr), "Upload", filename, "Successful", ]
            log_to_csv(log_data)
            print('Your data is in good hands')

        else:
            conn.send("False".encode())
            log_data = [str(datetime.datetime.now().date()),str(datetime.datetime.now().time()), str(addr), "Upload", filename, "Unsuccessful" ]
            log_to_csv(log_data)
            print('Your data is not in good hands')

        # Once file transfer is done, a message to the client is sent regarding it
        print(f"File Data Recieved")
        conn.send("File data recieved".encode())
    except Exception as e:
        print(f"Error in upload_file: {e}")
        try:
            conn.send("False".encode())
            conn.send("Upload failed".encode())
        except:
            pass

def download_file(conn, addr):
    # Create the received data directory if it doesn't exist
    os.makedirs("Recieved data", exist_ok=True)
    
    # Receive the filename
    filename = conn.recv(SIZE).decode()
    print(f"Filename: {filename} received")
    conn.send("filename recieved".encode()) # Acknowledgemt 

    # Checks if the file the client needs exists in the server
    if os.path.exists("Recieved data/" + filename):
        # A message is sent to the client saying the file exists
        conn.send("Exist".encode())
        print("File exists")

        msg =  conn.recv(SIZE).decode()
        print(msg)

        # Read, Encrypt and send the file data to the client
        try:
            with open("Recieved data/"+ filename, 'r', encoding='utf-8') as f:
                data = f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try other encodings
            try:
                with open("Recieved data/"+ filename, 'r', encoding='latin-1') as f:
                    data = f.read()
            except:
                with open("Recieved data/"+ filename, 'r', encoding='cp1252', errors='ignore') as f:
                    data = f.read()
        
        encrypted_data = encrypt_data(data)
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        send_large_data(conn, encrypted_data_base64.encode())

        # Create chunks from the file and calculate the Merkle tree root hash
        ch = chunk_file("Recieved data/"+filename, 1024)
        hash1 = merkle_tree(ch)
        print(f"Hash value: {hash1}")
        conn.send(hash1.encode())
        log_data = [str(datetime.datetime.now().date()),str(datetime.datetime.now().time()), str(addr), "Download", filename, "Successful" ]
        log_to_csv(log_data)

    else:
        # A message is sent to the client if the file does not exist
        conn.send("NotExist".encode())
        log_data = [str(datetime.datetime.now().date()),str(datetime.datetime.now().time()), str(addr), "Download", filename, "File not found" ]
        log_to_csv(log_data)
        print("File does not exists")

def show_files(conn, addr):
    # Create the received data directory if it doesn't exist
    os.makedirs("Recieved data", exist_ok=True)
    
    files = []
    for f in os.listdir('./Recieved data'):
        if f.endswith(".txt"):
            files.append(f)
    
    if files:
        files = '\n'.join(files)
        print("Files: \n", files)
    else:
        files="None"
    msg = conn.recv(SIZE).decode()

    conn.send(files.encode())
    log_data = [str(datetime.datetime.now().date()),str(datetime.datetime.now().time()), str(addr), "Get File Names" ]
    log_to_csv(log_data)
    print("File names sent!")

def main():
    print("Server is starting...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print("Server is listening")
    
    while True:
        conn,  addr = server.accept()
        print(F"New connection {addr} connected.")
        log_data = [str(datetime.datetime.now().date()), str(datetime.datetime.now().time()), str(addr), "New connection"]
        log_to_csv(log_data)

        # Receive the type of transfer (Upload or Download) from the client
        transfertype = conn.recv(SIZE).decode()
        print(f"Received transfertype: {transfertype}")
        conn.send("Recieved Transfer type".encode()) # Acknowledgemt 

        # If the client wants to upload files to the server:
        if transfertype=="Upload":
            upload_file(conn, addr)

        # If the client wants to download files from the client:
        elif transfertype=="Download":
            download_file(conn, addr)

        elif transfertype=="Show":
            show_files(conn, addr)

        else:
            # Error in the revieved transfer type info
            print("Invalid Transfer Type Recieved")
            break

    conn.close()
    print(f"Disconnected {addr} ")
    return

if __name__ == '__main__':
    if not os.path.exists("logs.csv"):
        with open("logs.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date","Timestamp", "Client Address", "Event", "Filename", "Status" ])
    main()