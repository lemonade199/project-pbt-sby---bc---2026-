"""
midtrans_config.py - Konfigurasi Midtrans Sandbox
Aplikasi Business Center SMKN 13 Bandung

CARA PAKAI:
  1. Daftar / login ke https://dashboard.sandbox.midtrans.com
  2. Masuk Settings → Access Keys
  3. Ganti nilai MIDTRANS_SERVER_KEY dan MIDTRANS_CLIENT_KEY di bawah
  4. Jalankan python main.py
"""

# ── Kunci Midtrans Sandbox ────────────────────────────────────────────────────
# GANTI dengan kunci Anda dari https://dashboard.sandbox.midtrans.com
MIDTRANS_SERVER_KEY  = "Mid-server-gKuAsozpTw2LMGToRKCzXQ1i"
MIDTRANS_CLIENT_KEY  = "Mid-client-jtvmm79T8QDY0u_7"

# Ubah ke True hanya saat production
MIDTRANS_IS_PRODUCTION = False

# ── URL Snap.js ───────────────────────────────────────────────────────────────
SNAP_JS_URL = (
    "https://app.midtrans.com/snap/snap.js"
    if MIDTRANS_IS_PRODUCTION
    else "https://app.sandbox.midtrans.com/snap/snap.js"
)

# ── Webhook server lokal ──────────────────────────────────────────────────────
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 5055
WEBHOOK_BASE = f"http://{WEBHOOK_HOST}:{WEBHOOK_PORT}"

# ── Metode pembayaran yang diaktifkan ─────────────────────────────────────────
ENABLED_PAYMENTS = [
    "qris",          # QRIS (GoPay, DANA, ShopeePay, OVO, dll)
    "gopay",         # GoPay langsung
    "bca_va",        # Virtual Account BCA
    "bni_va",        # Virtual Account BNI
    "bri_va",        # Virtual Account BRI
    "permata_va",    # Virtual Account Permata
    "other_va",      # VA bank lain
    "indomaret",     # Indomaret
]
