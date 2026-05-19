
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, storage
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_CONFIG = {
    "db_host": "localhost",
    "db_user": "root",
    "db_password": "",
    "db_name": "bc_smkn13",
    "images_folder": "images",
    "api_url": "http://127.0.0.1:8000"
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)

with open(CONFIG_FILE, "r") as f:
    config_data = json.load(f)

# Direktori Gambar (Bisa Absolut atau Network LAN)
img_val = config_data.get("images_folder", "images")
if os.path.isabs(img_val) or img_val.startswith(r"\\"):
    IMAGES_DIR = img_val
else:
    IMAGES_DIR = os.path.join(BASE_DIR, img_val)

os.makedirs(IMAGES_DIR, exist_ok=True)

# URL API
API_URL = config_data.get("api_url", "http://127.0.0.1:8000")

# Setup Resource Directory untuk Pyinstaller
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = sys._MEIPASS
else:
    RESOURCE_DIR = BASE_DIR

# Inisialisasi Firebase
# Mencari file JSON di RESOURCE_DIR atau BASE_DIR yang merupakan file kredensial (biasanya nama file mengandung 'firebase-adminsdk')
json_files = [f for f in os.listdir(RESOURCE_DIR) if f.endswith('.json') and 'firebase-adminsdk' in f]
if not json_files and RESOURCE_DIR != BASE_DIR:
    json_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.json') and 'firebase-adminsdk' in f]

if json_files:
    # Mengambil file JSON pertama yang ditemukan
    search_dir = RESOURCE_DIR if os.path.exists(os.path.join(RESOURCE_DIR, json_files[0])) else BASE_DIR
    CRED_FILE = os.path.join(search_dir, json_files[0])
else:
    # Fallback
    CRED_FILE = os.path.join(BASE_DIR, "kredensial_firebase.json")

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(CRED_FILE)
        firebase_admin.initialize_app(cred)
        print(f"Firebase berhasil diinisialisasi menggunakan: {os.path.basename(CRED_FILE)}")
    except Exception as e:
        print(f"Gagal inisialisasi Firebase: {e}")

# Inisialisasi Google Drive
DRIVE_FOLDER_ID = "1sPuG3yZAI-8hlxUX1hKXX3JA4anAVGLo"
drive_service = None

# Path untuk file OAuth
client_secret_files = [f for f in os.listdir(RESOURCE_DIR) if f.startswith('client_secret') and f.endswith('.json')]
if not client_secret_files and RESOURCE_DIR != BASE_DIR:
    client_secret_files = [f for f in os.listdir(BASE_DIR) if f.startswith('client_secret') and f.endswith('.json')]

if client_secret_files:
    search_dir = RESOURCE_DIR if os.path.exists(os.path.join(RESOURCE_DIR, client_secret_files[0])) else BASE_DIR
    CLIENT_SECRET_FILE = os.path.join(search_dir, client_secret_files[0])
else:
    CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret.json")

# token.json selalu di BASE_DIR agar bisa dimodifikasi/disimpan
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SCOPES = ['https://www.googleapis.com/auth/drive']

try:
    creds = None
    # Cari token.json yang sudah tersimpan
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Jika tidak ada token valid, minta user login (OAuth Flow)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(CLIENT_SECRET_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                # Simpan token untuk sesi berikutnya
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            else:
                print(f"File client_secret tidak ditemukan: {CLIENT_SECRET_FILE}")

    if creds:
        drive_service = build('drive', 'v3', credentials=creds)
        print("Google Drive API (OAuth2) berhasil diinisialisasi")
except Exception as e:
    print(f"Gagal inisialisasi Google Drive (OAuth2): {e}")

try:
    db_firestore = firestore.client()
except Exception:
    db_firestore = None

def get_db():
    return db_firestore

def get_drive_service():
    return drive_service

def get_connection():
    """Stub for backward compatibility"""
    return db_firestore

def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """Stub to raise error since we use Firebase now"""
    raise NotImplementedError("Gunakan get_db() untuk Firestore")

def run_migrations():
    pass
