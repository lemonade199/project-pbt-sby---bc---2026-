"""
admin/dashboard.py - Dashboard Admin (Full Redesign Premium)
Aplikasi Business Center SMKN 13 Bandung
Palet: Dark Green #051F20 → Pale Mint #DAF1DE
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from db import get_db

# ─── Palet Warna (seragam seluruh aplikasi) ───────────────────
C_DARKEST    = "#051F20"
C_DARK       = "#0B2B26"
C_MID        = "#163832"
C_MUTED      = "#235347"
C_MINT       = "#8EB69B"
C_PALE       = "#DAF1DE"
WHITE        = "#FFFFFF"
BG_MAIN      = "#F4FAF6"
BORDER_CLR   = "#D1E8D8"
DARK_TEXT    = "#1A2E22"
GRAY_TEXT    = "#5C7A68"
LIGHT_TEXT   = "#9DB8A8"

# Warna kartu statistik
CARD_COLORS  = [
    ("#163832", "#DAF1DE"),   # barang      → mid green
    ("#0B2B26", "#8EB69B"),   # pending     → dark green
    ("#235347", "#DAF1DE"),   # diterima    → muted
    ("#6B3A2A", "#F5DDD5"),   # ditolak     → terracotta hangat
    ("#004D40", "#E0F2F1"),   # paid        → teal
]

SIDEBAR_W    = 220


# ─── Helper: pill button ──────────────────────────────────────────────────────
def _pill(parent, text, command, w=160, h=36, r=18,
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


class AdminDashboard(tk.Toplevel):
    def __init__(self, master, admin_data: dict):
        super().__init__(master)
        self.master        = master
        self.admin_data    = admin_data
        self.active_frame  = None
        self.sidebar_btns  = {}
        self._active_key   = None

        self.title("Admin Dashboard — Business Center SMKN 13 Bandung")
        self.geometry("1120x660")
        self.minsize(960, 580)
        self.configure(bg=BG_MAIN)
        self._center(1120, 660)
        self._build_styles()
        self._build_ui()
        self._show_home()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_styles(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Dash.Treeview",
                    font=("Segoe UI", 9), rowheight=32,
                    background=WHITE, fieldbackground=WHITE,
                    foreground=DARK_TEXT, borderwidth=0)
        s.configure("Dash.Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background=BG_MAIN, foreground=GRAY_TEXT,
                    relief="flat", borderwidth=0)
        s.map("Dash.Treeview",
              background=[("selected", C_PALE)],
              foreground=[("selected", C_DARKEST)])
        s.configure("Thin.Vertical.TScrollbar",
                    gripcount=0, background=C_MINT,
                    troughcolor=BG_MAIN, borderwidth=0,
                    arrowsize=0, width=5)
        s.map("Thin.Vertical.TScrollbar",
              background=[("active", C_MUTED)])

    def _build_ui(self):
        self._build_sidebar()
        self.content_area = tk.Frame(self, bg=BG_MAIN)
        self.content_area.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C_DARKEST, width=SIDEBAR_W)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self.sidebar = sb

        # Logo area
        logo = tk.Frame(sb, bg=C_DARK, height=72)
        logo.pack(fill="x")
        logo.pack_propagate(False)

        logo_inner = tk.Frame(logo, bg=C_DARK)
        logo_inner.pack(expand=True, fill="both", padx=16)
        tk.Label(logo_inner, text="🏫", font=("Segoe UI Emoji", 20),
                 bg=C_DARK).pack(side="left", pady=16)
        logo_txt = tk.Frame(logo_inner, bg=C_DARK)
        logo_txt.pack(side="left", padx=10, fill="y", pady=16)
        tk.Label(logo_txt, text="BC Admin",
                 font=("Segoe UI", 11, "bold"),
                 bg=C_DARK, fg=WHITE, anchor="w").pack(anchor="w")
        tk.Label(logo_txt, text="SMKN 13 Bandung",
                 font=("Segoe UI", 7),
                 bg=C_DARK, fg=C_MINT, anchor="w").pack(anchor="w")

        # User info
        user_f = tk.Frame(sb, bg=C_DARKEST)
        user_f.pack(fill="x", padx=14, pady=(16, 4))
        tk.Frame(user_f, bg=C_MUTED, height=1).pack(fill="x", pady=(0,10))

        avatar_f = tk.Frame(user_f, bg=C_MUTED, width=36, height=36)
        avatar_f.pack(side="left")
        avatar_f.pack_propagate(False)
        tk.Label(avatar_f, text="👤", font=("Segoe UI Emoji", 16),
                 bg=C_MUTED).pack(expand=True)

        user_info = tk.Frame(user_f, bg=C_DARKEST)
        user_info.pack(side="left", padx=10, fill="y")
        tk.Label(user_info,
                 text=self.admin_data.get("username", "Admin"),
                 font=("Segoe UI", 9, "bold"),
                 bg=C_DARKEST, fg=WHITE, anchor="w").pack(anchor="w")
        tk.Label(user_info,
                 text=self.admin_data.get("role", "Administrator").title(),
                 font=("Segoe UI", 7),
                 bg=C_DARKEST, fg=C_MINT, anchor="w").pack(anchor="w")

        tk.Frame(sb, bg=C_MUTED, height=1).pack(
            fill="x", padx=14, pady=(12,8))

        # Label navigasi
        tk.Label(sb, text="N A V I G A S I",
                 font=("Segoe UI", 7),
                 bg=C_DARKEST, fg=C_MUTED).pack(anchor="w", padx=18, pady=(0,6))

        # Menu items
        menus = [
            ("🏠", "Dashboard",          "home"),
            ("📦", "Kelola Barang",       "barang"),
            ("📋", "Konfirmasi Pesanan",  "konfirmasi"),
            ("💳", "Status Pembayaran",   "pembayaran"),
        ]
        for icon, label, key in menus:
            self._make_menu_item(sb, icon, label, key)

        # Spacer + Logout di bawah
        tk.Frame(sb, bg=C_DARKEST).pack(fill="both", expand=True)
        tk.Frame(sb, bg=C_MUTED, height=1).pack(fill="x", padx=14, pady=8)

        logout_f = tk.Frame(sb, bg=C_DARKEST, cursor="hand2")
        logout_f.pack(fill="x", padx=14, pady=(0,16))
        logout_f.bind("<Button-1>", lambda e: self._logout())

        for widget_side, widget_text, widget_font, widget_fg in [
            ("left", "🚪", ("Segoe UI Emoji", 14), "#FF8A80"),
            ("left", "  Logout", ("Segoe UI", 9, "bold"), "#FF8A80"),
        ]:
            lbl = tk.Label(logout_f, text=widget_text,
                           font=widget_font,
                           bg=C_DARKEST, fg=widget_fg)
            lbl.pack(side=widget_side, pady=10)
            lbl.bind("<Button-1>", lambda e: self._logout())
            lbl.bind("<Enter>", lambda e, f=logout_f: f.config(bg="#1A0808") or
                     [w.config(bg="#1A0808") for w in f.winfo_children()])
            lbl.bind("<Leave>", lambda e, f=logout_f: f.config(bg=C_DARKEST) or
                     [w.config(bg=C_DARKEST) for w in f.winfo_children()])

    def _make_menu_item(self, parent, icon, label, key):
        item_f = tk.Frame(parent, bg=C_DARKEST, cursor="hand2", height=44)
        item_f.pack(fill="x", padx=10, pady=2)
        item_f.pack_propagate(False)

        accent = tk.Frame(item_f, bg=C_DARKEST, width=4)
        accent.pack(side="left", fill="y")

        icon_lbl = tk.Label(item_f, text=icon,
                            font=("Segoe UI Emoji", 13),
                            bg=C_DARKEST, fg=LIGHT_TEXT)
        icon_lbl.pack(side="left", padx=(8,6))

        text_lbl = tk.Label(item_f, text=label,
                            font=("Segoe UI", 9),
                            bg=C_DARKEST, fg=LIGHT_TEXT, anchor="w")
        text_lbl.pack(side="left", fill="x", expand=True)

        def _enter(e):
            if self._active_key != key:
                for w in [item_f, icon_lbl, text_lbl]:
                    w.config(bg=C_DARK)
                accent.config(bg=C_DARK)

        def _leave(e):
            if self._active_key != key:
                for w in [item_f, icon_lbl, text_lbl]:
                    w.config(bg=C_DARKEST)
                accent.config(bg=C_DARKEST)

        def _click(e=None):
            self._navigate(key)

        for w in [item_f, icon_lbl, text_lbl]:
            w.bind("<Enter>",    _enter)
            w.bind("<Leave>",    _leave)
            w.bind("<Button-1>", _click)

        self.sidebar_btns[key] = {
            "frame": item_f, "accent": accent,
            "icon": icon_lbl, "text": text_lbl
        }

    def _set_active_menu(self, key):
        self._active_key = key
        for k, widgets in self.sidebar_btns.items():
            if k == key:
                widgets["frame"].config(bg=C_MID)
                widgets["accent"].config(bg=C_MINT)
                widgets["icon"].config(bg=C_MID, fg=WHITE)
                widgets["text"].config(bg=C_MID, fg=WHITE,
                                       font=("Segoe UI", 9, "bold"))
            else:
                widgets["frame"].config(bg=C_DARKEST)
                widgets["accent"].config(bg=C_DARKEST)
                widgets["icon"].config(bg=C_DARKEST, fg=LIGHT_TEXT)
                widgets["text"].config(bg=C_DARKEST, fg=LIGHT_TEXT,
                                       font=("Segoe UI", 9))

    def _navigate(self, key: str):
        self._set_active_menu(key)
        if self.active_frame:
            self.active_frame.destroy()
        if key == "home":
            self._show_home()
        elif key == "barang":
            self._show_barang()
        elif key == "konfirmasi":
            self._show_konfirmasi()
        elif key == "pembayaran":
            self._show_pembayaran()

    def _show_home(self):
        self._set_active_menu("home")
        if self.active_frame:
            self.active_frame.destroy()
        self.active_frame = HomeDashboard(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _show_barang(self):
        if self.active_frame:
            self.active_frame.destroy()
        from admin.barang import BarangPanel
        self.active_frame = BarangPanel(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _show_konfirmasi(self):
        if self.active_frame:
            self.active_frame.destroy()
        from admin.konfirmasi import KonfirmasiPanel
        self.active_frame = KonfirmasiPanel(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _show_pembayaran(self):
        if self.active_frame:
            self.active_frame.destroy()
        from admin.pembayaran import PembayaranPanel
        self.active_frame = PembayaranPanel(self.content_area, self)
        self.active_frame.pack(fill="both", expand=True)

    def _logout(self):
        if messagebox.askyesno("Logout", "Yakin ingin keluar dari dashboard admin?", parent=self):
            self.destroy()
            self.master.deiconify()


class HomeDashboard(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=BG_MAIN)
        self.dashboard = dashboard
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Frame(topbar, bg=C_MID, width=4).pack(side="left", fill="y")

        title_col = tk.Frame(topbar, bg=WHITE)
        title_col.pack(side="left", padx=20, fill="y", pady=12)
        tk.Label(title_col, text="Dashboard",
                 font=("Segoe UI", 14, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(anchor="w")
        tk.Label(title_col,
                 text=datetime.datetime.now().strftime("%A, %d %B %Y"),
                 font=("Segoe UI", 8),
                 bg=WHITE, fg=GRAY_TEXT, anchor="w").pack(anchor="w")

        btn_ref = _pill(topbar, text="↻  Refresh", command=self._refresh,
                        w=100, h=32, r=16,
                        color=C_PALE, hover=C_MINT, fg=C_MID,
                        font=("Segoe UI", 8, "bold"))
        btn_ref.config(bg=WHITE)
        btn_ref.pack(side="right", padx=20, pady=16)

        tk.Frame(self, bg=BORDER_CLR, height=1).pack(fill="x")

        # Scrollable content
        canvas = tk.Canvas(self, bg=BG_MAIN, highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical",
                               command=canvas.yview,
                               style="Thin.Vertical.TScrollbar")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.scroll_frame = tk.Frame(canvas, bg=BG_MAIN)
        win = canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e:
            canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e:
            canvas.itemconfig(win, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e:
            canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_content(self.scroll_frame)

    def _build_content(self, parent):
        stats = self._get_stats()
        cards_data = [
            ("📦", "Total Barang",     stats["barang"],   CARD_COLORS[0]),
            ("⏳", "Pesanan Pending",  stats["pending"],  CARD_COLORS[1]),
            ("✅", "Pesanan Diterima", stats["diterima"], CARD_COLORS[2]),
            ("❌", "Pesanan Ditolak",  stats["ditolak"],  CARD_COLORS[3]),
            ("💳", "Pembayaran Paid",  stats["paid"],     CARD_COLORS[4]),
        ]

        stat_wrap = tk.Frame(parent, bg=BG_MAIN)
        stat_wrap.pack(fill="x", padx=20, pady=20)

        for i, (icon, label, value, (bg, fg_accent)) in enumerate(cards_data):
            self._make_stat_card(stat_wrap, icon, label, value, bg, fg_accent, col=i)
            stat_wrap.grid_columnconfigure(i, weight=1, uniform="card")

        # Akses cepat
        quick_wrap = tk.Frame(parent, bg=WHITE,
                              highlightbackground=BORDER_CLR,
                              highlightthickness=1)
        quick_wrap.pack(fill="x", padx=20, pady=(0,16))

        q_hdr = tk.Frame(quick_wrap, bg=WHITE)
        q_hdr.pack(fill="x", padx=16, pady=(14,10))
        tk.Frame(q_hdr, bg=C_MID, width=4, height=18).pack(side="left")
        tk.Label(q_hdr, text="  Akses Cepat",
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left")

        btn_row = tk.Frame(quick_wrap, bg=WHITE)
        btn_row.pack(padx=16, pady=(0,16), anchor="w")

        b1 = _pill(btn_row, text="➕  Tambah Barang",
                   command=lambda: self.dashboard._navigate("barang"),
                   w=180, h=38, r=19,
                   color=C_MID, hover=C_DARK,
                   font=("Segoe UI", 9, "bold"))
        b1.config(bg=WHITE)
        b1.pack(side="left", padx=(0,12))

        b2 = _pill(btn_row, text="📋  Pesanan Pending",
                   command=lambda: self.dashboard._navigate("konfirmasi"),
                   w=190, h=38, r=19,
                   color=C_MUTED, hover=C_MID,
                   font=("Segoe UI", 9, "bold"))
        b2.config(bg=WHITE)
        b2.pack(side="left")

        # Pesanan terbaru
        recent_wrap = tk.Frame(parent, bg=WHITE,
                               highlightbackground=BORDER_CLR,
                               highlightthickness=1)
        recent_wrap.pack(fill="both", expand=True, padx=20, pady=(0,20))

        r_hdr = tk.Frame(recent_wrap, bg=WHITE)
        r_hdr.pack(fill="x", padx=16, pady=(14,8))
        tk.Frame(r_hdr, bg=C_MID, width=4, height=18).pack(side="left")
        tk.Label(r_hdr, text="  Pesanan Terbaru",
                 font=("Segoe UI", 11, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left")

        self._build_recent_table(recent_wrap)

    def _make_stat_card(self, parent, icon, label, value, bg, fg_accent, col):
        card = tk.Frame(parent, bg=bg, height=120)
        card.grid(row=0, column=col, padx=(0 if col==0 else 8, 0), sticky="ew")
        card.pack_propagate(False)

        inner = tk.Frame(card, bg=bg)
        inner.pack(expand=True, fill="both", padx=18, pady=14)

        top = tk.Frame(inner, bg=bg)
        top.pack(fill="x")
        tk.Label(top, text=str(value),
                 font=("Segoe UI", 26, "bold"),
                 bg=bg, fg=WHITE).pack(side="left")
        tk.Label(top, text=icon,
                 font=("Segoe UI Emoji", 22),
                 bg=bg, fg=fg_accent).pack(side="right")

        tk.Label(inner, text=label,
                 font=("Segoe UI", 9),
                 bg=bg, fg=fg_accent, anchor="w").pack(anchor="w", pady=(4,0))

        tk.Frame(card, bg=fg_accent, height=3).pack(fill="x", side="bottom")

    def _get_stats(self) -> dict:
        try:
            db = get_db()
            barang_len = len(db.collection('barang').get())
            pending_len = len(db.collection('pesanan').where('status', '==', 'pending').get())
            diterima_len = len(db.collection('pesanan').where('status', '==', 'diterima').get())
            ditolak_len = len(db.collection('pesanan').where('status', '==', 'ditolak').get())
            paid_len = len(db.collection('pesanan').where('payment_status', '==', 'paid').get())
            
            return {
                "barang":   barang_len,
                "pending":  pending_len,
                "diterima": diterima_len,
                "ditolak":  ditolak_len,
                "paid":     paid_len,
            }
        except Exception as e:
            print(f"Error _get_stats: {e}")
            return {"barang": 0, "pending": 0, "diterima": 0, "ditolak": 0, "paid": 0}

    def _build_recent_table(self, parent):
        cols = ("ID", "Tanggal", "Total", "Status", "Pembayaran")
        tv   = ttk.Treeview(parent, columns=cols, show="headings",
                            style="Dash.Treeview", height=7)
        tv.heading("ID",         text="ID Pesanan")
        tv.heading("Tanggal",    text="Tanggal & Waktu")
        tv.heading("Total",      text="Total Harga")
        tv.heading("Status",     text="Status")
        tv.heading("Pembayaran", text="Pay. Status")

        tv.column("ID",         width=90,  anchor="center")
        tv.column("Tanggal",    width=200, anchor="center")
        tv.column("Total",      width=140, anchor="e")
        tv.column("Status",     width=110, anchor="center")
        tv.column("Pembayaran", width=110, anchor="center")

        sb = ttk.Scrollbar(parent, orient="vertical",
                           command=tv.yview,
                           style="Thin.Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0,16), pady=(0,16))
        tv.pack(fill="both", expand=True, padx=16, pady=(0,16))

        # Tag warna baris status
        tv.tag_configure("pending",  background="#FFF8E1", foreground="#7A5800")
        tv.tag_configure("diterima", background="#F0FAF4", foreground="#163832")
        tv.tag_configure("ditolak",  background="#FFF0F0", foreground="#8B1A1A")

        try:
            from firebase_admin import firestore
            db = get_db()
            docs = db.collection('pesanan').order_by('tanggal', direction=firestore.Query.DESCENDING).limit(10).stream()
            
            for doc in docs:
                r = doc.to_dict()
                total = f"Rp {r.get('total_harga', 0):,.0f}"
                pay_st = (r.get("payment_status") or "unpaid").upper()
                status = r.get("status", "").lower()
                label  = {"pending":"⏳ Pending",
                          "diterima":"✅ Diterima",
                          "ditolak":"❌ Ditolak"}.get(status, status.upper())
                tv.insert("", "end", values=(
                    doc.id[:8],
                    r.get("tanggal", ""),
                    total,
                    label,
                    pay_st
                ), tags=(status,))
        except Exception as e:
            print(f"Error recent_table: {e}")

    def _refresh(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self._build_content(self.scroll_frame)
