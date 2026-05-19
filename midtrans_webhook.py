"""
midtrans_webhook.py - Flask webhook server untuk Midtrans callback
Aplikasi Business Center SMKN 13 Bandung

Fitur:
  - GET  /pay/<snap_token>        → Halaman HTML pembayaran Snap
  - GET  /pay/finish              → Redirect setelah Snap selesai
  - POST /midtrans/callback       → Webhook notifikasi dari Midtrans
  - Verifikasi signature SHA-512
  - Update payment_status di database
  - Jalan otomatis di background thread saat main.py dijalankan
"""

import hashlib
import json
import logging
import threading

from flask import Flask, request, jsonify
from midtrans_config import (
    MIDTRANS_SERVER_KEY,
    MIDTRANS_CLIENT_KEY,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    SNAP_JS_URL,
)
from db import get_db

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("MidtransWebhook")

def reduce_stock(id_pesanan: str):
    """Mengurangi stok barang berdasarkan detail pesanan di Firestore."""
    try:
        from firebase_admin import firestore
        db = get_db()
        doc_ref = db.collection('pesanan').document(id_pesanan)
        doc = doc_ref.get()
        if not doc.exists:
            log.warning(f"Pesanan #{id_pesanan} tidak ditemukan untuk pengurangan stok.")
            return
            
        p = doc.to_dict()
        details = p.get('detail_pesanan', [])
        
        batch = db.batch()
        for d in details:
            b_ref = db.collection('barang').document(d["id_barang"])
            batch.update(b_ref, {'stok': firestore.Increment(-d["jumlah"])})
        batch.commit()
        
        log.info(f"Stok untuk Pesanan #{id_pesanan[:8]} berhasil dikurangi.")
    except Exception as e:
        log.error(f"Gagal kurangi stok: {e}")

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ── HTML template halaman pembayaran ─────────────────────────────────────────
_PAYMENT_HTML = """\
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pembayaran – Business Center SMKN 13</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Segoe UI',sans-serif;
        background:linear-gradient(135deg,#CC0000 0%,#7B0000 100%);
        min-height:100vh;display:flex;align-items:center;justify-content:center}}
  .card{{background:#fff;border-radius:18px;padding:36px 32px;
          max-width:440px;width:92%;box-shadow:0 24px 64px rgba(0,0,0,.35);text-align:center}}
  .logo{{font-size:46px;margin-bottom:8px}}
  h1{{color:#CC0000;font-size:19px;font-weight:700;margin-bottom:4px}}
  .sub{{color:#888;font-size:12px;margin-bottom:22px}}
  .info-box{{background:#FFF5F5;border:1px solid #FFCDD2;border-radius:10px;
              padding:14px 16px;margin-bottom:18px;text-align:left}}
  .info-box p{{margin:3px 0;font-size:13px;color:#333}}
  .info-box .total{{font-size:22px;font-weight:700;color:#CC0000;margin-top:6px;text-align:center}}
  .methods{{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:20px}}
  .chip{{background:#f0f0f0;border-radius:20px;padding:4px 12px;font-size:11px;color:#555}}
  .btn{{background:linear-gradient(135deg,#CC0000,#900);color:#fff;border:none;
         padding:14px;font-size:15px;font-weight:700;border-radius:10px;
         cursor:pointer;width:100%;transition:opacity .2s;margin-bottom:8px}}
  .btn:hover{{opacity:.88}} .btn:disabled{{opacity:.45;cursor:not-allowed}}
  .spinner{{display:none;margin:14px auto;width:34px;height:34px;
             border:4px solid #FFCDD2;border-top:4px solid #CC0000;
             border-radius:50%;animation:spin .8s linear infinite}}
  @keyframes spin{{to{{transform:rotate(360deg)}}}}
  .msg{{font-size:12px;color:#888;margin-top:8px}}
  .ok-box{{display:none;background:#E8F5E9;border:1px solid #A5D6A7;
            border-radius:10px;padding:18px;margin-top:14px}}
  .ok-box h2{{color:#2E7D32;margin-bottom:4px}}
  .fail-box{{display:none;background:#FFEBEE;border:1px solid #FFCDD2;
              border-radius:10px;padding:18px;margin-top:14px}}
  .fail-box h2{{color:#CC0000;margin-bottom:4px}}
  small{{color:#aaa;font-size:10px;display:block;margin-top:18px}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">🏫</div>
  <h1>Business Center SMKN 13</h1>
  <p class="sub">Pembayaran Pesanan Online – Mode Sandbox</p>

  <div class="info-box">
    <p>🧾 ID Pesanan: <strong>#{order_id_short}</strong></p>
    <p>👤 Nama: <strong>{customer_name}</strong></p>
    <p class="total">Rp {total_fmt}</p>
  </div>

  <div class="methods">
    <span class="chip">QRIS</span>
    <span class="chip">GoPay</span>
    <span class="chip">DANA</span>
    <span class="chip">ShopeePay</span>
    <span class="chip">Virtual Account</span>
    <span class="chip">Indomaret</span>
  </div>

  <button class="btn" id="btnPay" onclick="startPay()">💳 Bayar Sekarang</button>
  <div class="spinner" id="spinner"></div>
  <p class="msg" id="msgTxt">Pilih metode pembayaran dengan klik tombol di atas.</p>

  <div class="ok-box" id="okBox">
    <h2>✅ Pembayaran Berhasil!</h2>
    <p>Pesanan Anda sedang diproses oleh admin.</p>
    <p style="font-size:12px;color:#666;margin-top:6px">Halaman ini bisa ditutup.</p>
  </div>
  <div class="fail-box" id="failBox">
    <h2>❌ Pembayaran Gagal / Dibatalkan</h2>
    <p id="failMsg">Silakan coba lagi atau hubungi kasir.</p>
  </div>

  <small>Powered by Midtrans Sandbox · BC SMKN 13 Bandung</small>
</div>

<script src="{snap_js}" data-client-key="{client_key}"></script>
<script>
const TOKEN = "{snap_token}";
function startPay() {{
  var btn = document.getElementById('btnPay');
  btn.disabled = true;
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('msgTxt').textContent = 'Membuka jendela pembayaran…';
  snap.pay(TOKEN, {{
    onSuccess: function(r) {{
      document.getElementById('spinner').style.display='none';
      btn.style.display='none';
      document.getElementById('msgTxt').textContent='';
      document.getElementById('okBox').style.display='block';
    }},
    onPending: function(r) {{
      document.getElementById('spinner').style.display='none';
      btn.disabled = false;
      document.getElementById('msgTxt').textContent =
        '⏳ Pembayaran pending — selesaikan pembayaran Anda.';
    }},
    onError: function(r) {{
      document.getElementById('spinner').style.display='none';
      btn.disabled = false;
      document.getElementById('failBox').style.display='block';
      document.getElementById('failMsg').textContent =
        r.status_message || 'Terjadi kesalahan.';
    }},
    onClose: function() {{
      document.getElementById('spinner').style.display='none';
      btn.disabled = false;
      document.getElementById('msgTxt').textContent =
        'Popup ditutup. Klik tombol untuk mencoba kembali.';
    }}
  }});
}}
</script>
</body>
</html>
"""

