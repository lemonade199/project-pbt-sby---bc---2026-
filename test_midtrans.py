"""
test_midtrans.py - Script untuk menguji koneksi Midtrans Sandbox
Jalankan: python test_midtrans.py
"""
import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from midtrans_config import MIDTRANS_SERVER_KEY, MIDTRANS_CLIENT_KEY, MIDTRANS_IS_PRODUCTION

print("=" * 55)
print("  Test Koneksi Midtrans Sandbox")
print("=" * 55)
print(f"  Mode       : {'PRODUCTION' if MIDTRANS_IS_PRODUCTION else 'SANDBOX'}")
print(f"  Server Key : {MIDTRANS_SERVER_KEY[:20]}...")
print(f"  Client Key : {MIDTRANS_CLIENT_KEY[:20]}...")
print()

# Cek format
ok = True
if not MIDTRANS_SERVER_KEY.startswith("SB-Mid-server-"):
    print("[ERROR] Server Key harus dimulai 'SB-Mid-server-'"); ok = False
if not MIDTRANS_CLIENT_KEY.startswith("SB-Mid-client-"):
    print("[ERROR] Client Key harus dimulai 'SB-Mid-client-'"); ok = False
if "XXXX" in MIDTRANS_SERVER_KEY:
    print("[ERROR] Kunci masih placeholder!"); ok = False
if ok:
    print("[OK] Format kunci valid.")
else:
    sys.exit(1)

print("Mengecek midtransclient...", end=" ")
try:
    import midtransclient
    print("OK")
except ImportError:
    print("TIDAK ADA -> pip install midtransclient"); sys.exit(1)

print("Menghubungi Midtrans API...", end=" ", flush=True)
try:
    import time
    snap = midtransclient.Snap(
        is_production=MIDTRANS_IS_PRODUCTION,
        server_key=MIDTRANS_SERVER_KEY,
        client_key=MIDTRANS_CLIENT_KEY,
    )
    result = snap.create_transaction({
        "transaction_details": {
            "order_id": f"BC-TEST-{int(time.time())}",
            "gross_amount": 10000,
        },
        "customer_details": {"first_name": "Test"},
        "item_details": [{"id": "t1", "price": 10000, "quantity": 1, "name": "Test"}],
    })
    token = result.get("token", "")
    print("SUKSES!")
    print()
    print("=" * 55)
    print("  Midtrans TERHUBUNG! Kunci Anda VALID.")
    print(f"  Token : {token[:40]}...")
    print("  Silakan jalankan: python main.py")
    print("=" * 55)

except Exception as e:
    err = str(e)
    print("GAGAL!")
    print()
    print("=" * 55)
    if "401" in err or "Access denied" in err:
        print("  ERROR: Kunci API DITOLAK (HTTP 401)")
        print()
        print("  Kemungkinan penyebab:")
        print("  1. Kunci salah copy (terpotong / ada spasi)")
        print("  2. Akun sandbox belum terverifikasi")
        print("  3. Login ke dashboard salah (production vs sandbox)")
        print()
        print("  SOLUSI:")
        print("  1. Buka: https://dashboard.sandbox.midtrans.com")
        print("     (pastikan URL ada kata 'sandbox')")
        print("  2. Settings -> Access Keys")
        print("  3. Klik tombol [Copy] di kanan kunci")
        print("     (JANGAN select manual - bisa terpotong)")
        print("  4. Paste ke midtrans_config.py")
        print("  5. Jalankan lagi: python test_midtrans.py")
    elif "timeout" in err.lower() or "connection" in err.lower():
        print("  ERROR: Tidak ada koneksi internet")
    else:
        print(f"  ERROR: {err[:300]}")
    print("=" * 55)
    sys.exit(1)
