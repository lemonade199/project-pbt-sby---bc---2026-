import hashlib
from db import get_db

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def add_admin():
    db = get_db()
    if db is None:
        print("Gagal koneksi Firestore. Pastikan file JSON kredensial sudah benar di folder 'migrate'.")
        return
        
    username = "admin"
    password = "admin123"
    hashed_pw = hash_password(password)
    
    # Cek apakah user sudah ada
    try:
        docs = db.collection('users').where('username', '==', username).get()
        if docs:
            doc_ref = docs[0].reference
            doc_ref.set({
                "username": username,
                "password": hashed_pw,
                "role": "admin"
            })
            print(f"User '{username}' berhasil di-reset dengan password 'admin123'.")
            return

        # Tambahkan ke collection 'users'
        doc_ref = db.collection('users').document()
        doc_ref.set({
            "username": username,
            "password": hashed_pw,
            "role": "admin"
        })
        print(f"User '{username}' berhasil ditambahkan ke Firebase dengan ID: {doc_ref.id}")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengakses Firestore: {e}")

if __name__ == "__main__":
    add_admin()
