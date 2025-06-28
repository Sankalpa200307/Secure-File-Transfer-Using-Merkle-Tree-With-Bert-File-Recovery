'''
22AIE203 - DSA2 
Merkle Tree Project
By Amritha and Saran
'''
import os
from hashlib import sha256
import socket
import pandas as pd
import streamlit as st
from cryptography.fernet import Fernet
import base64

# the buffer size for sending and receiving data 
# over the network is 102400 bytes (100 KB)
SIZE = 102400 
PORT = 4455
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

    return sha256(left_hash.encode() + right_hash.encode()).hexdigest()

def show_files(ip):
    IP = socket.gethostbyname(socket.gethostname()) 
    # change the value to input ip while connecting to server on another system
    # IP = ip
    ADDR = (IP, PORT)

    try:
        # Establish a connection to the server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        # Send the "Upload" message to the server
        client.send("Show".encode())

        msg = client.recv(SIZE).decode() # Recieves acknowledgment
        print(msg)
        
    except:
        # Handles connection failure
        st.error("Connection Failure! Check if the server is active.")
        return
    
    client.send("Sending Filenames".encode())
    file_names = client.recv(SIZE).decode()
    client.close()
    print("File names Recieved")
    return file_names


# Function to upload a file to the server
def upload_file(uploaded_file, ip):
    IP = socket.gethostbyname(socket.gethostname()) 
    # change the value to input ip while connecting to server on another system
    # IP = ip
    ADDR = (IP, PORT)

    try:
        # Establish a connection to the server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        # Send the "Upload" message to the server
        client.send("Upload".encode())

        msg = client.recv(SIZE).decode() # Recieves acknowledgment
        print(msg)
        
    except:
        # Handles connection failure
        st.error("Connection Failure! Check if the server is active.")
        return

    # Send the filename to the server
    client.send(uploaded_file.name.encode())

    # Receive acknowledgment from the server
    msg = client.recv(SIZE).decode()
    print(f"Server: {msg}")

    # Read the contents of the uploaded file
    data = uploaded_file.read()
    if isinstance(data, bytes):
        try:
            data = data.decode('utf-8')
        except UnicodeDecodeError:
            # If UTF-8 fails, try other common encodings
            try:
                data = data.decode('latin-1')
            except:
                data = data.decode('cp1252', errors='ignore')
    
    # Send encrypted file data to the server
    encrypted_data = encrypt_data(data)
    encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
    send_large_data(client, encrypted_data_base64.encode())

    # Create file chunks and calculate Merkle tree root hash
    # We need to create a temporary file or work with the data directly
    chunks = [data[i:i+1024] for i in range(0, len(data), 1024)]
    hash1 = merkle_tree(chunks)
    print(f"Hash value: {hash1}")

    # Send calculated hash to the server
    client.send(hash1.encode())

    # Receive verification of data integrity from the server
    try:
        secure = client.recv(SIZE).decode()
        if secure == "True":
            st.success("Data Integrity assured!", icon="✅")
        else:
            st.error("Data might be lost.")
        
        # Receive acknowledgment of file data receipt from the server
        msg = client.recv(SIZE).decode()
        print(f"Server: {msg}")
        
        client.close()
        if msg == "File data recieved":
            return True
        return False
    except Exception as e:
        print(f"Error during upload: {e}")
        client.close()
        st.error("Upload failed due to connection issues.")
        return False