_FINISH_HTML = """\
<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><title>Selesai</title>
<style>body{{font-family:'Segoe UI',sans-serif;display:flex;align-items:center;
       justify-content:center;min-height:100vh;background:#f5f5f5}}
.box{{background:#fff;padding:40px;border-radius:16px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.1)}}
h1{{color:#2E7D32;font-size:22px}} p{{color:#666;margin-top:10px}}</style></head>
<body><div class="box">
  <h1>✅ Proses Pembayaran Selesai</h1>
  <p>Terima kasih! Status pesanan akan diperbarui otomatis.</p>
  <p style="margin-top:16px;font-size:12px;color:#aaa">Halaman ini bisa ditutup.</p>
</div></body></html>
"""


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/pay/finish")
def pay_finish():
    return _FINISH_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/pay/<snap_token>")
def payment_page(snap_token: str):
    """Halaman HTML pembayaran Snap — dibuka di browser pengguna."""
    try:
        db = get_db()
        docs = db.collection('pesanan').where('snap_token', '==', snap_token).limit(1).get()
        if not docs:
            return "<h3>Pesanan tidak ditemukan.</h3>", 404
        doc = docs[0]
        p = doc.to_dict()
        html = _PAYMENT_HTML.format(
            order_id_short=doc.id[:8],
            customer_name=p.get("nama_pembeli") or "Pembeli",
            total_fmt=f"{p.get('total_harga', 0):,.0f}",
            snap_token=snap_token,
            client_key=MIDTRANS_CLIENT_KEY,
            snap_js=SNAP_JS_URL,
        )
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return f"<h3>Error: {e}</h3>", 500


