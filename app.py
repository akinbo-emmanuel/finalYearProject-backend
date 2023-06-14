import os
import random
import string
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from google.cloud import storage

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SECRET_KEY'] = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

# Firebase Storage Credentials
firebase_credentials = {
    "apiKey": "AIzaSyB_fgH-gqRagjhIRoY6SUaKoxlgyzjPrIk",
    "authDomain": "file-manager-1169c.firebaseapp.com",
    "projectId": "file-manager-1169c",
    "storageBucket": "file-manager-1169c.appspot.com",
    "messagingSenderId": "627965509307",
    "appId": "1:627965509307:web:0e4d1eee0cdb5fce1cf39e",
    "measurementId": "G-50PEMH6L40"
}

# Initialize Firebase Storage Client
storage_client = storage.Client.from_service_account_json(firebase_credentials)

@app.route('/upload', methods=['POST'])
def handle_file_upload():
    file = request.files['file']

    # Perform file size and type validation here

    # Save the file to the server
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Encrypt the file
    encrypted_file_path = encrypt_file(file_path)

    # Upload the encrypted file to Firebase Storage
    remote_path = os.path.basename(encrypted_file_path)
    upload_file_to_storage(encrypted_file_path, remote_path)

    # Return the download URL to the client
    download_url = get_download_url(remote_path)
    return jsonify({'download_url': download_url})

def encrypt_file(file_path):
    encryption_key = get_random_bytes(32)
    cipher = AES.new(encryption_key, AES.MODE_EAX)

    with open(file_path, 'rb') as file:
        data = file.read()

    ciphertext, tag = cipher.encrypt_and_digest(data)

    encrypted_file_path = file_path + '.enc'
    with open(encrypted_file_path, 'wb') as file:
        [file.write(x) for x in (cipher.nonce, tag, ciphertext)]

    return encrypted_file_path

def upload_file_to_storage(file_path, remote_path):
    bucket_name = firebase_credentials['storageBucket']
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(remote_path)

    blob.upload_from_filename(file_path)

def get_download_url(remote_path):
    bucket_name = firebase_credentials['storageBucket']
    return f"https://storage.googleapis.com/{bucket_name}/{remote_path}"

if __name__ == '__main__':
    app.run()
