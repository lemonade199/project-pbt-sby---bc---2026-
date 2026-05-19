"""
admin/pembayaran.py - Panel Status Pembayaran Midtrans
Aplikasi Business Center SMKN 13 Bandung

Menampilkan:
  - order_id, nama pembeli, metode pembayaran, total, payment_status
  - Auto-refresh setiap 10 detik
  - Warna status (paid=hijau, pending=biru, failed=merah, unpaid=oranye)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from db import get_db
from midtrans_webhook import reduce_stock

PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_B   = "#1565C0"
ROW_ALT    = "#FFF5F5"

PAY_COLOR = {
    "unpaid":  "#E65100",
    "pending": "#1565C0",
    "paid":    "#2E7D32",
    "failed":  "#B71C1C",
    "expired": "#757575",
}

PAY_EMOJI = {
    "unpaid":  "⏳",
    "pending": "🔵",
    "paid":    "✅",
    "failed":  "❌",
    "expired": "⌛",
}


class PembayaranPanel(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=LIGHT_GRAY)
        self.dashboard   = dashboard
        self._auto_id    = None
        self._build()
        self._load()
        self._start_auto_refresh()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=WHITE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="💳  Status Pembayaran Midtrans",
                 font=("Segoe UI", 15, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left", padx=24, pady=14)

        tk.Button(hdr, text="🔄 Refresh", font=("Segoe UI", 9),
                  bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self._load).pack(side="right", padx=16)

        # Filter
        filter_frame = tk.Frame(self, bg=WHITE)
        filter_frame.pack(fill="x", padx=20, pady=8)

        tk.Label(filter_frame, text="Filter Status:", font=("Segoe UI", 9), bg=WHITE).pack(side="left", padx=(0,5))
        self.cb_status = ttk.Combobox(filter_frame, values=["SEMUA", "UNPAID", "PENDING", "WAITING_CONFIRMATION", "PAID", "FAILED", "EXPIRED", "REJECTED"], width=18, state="readonly")
        self.cb_status.set("SEMUA")
        self.cb_status.pack(side="left", padx=5)
        self.cb_status.bind("<<ComboboxSelected>>", lambda _: self._load())

        tk.Label(filter_frame, text="Metode:", font=("Segoe UI", 9), bg=WHITE).pack(side="left", padx=(15,5))
        self.cb_meth = ttk.Combobox(filter_frame, values=["SEMUA", "MIDTRANS", "CASH"], width=12, state="readonly")
        self.cb_meth.set("SEMUA")
        self.cb_meth.pack(side="left", padx=5)
        self.cb_meth.bind("<<ComboboxSelected>>", lambda _: self._load())

        # Tombol aksi admin
        self.btn_paid = tk.Button(filter_frame, text="✅ Konfirmasi PAID", font=("Segoe UI", 9, "bold"),
                                   bg="#2E7D32", fg=WHITE, relief="flat", padx=12, pady=4, state="disabled",
                                   command=self._confirm_paid)
        self.btn_paid.pack(side="right", padx=5)

        self.btn_reject = tk.Button(filter_frame, text="❌ Tolak Pembayaran", font=("Segoe UI", 9, "bold"),
                                     bg="#B71C1C", fg=WHITE, relief="flat", padx=12, pady=4, state="disabled",
                                     command=self._reject_payment)
        self.btn_reject.pack(side="right", padx=5)

        # Legend
        legend = tk.Frame(self, bg=WHITE)
        legend.pack(fill="x", padx=20, pady=(8, 0))
        for ps, clr in PAY_COLOR.items():
            em = PAY_EMOJI.get(ps, "")
            tk.Label(legend, text=f"{em} {ps.upper()}",
                     font=("Segoe UI", 8, "bold"),
                     bg=WHITE, fg=clr).pack(side="left", padx=10, pady=6)

        # Treeview
        table_frame = tk.Frame(self, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=12)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Pay.Treeview",
                        font=("Segoe UI", 9), rowheight=30,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Pay.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background="#00796B", foreground=WHITE, relief="flat")
        style.map("Pay.Treeview",
                  background=[("selected", "#B2DFDB")],
                  foreground=[("selected", DARK_TEXT)])

        cols = ("ID", "Nama", "Tanggal", "Total", "Metode", "Pay Status", "Trx ID")
        self.tv = ttk.Treeview(table_frame, columns=cols,
                               show="headings", style="Pay.Treeview")

        self.tv.heading("ID",         text="ID Pesanan")
        self.tv.heading("Nama",       text="Nama Pembeli")
        self.tv.heading("Tanggal",    text="Tanggal")
        self.tv.heading("Total",      text="Total Harga")
        self.tv.heading("Metode",     text="Metode Bayar")
        self.tv.heading("Pay Status", text="Pay. Status")
        self.tv.heading("Trx ID",     text="Transaction ID")

        self.tv.column("ID",         width=70,  anchor="center")
        self.tv.column("Nama",       width=130, anchor="w")
        self.tv.column("Tanggal",    width=145, anchor="center")
        self.tv.column("Total",      width=110, anchor="e")
        self.tv.column("Metode",     width=110, anchor="center")
        self.tv.column("Pay Status", width=100, anchor="center")
        self.tv.column("Trx ID",     width=160, anchor="w")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv.pack(fill="both", expand=True)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)

        # Footer info auto-refresh
        self.lbl_info = tk.Label(self, text="",
                                  font=("Segoe UI", 8), bg=LIGHT_GRAY, fg=GRAY_TEXT)
        self.lbl_info.pack(anchor="e", padx=24, pady=(0, 8))

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load(self):
        for item in self.tv.get_children():
            self.tv.delete(item)
        try:
            db = get_db()
            docs = db.collection('pesanan').get()
            
            rows = []
            for doc in docs:
                r = doc.to_dict()
                r["id_pesanan"] = doc.id
                rows.append(r)
                
            st_f = self.cb_status.get()
            me_f = self.cb_meth.get()
            
            filtered_rows = []
            for r in rows:
                ps = r.get("payment_status") or "unpaid"
                metode = r.get("payment_method") or "-"
                
                if st_f != "SEMUA" and ps.upper() != st_f:
                    continue
                if me_f != "SEMUA" and metode.upper() != me_f:
                    continue
                filtered_rows.append(r)
                
            filtered_rows.sort(key=lambda x: x.get("tanggal", ""), reverse=True)
            
            for r in filtered_rows:
                ps      = r.get("payment_status") or "unpaid"
                em      = PAY_EMOJI.get(ps, "")
                metode  = (r.get("payment_method") or "-").upper()
                tx_id   = r.get("transaction_id") or "-"
                nama    = r.get("nama_pembeli") or "-"
                total   = f"Rp {r.get('total_harga', 0):,.0f}"
                tgl     = str(r.get("tanggal", ""))[:19]

                self.tv.insert("", "end", iid=r["id_pesanan"],
                               values=(
                                   r["id_pesanan"][:8],
                                   nama,
                                   tgl,
                                   total,
                                   metode,
                                   f"{em} {ps.upper()}",
                                   tx_id,
                               ),
                               tags=(ps,))

            # Tag warna per status
            for ps, clr in PAY_COLOR.items():
                self.tv.tag_configure(ps, foreground=clr)

            import datetime
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.lbl_info.config(text=f"Terakhir diperbarui: {now}  |  Auto-refresh setiap 10 detik")

        except Exception as e:
            messagebox.showerror("Error DB", str(e))

    def _on_select(self, _):
        sel = self.tv.selection()
        if not sel:
            self.btn_paid.config(state="disabled")
            self.btn_reject.config(state="disabled")
            return

        iid = sel[0]
        # Ambil data dari treeview (Pay Status ada di index 5)
        vals = self.tv.item(iid, "values")
        status = vals[5].lower() # format: "✅ PAID" -> butuh mapping atau raw
        
        # Cari status asli di DB/Tags
        tags = self.tv.item(iid, "tags")
        raw_status = tags[0] if tags else ""

        if raw_status == "waiting_confirmation":
            self.btn_paid.config(state="normal")
            self.btn_reject.config(state="normal")
        else:
            self.btn_paid.config(state="disabled")
            self.btn_reject.config(state="disabled")

    def _confirm_paid(self):
        sel = self.tv.selection()
        if not sel: return
        oid = sel[0] # Full Firestore doc.id
        short_id = self.tv.item(sel[0], "values")[0]
        if messagebox.askyesno("Konfirmasi", f"Konfirmasi pembayaran Cash untuk Pesanan #{short_id} sebagai PAID?"):
            try:
                import datetime
                db = get_db()
                doc_ref = db.collection('pesanan').document(oid)
                doc_ref.update({
                    'payment_status': 'paid',
                    'status': 'diterima',
                    'confirmed_by_admin': self.dashboard.admin_data['username'],
                    'confirmed_at': datetime.datetime.now()
                })
                reduce_stock(oid)
                messagebox.showinfo("Sukses", f"Pesanan #{short_id} telah ditandai PAID dan stok dikurangi.")
                self._load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _reject_payment(self):
        sel = self.tv.selection()
        if not sel: return
        oid = sel[0] # Full Firestore doc.id
        short_id = self.tv.item(sel[0], "values")[0]
        if messagebox.askyesno("Tolak", f"Tolak pembayaran untuk Pesanan #{short_id}?"):
            try:
                import datetime
                db = get_db()
                doc_ref = db.collection('pesanan').document(oid)
                doc_ref.update({
                    'payment_status': 'rejected',
                    'confirmed_by_admin': self.dashboard.admin_data['username'],
                    'confirmed_at': datetime.datetime.now()
                })
                self._load()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    def _start_auto_refresh(self):
        self._auto_id = self.after(10000, self._auto_tick)

    def _auto_tick(self):
        if self.winfo_exists():
            self._load()
            self._auto_id = self.after(10000, self._auto_tick)

    def destroy(self):
        if self._auto_id:
            try:
                self.after_cancel(self._auto_id)
            except Exception:
                pass
        super().destroy()