# Function to download a file from the server
def download_file(filename, ip):
    try:
        IP = socket.gethostbyname(socket.gethostname()) 
        # change the value to input ip while connecting to server on another system
        # IP = ip
        ADDR = (IP, PORT)

        try:
            # Establish a connection to the server
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)

            # Send the "Download" message to the server
            client.send("Download".encode())

            # Receive acknowledgment from the server
            msg = client.recv(SIZE).decode()
            print(msg)
        except:
            # Handle connection failure
            st.error("Connection Failure! Check if the server is active.")
            return
        
        # Send the filename to the server
        client.send(filename.encode())
        msg = client.recv(SIZE).decode() # Receive acknowledgment from the server
        
        # Check if the file exists on the server
        exist = client.recv(SIZE).decode()
        print(f"Exists? {exist}")
        client.send("Downloading".encode()) # Send acknowledgment to start downloading
        
        if exist == "Exist":
            # Receive encrypted file data from the server
            encrypted_data_base64 = receive_large_data(client).decode()
            encrypted_data = base64.b64decode(encrypted_data_base64)

            os.makedirs("Downloaded", exist_ok=True)
            # Decrypt and write the data to a file in the "Downloaded" folder
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
            
            with open("Downloaded/"+ filename, 'w', encoding='utf-8') as f:
                f.write(decrypted_data)

            # Receive the hash value of the downloaded file from the server
            hash_val = client.recv(SIZE).decode()
            print(f"Hash value {hash_val}")
            client.close()

            # Create file chunks and calculate Merkle tree root hash
            ch = chunk_file("Downloaded/"+ filename, 1024)
            hash2 = merkle_tree(ch)
            print(f"Hash value: {hash2}")

            # Verify data integrity
            if hash2 == hash_val:
                print("Downloaded data has the same hash values")
                st.success("Data Integrity assured!", icon="✅")
                return True
            else:
                st.error("Data might be lost", icon="🚨")
                return False
            
        elif exist=="NotExist":
            # Handle case where the file does not exist on the server
            st.error("No such file exists in the server", icon="🚨")
            return False
        else:
            print("Some other error")
            return False
    except Exception as e:
        print(f"Error during download: {e}")
        try:
            client.close()
        except:
            pass
        st.error("Download failed due to connection issues.")
        return False

# Function to send large data in chunks
def send_large_data(client, data):
    # Send the length of data first
    data_length = len(data)
    client.send(str(data_length).encode())
    
    # Wait for acknowledgment
    client.recv(1024)
    
    # Send data in chunks
    chunk_size = 8192  # 8KB chunks
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        client.send(chunk)
        # Wait for acknowledgment
        client.recv(1024)

# Function to receive large data in chunks
def receive_large_data(client):
    # Receive the length of data first
    data_length = int(client.recv(1024).decode())
    client.send(b"OK")  # Send acknowledgment
    
    # Receive data in chunks
    received_data = b""
    chunk_size = 8192  # 8KB chunks
    
    while len(received_data) < data_length:
        chunk = client.recv(min(chunk_size, data_length - len(received_data)))
        if not chunk:
            break
        received_data += chunk
        client.send(b"OK")  # Send acknowledgment
    
    return received_data

# Streamlit web application entry point
if __name__ == "__main__":
    st.title("Secure File Transfer System")
    st.subheader("Encrypt and Verify in a Flash ⚡")
    
    # text input for IP address of the server
    ip = st.text_input("Enter IP address of the server: ")
    showfiles = st.button("Show Files")

    if showfiles:
        try:
            files = show_files(ip)
            print(files)
            if files !="None":
                files = files.split("\n")
                df = pd.DataFrame({"Files in the server: ":files})
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No Files in the server.")
        except:
            pass
    st.divider()

    # file uploader input for uploading files
    uploaded_file = st.file_uploader("Choose a text file!", accept_multiple_files=True)
    upload = st.button("Upload Files!")
    if upload:
        if uploaded_file:
            filenames = []
            for x in uploaded_file:
                if upload_file(x, ip):
                    st.success(f'File {x.name} was transferred successfully!', icon="✅")
                    filenames.append(x.name)
                else:
                    st.error(f'There is some problem with transferring {x.name}! Try again', icon="🚨")
            print(filenames)
        else:
            st.error(f'Browse files to upload first!', icon="🚨")
    st.divider()

    # text input for downloading a certain file from the server
    filename = st.text_input("Enter file you want to download from the server: ")
    download = st.button("Download File")
    if download:
        if filename:
            if download_file(filename, ip):
                st.success(f'File {filename} was downloaded successfully! Check your "Downloaded" folder.', icon="✅")
            else:
                st.error(f'Downloading of {filename} failed! Try again', icon="🚨")
        else:
            st.error(f'Enter a filename to be downloaded first!', icon="🚨")
