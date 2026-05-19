"""
admin/konfirmasi.py - Panel Konfirmasi Pesanan (Redesign Premium)
Aplikasi Business Center SMKN 13 Bandung
Palet: Dark Green #051F20 → Pale Mint #DAF1DE
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from db import get_db

# ─── Palet Warna (seragam seluruh aplikasi) ───────────────────
C_DARKEST   = "#051F20"
C_DARK      = "#0B2B26"
C_MID       = "#163832"
C_MUTED     = "#235347"
C_MINT      = "#8EB69B"
C_PALE      = "#DAF1DE"
WHITE       = "#FFFFFF"
BG_MAIN     = "#F4FAF6"
BORDER_CLR  = "#D1E8D8"
DARK_TEXT   = "#1A2E22"
GRAY_TEXT   = "#5C7A68"
LIGHT_TEXT  = "#9DB8A8"

# Status colors
S_PENDING   = "#C07A00"   # amber
S_DITERIMA  = "#163832"   # hijau gelap
S_DITOLAK   = "#8B1A1A"   # merah gelap

S_BG_PENDING  = "#FFF8E1"
S_BG_DITERIMA = "#F0FAF4"
S_BG_DITOLAK  = "#FFF0F0"

BTN_ACCEPT  = "#163832"
BTN_ACCEPT_H= "#0B2B26"
BTN_REJECT  = "#7A2020"
BTN_REJECT_H= "#5C1515"

PAY_COLOR = {
    "unpaid":  "#C07A00",
    "waiting_confirmation": "#1565C0",
    "pending": "#1565C0",
    "paid":    "#163832",
    "failed":  "#8B1A1A",
    "expired": "#5C7A68",
}


# ─── Helper: pill button ──────────────────────────────────────────────────────
def _pill(parent, text, command, w=150, h=38, r=19,
          color=C_MID, hover=C_DARK, fg=WHITE,
          font=("Segoe UI", 9, "bold")):
    cv = tk.Canvas(parent, width=w, height=h,
                   bg=parent["bg"], highlightthickness=0, cursor="hand2")
    def _draw(fill):
        cv.delete("all")
        cv.create_arc(0,0,r*2,h,start=90,extent=180,fill=fill,outline=fill)
        cv.create_arc(w-r*2,0,w,h,start=270,extent=180,fill=fill,outline=fill)
        cv.create_rectangle(r,0,w-r,h,fill=fill,outline=fill)
        cv.create_text(w//2,h//2,text=text,fill=fg,font=font,anchor="center")
    _draw(color)
    cv.bind("<Enter>",    lambda e: _draw(hover))
    cv.bind("<Leave>",    lambda e: _draw(color))
    cv.bind("<Button-1>", lambda e: command())
    return cv


def _pill_disabled(parent, text, w=150, h=38, r=19,
                   font=("Segoe UI", 9, "bold")):
    cv = tk.Canvas(parent, width=w, height=h,
                   bg=parent["bg"], highlightthickness=0)
    cv.create_arc(0,0,r*2,h,start=90,extent=180,fill=BORDER_CLR,outline=BORDER_CLR)
    cv.create_arc(w-r*2,0,w,h,start=270,extent=180,fill=BORDER_CLR,outline=BORDER_CLR)
    cv.create_rectangle(r,0,w-r,h,fill=BORDER_CLR,outline=BORDER_CLR)
    cv.create_text(w//2,h//2,text=text,fill=LIGHT_TEXT,font=font,anchor="center")
    return cv


class KonfirmasiPanel(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=BG_MAIN)
        self.dashboard   = dashboard
        self.selected_id = None
        self._filter_val = "semua"
        self._build_styles()
        self._build()
        self._load_pesanan()

    def _build_styles(self):
        s = ttk.Style()
        s.theme_use("default")

        # Treeview pesanan
        s.configure("Pesanan.Treeview",
                    font=("Segoe UI", 9), rowheight=32,
                    background=WHITE, fieldbackground=WHITE,
                    foreground=DARK_TEXT, borderwidth=0)
        s.configure("Pesanan.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=BG_MAIN, foreground=GRAY_TEXT,
                    relief="flat", borderwidth=0)
        s.map("Pesanan.Treeview",
              background=[("selected", C_PALE)],
              foreground=[("selected", C_DARKEST)])

        # Treeview detail
        s.configure("Detail.Treeview",
                    font=("Segoe UI", 9), rowheight=30,
                    background=WHITE, fieldbackground=WHITE,
                    foreground=DARK_TEXT, borderwidth=0)
        s.configure("Detail.Treeview.Heading",
                    font=("Segoe UI", 8, "bold"),
                    background=BG_MAIN, foreground=GRAY_TEXT,
                    relief="flat", borderwidth=0)
        s.map("Detail.Treeview",
              background=[("selected", C_PALE)])

        # Scrollbar tipis
        s.configure("Thin.Vertical.TScrollbar",
                    gripcount=0, background=C_MINT,
                    troughcolor=BG_MAIN, borderwidth=0,
                    arrowsize=0, width=5)
        s.map("Thin.Vertical.TScrollbar",
              background=[("active", C_MUTED)])

    def _build(self):
        self._build_topbar()
        self._build_filter_tabs()
        tk.Frame(self, bg=BORDER_CLR, height=1).pack(fill="x")
        self._build_body()

    def _build_topbar(self):
        topbar = tk.Frame(self, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Frame(topbar, bg=C_MID, width=4).pack(side="left", fill="y")

        title_col = tk.Frame(topbar, bg=WHITE)
        title_col.pack(side="left", padx=20, fill="y", pady=12)
        tk.Label(title_col, text="Konfirmasi Pesanan",
                 font=("Segoe UI", 14, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(anchor="w")
        tk.Label(title_col, text="Terima atau tolak pesanan dari pelanggan",
                 font=("Segoe UI", 8),
                 bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")

        btn_ref = _pill(topbar, text="↻  Refresh", command=self._refresh,
                        w=100, h=32, r=16,
                        color=C_PALE, hover=C_MINT, fg=C_MID,
                        font=("Segoe UI", 8, "bold"))
        btn_ref.config(bg=WHITE)
        btn_ref.pack(side="right", padx=20, pady=16)

        btn_clear = _pill(topbar, text="🗑  Hapus Histori", command=self._hapus_semua_histori,
                         w=130, h=32, r=16,
                         color="#7A2020", hover="#5C1515", fg=WHITE,
                         font=("Segoe UI", 8, "bold"))
        btn_clear.config(bg=WHITE)
        btn_clear.pack(side="right", padx=(0, 10), pady=16)

    def _build_filter_tabs(self):
        tab_wrap = tk.Frame(self, bg=WHITE)
        tab_wrap.pack(fill="x", padx=20, pady=(10,0))

        self.filter_btns = {}
        filters = [
            ("Semua",        "semua"),
            ("⏳  Pending",  "pending"),
            ("✅  Diterima", "diterima"),
            ("❌  Ditolak",  "ditolak"),
        ]
        for label, key in filters:
            btn = tk.Label(tab_wrap, text=label,
                           font=("Segoe UI", 9, "bold"),
                           bg=WHITE, fg=LIGHT_TEXT,
                           padx=14, pady=8, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._set_filter(k))
            self.filter_btns[key] = btn

        self._set_filter("semua", init=True)

    def _build_body(self):
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Panel kiri: daftar pesanan
        left = tk.Frame(body, bg=WHITE,
                        highlightbackground=BORDER_CLR,
                        highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0,8))

        # Sub-header kiri
        l_hdr = tk.Frame(left, bg=WHITE)
        l_hdr.pack(fill="x", padx=14, pady=(12,8))
        tk.Frame(l_hdr, bg=C_MID, width=4, height=16).pack(side="left")
        tk.Label(l_hdr, text="  Daftar Pesanan",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left")
        self.lbl_count = tk.Label(l_hdr, text="",
                                   font=("Segoe UI", 8),
                                   bg=WHITE, fg=GRAY_TEXT)
        self.lbl_count.pack(side="left", padx=6)

        tk.Frame(left, bg=BORDER_CLR, height=1).pack(fill="x")

        # Treeview
        tree_wrap = tk.Frame(left, bg=WHITE)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("ID", "Tanggal", "Total", "Status", "Pembayaran")
        self.tree = ttk.Treeview(tree_wrap, columns=cols,
                                  show="headings", style="Pesanan.Treeview",
                                  selectmode="browse")
        self.tree.heading("ID",      text="ID")
        self.tree.heading("Tanggal", text="Tanggal & Jam")
        self.tree.heading("Total",   text="Total Harga")
        self.tree.heading("Status",  text="Status")
        self.tree.heading("Pembayaran", text="Pembayaran")

        self.tree.column("ID",         width=55,  anchor="center", stretch=False)
        self.tree.column("Tanggal",    width=150, anchor="center")
        self.tree.column("Total",      width=110, anchor="e",  stretch=False)
        self.tree.column("Status",     width=90,  anchor="center", stretch=False)
        self.tree.column("Pembayaran", width=95,  anchor="center", stretch=False)

        tsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                            command=self.tree.yview,
                            style="Thin.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y", pady=4)
        self.tree.pack(fill="both", expand=True, padx=(8,0), pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Panel kanan: detail + aksi
        right = tk.Frame(body, bg=WHITE, width=300,
                         highlightbackground=BORDER_CLR,
                         highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_detail_panel(right)

    def _build_detail_panel(self, parent):
        # Header detail
        d_hdr = tk.Frame(parent, bg=C_DARKEST, height=52)
        d_hdr.pack(fill="x")
        d_hdr.pack_propagate(False)
        tk.Label(d_hdr, text="Detail Pesanan",
                 font=("Segoe UI", 10, "bold"),
                 bg=C_DARKEST, fg=WHITE).pack(
                     side="left", padx=16, pady=15)

        # Info pesanan
        info = tk.Frame(parent, bg=WHITE)
        info.pack(fill="x", padx=14, pady=(14,8))

        self.lbl_id = tk.Label(info, text="Pilih pesanan dari daftar",
                                font=("Segoe UI", 11, "bold"),
                                bg=WHITE, fg=DARK_TEXT, anchor="w",
                                wraplength=260, justify="left")
        self.lbl_id.pack(anchor="w")

        self.lbl_tgl = tk.Label(info, text="",
                                 font=("Segoe UI", 8),
                                 bg=WHITE, fg=GRAY_TEXT, anchor="w")
        self.lbl_tgl.pack(anchor="w", pady=(2,0))

        # Badge status
        self.badge_frame = tk.Frame(parent, bg=WHITE)
        self.badge_frame.pack(fill="x", padx=14, pady=(0,10))
        self.lbl_badge = tk.Label(self.badge_frame, text="",
                                   font=("Segoe UI", 8, "bold"),
                                   bg=WHITE, fg=WHITE,
                                   padx=10, pady=4)
        self.lbl_badge.pack(side="left")

        tk.Frame(parent, bg=BORDER_CLR, height=1).pack(fill="x", padx=14)

        # Label detail items
        di_hdr = tk.Frame(parent, bg=WHITE)
        di_hdr.pack(fill="x", padx=14, pady=(10,6))
        tk.Frame(di_hdr, bg=C_MINT, width=3, height=14).pack(side="left")
        tk.Label(di_hdr, text="  Item Dipesan",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left")

        # Treeview detail items
        det_wrap = tk.Frame(parent, bg=WHITE)
        det_wrap.pack(fill="both", expand=True, padx=8, pady=(0,4))

        det_cols = ("Barang", "Jml", "Subtotal")
        self.tree_detail = ttk.Treeview(det_wrap, columns=det_cols,
                                         show="headings", style="Detail.Treeview",
                                         height=6)
        self.tree_detail.heading("Barang",   text="Nama Barang")
        self.tree_detail.heading("Jml",      text="Qty")
        self.tree_detail.heading("Subtotal", text="Subtotal")
        self.tree_detail.column("Barang",   width=130, anchor="w")
        self.tree_detail.column("Jml",      width=36,  anchor="center", stretch=False)
        self.tree_detail.column("Subtotal", width=90,  anchor="e",  stretch=False)

        dsb = ttk.Scrollbar(det_wrap, orient="vertical",
                            command=self.tree_detail.yview,
                            style="Thin.Vertical.TScrollbar")
        self.tree_detail.configure(yscrollcommand=dsb.set)
        dsb.pack(side="right", fill="y")
        self.tree_detail.pack(fill="both", expand=True)

        tk.Frame(parent, bg=BORDER_CLR, height=1).pack(fill="x", padx=14, pady=(4,0))

        # Total
        tot_f = tk.Frame(parent, bg=WHITE)
        tot_f.pack(fill="x", padx=14, pady=10)
        tk.Label(tot_f, text="Total:",
                 font=("Segoe UI", 9),
                 bg=WHITE, fg=GRAY_TEXT).pack(side="left")
        self.lbl_total = tk.Label(tot_f, text="—",
                                   font=("Segoe UI", 16, "bold"),
                                   bg=WHITE, fg=C_MID)
        self.lbl_total.pack(side="right")

        tk.Frame(parent, bg=BORDER_CLR, height=1).pack(fill="x")

        # Info pembayaran Midtrans
        self.lbl_payment = tk.Label(parent, text="",
                                    font=("Segoe UI", 8),
                                    bg=WHITE, fg=GRAY_TEXT,
                                    anchor="w", justify="left", wraplength=260)
        self.lbl_payment.pack(fill="x", padx=14, pady=(8,0))

        # Notif aksi
        self.lbl_aksi_notif = tk.Label(parent, text="",
                                        font=("Segoe UI", 8),
                                        bg=WHITE, fg=GRAY_TEXT,
                                        wraplength=260, justify="center")
        self.lbl_aksi_notif.pack(fill="x", padx=10, pady=(6,0))

        # Tombol aksi
        self.aksi_frame = tk.Frame(parent, bg=WHITE)
        self.aksi_frame.pack(fill="x", padx=14, pady=(6,14))
        self._render_aksi_buttons(enabled=False, status=None)

    def _render_aksi_buttons(self, enabled: bool, status: str, pay_meth: str = "-", pay_st: str = "-"):
        for w in self.aksi_frame.winfo_children():
            w.destroy()

        if not enabled:
            d1 = _pill_disabled(self.aksi_frame, text="✅  Terima",
                                 w=260, h=40, r=20)
            d1.pack(pady=(0,8))
            d2 = _pill_disabled(self.aksi_frame, text="❌  Tolak",
                                 w=260, h=40, r=20)
            d2.pack()
            self.lbl_aksi_notif.config(text="")
            return

        if pay_meth.upper() == "CASH" and pay_st == "waiting_confirmation":
            self.lbl_aksi_notif.config(text="Pembayaran Tunai menunggu konfirmasi.")
            b1 = _pill(self.aksi_frame, text="💰  Konfirmasi Bayar Cash",
                       command=self._confirm_cash_manual,
                       w=260, h=42, r=21,
                       color="#2E7D32", hover="#1B5E20",
                       font=("Segoe UI", 9, "bold"))
            b1.config(bg=WHITE)
            b1.pack(pady=(0,8))

            b2 = _pill(self.aksi_frame, text="❌  Tolak Pesanan",
                       command=self._tolak_pesanan,
                       w=260, h=42, r=21,
                       color=BTN_REJECT, hover=BTN_REJECT_H,
                       font=("Segoe UI", 10, "bold"))
            b2.config(bg=WHITE)
            b2.pack()
        elif status == "pending":
            self.lbl_aksi_notif.config(text="")
            b1 = _pill(self.aksi_frame, text="✅  Terima Pesanan",
                       command=self._terima_pesanan,
                       w=260, h=42, r=21,
                       color=BTN_ACCEPT, hover=BTN_ACCEPT_H,
                       font=("Segoe UI", 10, "bold"))
            b1.config(bg=WHITE)
            b1.pack(pady=(0,8))

            b2 = _pill(self.aksi_frame, text="❌  Tolak Pesanan",
                       command=self._tolak_pesanan,
                       w=260, h=42, r=21,
                       color=BTN_REJECT, hover=BTN_REJECT_H,
                       font=("Segoe UI", 10, "bold"))
            b2.config(bg=WHITE)
            b2.pack()
        else:
            # Selesai (diterima atau ditolak)
            self.lbl_aksi_notif.config(
                text=f"Pesanan ini sudah {status.upper()}.",
                fg=GRAY_TEXT)
            b1 = _pill(self.aksi_frame, text="🗑  Hapus Pesanan Ini",
                       command=self._hapus_pesanan,
                       w=260, h=42, r=21,
                       color="#37474F", hover="#263238",
                       font=("Segoe UI", 10, "bold"))
            b1.config(bg=WHITE)
            b1.pack()

    def _set_filter(self, key: str, init: bool = False):
        self._filter_val = key
        for k, btn in self.filter_btns.items():
            if k == key:
                btn.config(fg=C_MID, font=("Segoe UI", 9, "bold"))
            else:
                btn.config(fg=LIGHT_TEXT, font=("Segoe UI", 9))
        if not init:
            self._load_pesanan()

    def _load_pesanan(self):
        self.selected_id = None
        self._clear_detail()
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            from firebase_admin import firestore
            db = get_db()
            if self._filter_val == "semua":
                docs = db.collection('pesanan').order_by('tanggal', direction=firestore.Query.DESCENDING).stream()
            else:
                docs = db.collection('pesanan').where('status', '==', self._filter_val).order_by('tanggal', direction=firestore.Query.DESCENDING).stream()
            
            docs_list = list(docs)
            self.lbl_count.config(text=f"({len(docs_list)} pesanan)")

            # Tag warna per status
            self.tree.tag_configure("pending",
                background=S_BG_PENDING,  foreground=S_PENDING)
            self.tree.tag_configure("diterima",
                background=S_BG_DITERIMA, foreground=S_DITERIMA)
            self.tree.tag_configure("ditolak",
                background=S_BG_DITOLAK,  foreground=S_DITOLAK)

            STATUS_LABEL = {
                "pending":  "⏳ Pending",
                "diterima": "✅ Diterima",
                "ditolak":  "❌ Ditolak",
            }
            for doc in docs_list:
                r = doc.to_dict()
                total = f"Rp {r.get('total_harga', 0):,.0f}"
                status = r.get("status", "")
                label = STATUS_LABEL.get(status, status.upper())
                pay_st = (r.get("payment_status") or "unpaid").upper()
                self.tree.insert("", "end", iid=doc.id,
                                 values=(doc.id[:8],
                                         str(r.get("tanggal", ""))[:19],
                                         total, label, pay_st),
                                 tags=(status,))
        except Exception as e:
            messagebox.showerror("Error DB", str(e), parent=self)

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = str(sel[0])
        self._load_detail(self.selected_id)

    def _load_detail(self, id_pesanan: str):
        self._clear_detail()
        try:
            db = get_db()
            doc = db.collection('pesanan').document(id_pesanan).get()
            if not doc.exists:
                return
            p = doc.to_dict()
            status = p.get("status", "")
            pay_st = p.get("payment_status") or "unpaid"
            pay_meth = p.get("payment_method") or "-"
            tx_id = p.get("transaction_id") or "-"
            nama_pmb = p.get("nama_pembeli") or "-"

            self.lbl_id.config(text=f"Pesanan #{id_pesanan[:8]}  |  {nama_pmb}")
            self.lbl_tgl.config(text=f"📅 {str(p.get('tanggal', ''))[:19]}")
            self.lbl_total.config(text=f"Rp {p.get('total_harga', 0):,.0f}")

            # Badge status
            badge_cfg = {
                "pending":  (S_BG_PENDING,  S_PENDING,  "⏳  PENDING"),
                "diterima": (S_BG_DITERIMA, S_DITERIMA, "✅  DITERIMA"),
                "ditolak":  (S_BG_DITOLAK,  S_DITOLAK,  "❌  DITOLAK"),
            }
            bg, fg, txt = badge_cfg.get(status, (BG_MAIN, GRAY_TEXT, status.upper()))
            self.lbl_badge.config(text=txt, bg=bg, fg=fg)

            # Info pembayaran Midtrans
            pay_clr = PAY_COLOR.get(pay_st, GRAY_TEXT)
            self.lbl_payment.config(
                text=f"💳 Pembayaran: {pay_st.upper()}  |  Metode: {pay_meth.upper()}\n"
                     f"🆔 Trans ID: {tx_id}",
                fg=pay_clr
            )

            # Render tombol sesuai status
            self._render_aksi_buttons(enabled=True, status=status, pay_meth=pay_meth, pay_st=pay_st)

            # Detail items
            detail_rows = p.get('detail_pesanan', [])
            for dr in detail_rows:
                sub = f"Rp {dr.get('subtotal', 0):,.0f}"
                self.tree_detail.insert("", "end",
                                        values=(dr.get("nama_barang", ""), dr.get("jumlah", 0), sub))
        except Exception as e:
            messagebox.showerror("Error DB", str(e), parent=self)

    def _confirm_cash_manual(self):
        if not self.selected_id: return
        short_id = self.selected_id[:8]
        if messagebox.askyesno("Konfirmasi", f"Konfirmasi pembayaran CASH untuk Pesanan #{short_id}?\n\nStatus akan berubah menjadi PAID dan stok akan dikurangi."):
            try:
                import datetime
                db = get_db()
                doc_ref = db.collection('pesanan').document(self.selected_id)
                doc_ref.update({
                    'payment_status': 'paid',
                    'status': 'diterima',
                    'confirmed_at': datetime.datetime.now()
                })
                # Kurangi stok
                from midtrans_webhook import reduce_stock
                reduce_stock(self.selected_id)
                messagebox.showinfo("Sukses", f"Pesanan #{short_id} telah lunas (PAID).")
                self._load_pesanan()
                self._load_detail(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _clear_detail(self):
        for row in self.tree_detail.get_children():
            self.tree_detail.delete(row)
        self.lbl_id.config(text="Pilih pesanan dari daftar")
        self.lbl_tgl.config(text="")
        self.lbl_total.config(text="—")
        self.lbl_badge.config(text="", bg=WHITE)
        self.lbl_payment.config(text="")
        self.lbl_aksi_notif.config(text="")
        self._render_aksi_buttons(enabled=False, status=None)

    def _terima_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Konfirmasi Terima",
                                    f"Terima pesanan #{self.selected_id[:8]}?\n\nStok barang akan dikurangi.",
                                    parent=self):
            return
        try:
            from firebase_admin import firestore
            db = get_db()
            doc_ref = db.collection('pesanan').document(self.selected_id)
            doc = doc_ref.get()
            if not doc.exists: return
            p = doc.to_dict()
            details = p.get('detail_pesanan', [])

            # Cek stok
            for d in details:
                b_doc = db.collection('barang').document(d["id_barang"]).get()
                if not b_doc.exists: continue
                b = b_doc.to_dict()
                if b.get("stok", 0) < d["jumlah"]:
                    messagebox.showwarning(
                        "Stok Tidak Cukup",
                        f"Stok \"{b.get('nama_barang', '')}\" tidak mencukupi!\n"
                        f"Tersedia: {b.get('stok', 0)}, Dibutuhkan: {d['jumlah']}",
                        parent=self
                    )
                    return

            # Kurangi stok
            batch = db.batch()
            for d in details:
                b_ref = db.collection('barang').document(d["id_barang"])
                batch.update(b_ref, {'stok': firestore.Increment(-d["jumlah"])})

            batch.update(doc_ref, {'status': 'diterima'})
            batch.commit()

            messagebox.showinfo(
                "Berhasil",
                f"✅ Pesanan #{self.selected_id[:8]} DITERIMA!\nStok berhasil dikurangi.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _tolak_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("Konfirmasi Tolak",
                                    f"Tolak pesanan #{self.selected_id[:8]}?\n\nStok tidak akan berubah.",
                                    parent=self):
            return
        try:
            db = get_db()
            db.collection('pesanan').document(self.selected_id).update({'status': 'ditolak'})
            messagebox.showinfo(
                "Info",
                f"❌ Pesanan #{self.selected_id[:8]} DITOLAK.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _hapus_pesanan(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno(
            "Hapus Pesanan",
            f"Hapus histori pesanan #{self.selected_id[:8]} secara permanen?",
            parent=self
        ):
            return
        try:
            db = get_db()
            db.collection('pesanan').document(self.selected_id).delete()
            messagebox.showinfo(
                "Berhasil",
                f"🗑  Pesanan #{self.selected_id[:8]} berhasil dihapus.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _hapus_semua_histori(self):
        try:
            db = get_db()
            docs = db.collection('pesanan').where('status', 'in', ['diterima', 'ditolak']).stream()
            doc_ids = [d.id for d in docs]
            jumlah = len(doc_ids)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        if jumlah == 0:
            messagebox.showinfo(
                "Info",
                "Tidak ada histori yang bisa dihapus.\n(Pesanan pending tidak akan dihapus.)",
                parent=self
            )
            return

        if not messagebox.askyesno(
            "Hapus Semua Histori",
            f"Akan menghapus {jumlah} pesanan (diterima & ditolak) secara permanen.\n"
            "Pesanan berstatus PENDING tidak akan terpengaruh.\n\nLanjutkan?",
            parent=self
        ):
            return

        try:
            batch = db.batch()
            for did in doc_ids:
                batch.delete(db.collection('pesanan').document(did))
            batch.commit()

            messagebox.showinfo(
                "Berhasil",
                f"🗑  {jumlah} histori pesanan berhasil dihapus.",
                parent=self
            )
            self._refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _refresh(self):
        self.selected_id = None
        self._clear_detail()
        self._load_pesanan()