@app.route("/midtrans/callback", methods=["POST"])
def midtrans_callback():
    """Webhook endpoint — Midtrans mengirim notifikasi ke sini."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No payload"}), 400

        log.info("Callback Midtrans: %s", json.dumps(data, ensure_ascii=False))

        # ── Verifikasi Signature Key ──────────────────────────────────────
        order_id     = data.get("order_id", "")
        status_code  = data.get("status_code", "")
        gross_amount = data.get("gross_amount", "")
        sig_received = data.get("signature_key", "")
        raw          = order_id + status_code + gross_amount + MIDTRANS_SERVER_KEY
        sig_expected = hashlib.sha512(raw.encode()).hexdigest()

        if sig_received != sig_expected:
            log.warning("Signature tidak valid untuk order %s", order_id)
            return jsonify({"status": "error", "message": "Invalid signature"}), 403

        # ── Parse id_pesanan dari order_id (format: BC-{id}) ─────────────
        try:
            id_pesanan = order_id.split("-")[1]
        except IndexError:
            log.warning("Format order_id tidak dikenali: %s", order_id)
            return jsonify({"status": "error", "message": "Bad order_id"}), 400

        # ── Map status Midtrans → payment_status lokal ────────────────────
        tx_status    = data.get("transaction_status", "")
        fraud_status = data.get("fraud_status", "")
        payment_type = data.get("payment_type", "")
        tx_id        = data.get("transaction_id", "")

        if tx_status == "capture":
            pay_status = "paid" if fraud_status == "accept" else "failed"
        elif tx_status == "settlement":
            pay_status = "paid"
        elif tx_status in ("cancel", "deny", "failure"):
            pay_status = "failed"
        elif tx_status == "expire":
            pay_status = "expired"
        elif tx_status == "pending":
            pay_status = "pending"
        else:
            pay_status = tx_status

        _update_payment(id_pesanan, pay_status, payment_type, tx_id)
        log.info("Pesanan #%s → payment_status=%s", id_pesanan, pay_status)
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        log.error("Callback error: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Helper update DB ──────────────────────────────────────────────────────────
def _update_payment(id_pesanan: str, pay_status: str,
                    payment_method: str = "", transaction_id: str = ""):
    """Update kolom payment di tabel pesanan. Jika paid → status = diterima."""
    try:
        db = get_db()
        doc_ref = db.collection('pesanan').document(id_pesanan)
        
        updates = {
            'payment_status': pay_status,
            'payment_method': payment_method,
            'transaction_id': transaction_id
        }
        
        if pay_status == "paid":
            updates['status'] = 'diterima'
            doc_ref.update(updates)
            # KURANGI STOK DISINI
            reduce_stock(id_pesanan)
        else:
            doc_ref.update(updates)
            
        log.info("Pesanan #%s → payment_status=%s", id_pesanan, pay_status)
    except Exception as e:
        log.error("DB update payment error: %s", e)


# ── Background thread ─────────────────────────────────────────────────────────
_thread: threading.Thread = None


def ensure_webhook_running():
    """Jalankan Flask server di daemon thread (dipanggil dari main.py)."""
    global _thread
    if _thread and _thread.is_alive():
        return
    # Matikan log verbose Werkzeug
    import logging as _lg
    _lg.getLogger("werkzeug").setLevel(_lg.ERROR)

    def _run():
        app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT,
                debug=False, use_reloader=False)

    _thread = threading.Thread(target=_run, daemon=True, name="MidtransWebhook")
    _thread.start()
    log.info("Webhook server berjalan di http://%s:%s", WEBHOOK_HOST, WEBHOOK_PORT)
