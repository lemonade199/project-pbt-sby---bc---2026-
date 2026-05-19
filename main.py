"""
main.py - Entry Point Aplikasi Business Center SMKN 13 Bandung
Premium Modern Redesign
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Tambahkan path project ke sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ─── Palet Warna ──────────────────────────────────────────────────────────────
C_DARKEST   = "#051F20"
C_DARK      = "#0B2B26"
C_MID       = "#163832"
C_MUTED     = "#235347"
C_MINT      = "#8EB69B"
C_PALE      = "#DAF1DE"

WHITE       = "#FFFFFF"
BG_MAIN     = "#F4FAF6"
BORDER_CLR  = "#D9E9DE"

DARK_TEXT   = "#1A2E22"
GRAY_TEXT   = "#5C7A68"
LIGHT_TEXT  = "#9DB8A8"

ADMIN_CLR   = "#1A3A5C"
ADMIN_HVR   = "#102640"
ADMIN_PALE  = "#EEF2FF"


# ─── Helper: Pill Button ──────────────────────────────────────────────────────
def _pill(parent, text, command, w=190, h=42, r=21,
          color=C_MID, hover=C_DARK, fg=WHITE,
          font=("Segoe UI", 10, "bold")):

    cv = tk.Canvas(
        parent,
        width=w,
        height=h,
        bg=parent["bg"],
        highlightthickness=0,
        cursor="hand2"
    )

    def _draw(fill):
        cv.delete("all")
        cv.create_arc(0, 0, r * 2, h, start=90, extent=180, fill=fill, outline=fill)
        cv.create_arc(w - r * 2, 0, w, h, start=270, extent=180, fill=fill, outline=fill)
        cv.create_rectangle(r, 0, w - r, h, fill=fill, outline=fill)
        cv.create_text(w // 2, h // 2, text=text, fill=fg, font=font)

    _draw(color)

    cv.bind("<Enter>", lambda e: _draw(hover))
    cv.bind("<Leave>", lambda e: _draw(color))
    cv.bind("<Button-1>", lambda e: command())

    return cv


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Business Center — SMKN 13 Bandung")
        self.geometry("760x560")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(760, 560)
        self._build_ui()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_DARKEST, height=105)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Accent line
        tk.Frame(self, bg=C_MINT, height=4).pack(fill="x")

        inner = tk.Frame(hdr, bg=C_DARKEST)
        inner.pack(expand=True, fill="both", padx=34)

        # ICON
        tk.Label(
            inner,
            text="🏫",
            font=("Segoe UI Emoji", 30),
            bg=C_DARKEST
        ).pack(side="left", padx=(0, 18))

        # TEXT
        txt = tk.Frame(inner, bg=C_DARKEST)
        txt.pack(side="left")

        tk.Label(
            txt,
            text="BUSINESS CENTER",
            font=("Segoe UI", 21, "bold"),
            bg=C_DARKEST,
            fg=WHITE
        ).pack(anchor="w")

        tk.Label(
            txt,
            text="SMKN 13 Bandung  •  Sistem Manajemen Kasir Modern",
            font=("Segoe UI", 9),
            bg=C_DARKEST,
            fg=C_MINT
        ).pack(anchor="w", pady=(4, 0))

    def _build_body(self):
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(expand=True, fill="both")

        container = tk.Frame(body, bg=BG_MAIN)
        container.pack(expand=True)

        # ── Welcome Card ──────────────────────────────────────────────────────
        welcome = tk.Frame(
            container,
            bg=WHITE,
            highlightbackground=BORDER_CLR,
            highlightthickness=1
        )
        welcome.pack(fill="x", padx=34, pady=(32, 26))

        welcome_inner = tk.Frame(welcome, bg=WHITE)
        welcome_inner.pack(fill="both", padx=28, pady=24)

        tk.Label(
            welcome_inner,
            text="Selamat Datang 👋",
            font=("Segoe UI", 18, "bold"),
            bg=WHITE,
            fg=DARK_TEXT
        ).pack(anchor="w")

        tk.Label(
            welcome_inner,
            text="Pilih mode yang ingin digunakan untuk memulai sistem Business Center.",
            font=("Segoe UI", 10),
            bg=WHITE,
            fg=GRAY_TEXT
        ).pack(anchor="w", pady=(6, 0))

        # ── Card Container ────────────────────────────────────────────────────
        cards = tk.Frame(container, bg=BG_MAIN)
        cards.pack(fill="both", padx=34)

        self._make_card(
            parent=cards,
            col=0,
            icon="🛍️",
            icon_bg="#EAF7EF",
            title="Transaksi",
            subtitle="Digunakan untuk pembelian\nproduk dan transaksi kasir.",
            btn_text="Masuk Transaksi",
            btn_color=C_MID,
            btn_hover=C_DARK,
            card_hover="#F4FCF7",
            border_act=C_MINT,
            command=self._open_transaksi
        )

        self._make_card(
            parent=cards,
            col=1,
            icon="🔒",
            icon_bg=ADMIN_PALE,
            title="Admin Panel",
            subtitle="Kelola barang, stok,\nserta konfirmasi pesanan.",
            btn_text="Login Admin",
            btn_color=ADMIN_CLR,
            btn_hover=ADMIN_HVR,
            card_hover="#F5F7FF",
            border_act="#7B9ED9",
            command=self._open_admin_login
        )

        cards.grid_columnconfigure(0, weight=1, uniform="card")
        cards.grid_columnconfigure(1, weight=1, uniform="card")

    def _make_card(self, parent, col, icon, icon_bg, title, subtitle,
                   btn_text, btn_color, btn_hover,
                   card_hover, border_act, command):

        NORMAL_BG = WHITE

        card = tk.Frame(
            parent,
            bg=NORMAL_BG,
            bd=0,
            highlightbackground=BORDER_CLR,
            highlightthickness=1,
            cursor="hand2"
        )
        card.grid(row=0, column=col, padx=10, sticky="nsew")

        # Accent line
        accent = tk.Frame(card, bg=BORDER_CLR, height=4)
        accent.pack(fill="x")

        inner = tk.Frame(card, bg=NORMAL_BG)
        inner.pack(expand=True, fill="both", padx=26, pady=26)

        # ICON
        icon_box = tk.Frame(inner, bg=icon_bg, width=64, height=64)
        icon_box.pack(anchor="center", pady=(0, 18))
        icon_box.pack_propagate(False)

        tk.Label(
            icon_box,
            text=icon,
            font=("Segoe UI Emoji", 28),
            bg=icon_bg
        ).pack(expand=True)

        # TITLE
        tk.Label(
            inner,
            text=title,
            font=("Segoe UI", 14, "bold"),
            bg=NORMAL_BG,
            fg=DARK_TEXT
        ).pack(anchor="center")

        # SUBTITLE
        tk.Label(
            inner,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=NORMAL_BG,
            fg=GRAY_TEXT,
            justify="center"
        ).pack(anchor="center", pady=(8, 24))

        # BUTTON
        btn_cv = _pill(
            inner,
            text=btn_text,
            command=command,
            w=190,
            h=42,
            r=21,
            color=btn_color,
            hover=btn_hover,
            font=("Segoe UI", 9, "bold")
        )
        btn_cv.pack(anchor="center")

        # HOVER EFFECT
        def _enter(e):
            card.config(bg=card_hover, highlightbackground=border_act)
            accent.config(bg=btn_color)
            inner.config(bg=card_hover)
            btn_cv.config(bg=card_hover)

            for w in inner.winfo_children():
                try:
                    if w != icon_box:
                        w.config(bg=card_hover)
                except:
                    pass

        def _leave(e):
            card.config(bg=NORMAL_BG, highlightbackground=BORDER_CLR)
            accent.config(bg=BORDER_CLR)
            inner.config(bg=NORMAL_BG)
            btn_cv.config(bg=NORMAL_BG)

            for w in inner.winfo_children():
                try:
                    if w != icon_box:
                        w.config(bg=NORMAL_BG)
                except:
                    pass

        for widget in [card, inner]:
            widget.bind("<Enter>", _enter)
            widget.bind("<Leave>", _leave)

    def _build_footer(self):
        tk.Frame(self, bg=BORDER_CLR, height=1).pack(fill="x", side="bottom")

        foot = tk.Frame(self, bg=BG_MAIN)
        foot.pack(fill="x", side="bottom")

        tk.Label(
            foot,
            text="© 2026 Business Center SMKN 13 Bandung — All rights reserved",
            font=("Segoe UI", 8),
            bg=BG_MAIN,
            fg=LIGHT_TEXT
        ).pack(pady=11)

    def _open_transaksi(self):
        try:
            from user.transaksi import TransaksiWindow
            self.withdraw()
            win = TransaksiWindow(self)
            win.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(win))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_admin_login(self):
        try:
            from login_admin import LoginAdmin
            self.withdraw()
            win = LoginAdmin(self)
            win.protocol("WM_DELETE_WINDOW", lambda: self._on_child_close(win))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_child_close(self, win):
        win.destroy()
        self.deiconify()


if __name__ == "__main__":
    # ── Verifikasi Koneksi Firebase / Firestore ───────────────────────────────
    try:
        from db import get_db
        db = get_db()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Koneksi Firebase Gagal",
            f"{e}\n\nPastikan file konfigurasi Firebase Anda (serviceAccountKey.json) diletakkan dengan benar di root project."
        )
        sys.exit(1)

    # ── Jalankan Flask webhook server Midtrans di background ─────────────────
    try:
        from midtrans_webhook import ensure_webhook_running
        ensure_webhook_running()
    except Exception as _we:
        print(f"[Warning] Webhook Midtrans tidak bisa dijalankan: {_we}")

    app = MainApp()
    app.mainloop()
