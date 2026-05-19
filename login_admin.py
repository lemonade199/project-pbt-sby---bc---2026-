"""
login_admin.py - Halaman Login Admin (Redesign Modern Split Layout)
Aplikasi Business Center SMKN 13 Bandung
Inspirasi: Split panel, dark green palette #051F20 - #DAF1DE
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import messagebox
import hashlib
from PIL import Image, ImageTk, ImageDraw
from db import get_db

# ─── Palet Warna (dari color palette referensi) ───────────────────────
C_DARKEST   = "#051F20"   # Hijau paling gelap
C_DARK      = "#0B2B26"   # Hijau gelap
C_MID       = "#163832"   # Hijau mid
C_MUTED     = "#235347"   # Hijau muted
C_MINT      = "#8EB69B"   # Mint lembut
C_PALE      = "#DAF1DE"   # Pale mint (hampir putih)
WHITE       = "#FFFFFF"
DARK_TEXT   = "#1A1A1A"
GRAY_TEXT   = "#6B7280"
LIGHT_TEXT  = "#9CA3AF"
INPUT_BG    = "#F4FAF6"
INPUT_FOCUS = "#DAF1DE"
BORDER_CLR  = "#C9E8D1"
ERR_CLR     = "#E53935"

PANEL_W     = 340   # lebar panel kiri (ilustrasi)
WIN_W       = 820
WIN_H       = 520


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ─── Helper: Pill Button Canvas ───────────────────────────────────────────────
def _pill_btn(parent, text, command, w=260, h=44, r=22,
              color=C_MID, hover=C_DARK, fg=WHITE,
              font=("Segoe UI", 11, "bold")):
    cv = tk.Canvas(parent, width=w, height=h,
                   bg=parent["bg"], highlightthickness=0, cursor="hand2")

    def _draw(fill):
        cv.delete("all")
        cv.create_arc(0, 0, r*2, h, start=90, extent=180, fill=fill, outline=fill)
        cv.create_arc(w-r*2, 0, w, h, start=270, extent=180, fill=fill, outline=fill)
        cv.create_rectangle(r, 0, w-r, h, fill=fill, outline=fill)
        cv.create_text(w//2, h//2, text=text, fill=fg, font=font, anchor="center")

    _draw(color)
    cv.bind("<Enter>",    lambda e: _draw(hover))
    cv.bind("<Leave>",    lambda e: _draw(color))
    cv.bind("<Button-1>", lambda e: command())
    return cv


# ─── Helper: Rounded Entry (Canvas + Entry overlay) ───────────────────────────
def _rounded_entry(parent, textvariable=None, show=None,
                   w=260, h=42, r=12, bg=INPUT_BG,
                   font=("Segoe UI", 11)):
    frame = tk.Frame(parent, bg=parent["bg"])
    cv = tk.Canvas(frame, width=w, height=h, bg=parent["bg"],
                   highlightthickness=0)
    cv.pack()

    def _draw_bg(fill, border):
        cv.delete("bg")
        cv.create_arc(0, 0, r*2, r*2, start=90, extent=90,
                      fill=fill, outline=border, tags="bg")
        cv.create_arc(w-r*2, 0, w, r*2, start=0, extent=90,
                      fill=fill, outline=border, tags="bg")
        cv.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90,
                      fill=fill, outline=border, tags="bg")
        cv.create_arc(0, h-r*2, r*2, h, start=180, extent=90,
                      fill=fill, outline=border, tags="bg")
        cv.create_rectangle(r, 0, w-r, h, fill=fill, outline=fill, tags="bg")
        cv.create_rectangle(0, r, w, h-r, fill=fill, outline=fill, tags="bg")
        cv.create_line(r, 0, w-r, 0, fill=border, tags="bg")
        cv.create_line(r, h, w-r, h, fill=border, tags="bg")
        cv.create_line(0, r, 0, h-r, fill=border, tags="bg")
        cv.create_line(w, r, w, h-r, fill=border, tags="bg")

    _draw_bg(bg, BORDER_CLR)

    pad = 14
    ent = tk.Entry(frame, textvariable=textvariable,
                   font=font, relief="flat", bd=0,
                   bg=bg, fg=DARK_TEXT,
                   insertbackground=C_MID,
                   highlightthickness=0,
                   width=int((w - pad*2) / 7))
    if show:
        ent.config(show=show)

    ent.place(x=pad, y=(h - ent.winfo_reqheight()) // 2 + 2,
              width=w - pad*2)

    def _focus_in(e):
        _draw_bg(INPUT_FOCUS, C_MINT)
    def _focus_out(e):
        _draw_bg(bg, BORDER_CLR)

    ent.bind("<FocusIn>",  _focus_in)
    ent.bind("<FocusOut>", _focus_out)

    return frame, ent


class LoginAdmin(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master   = master
        self.show_pw  = False
        self._blobs   = []

        self.title("Login Admin — Business Center SMKN 13 Bandung")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(WIN_W, WIN_H)
        self._build_ui()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        left  = tk.Frame(self, bg=C_DARKEST, width=PANEL_W)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(self, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        cv = tk.Canvas(parent, width=PANEL_W, height=WIN_H,
                       bg=C_DARKEST, highlightthickness=0)
        cv.pack(fill="both", expand=True)

        blobs = [
            (PANEL_W//2 - 20, WIN_H//2 - 10, 160, C_DARK),
            (30,  60,  90,  C_MID),
            (PANEL_W - 50, WIN_H - 80, 110, C_MID),
            (60,  WIN_H - 50, 70, C_DARK),
            (PANEL_W - 30, 40, 60, C_MUTED),
            (PANEL_W//2 + 60, 30, 40, C_MUTED),
        ]
        for bx, by, br, bc in blobs:
            cv.create_oval(bx-br, by-br, bx+br, by+br, fill=bc, outline="")

        img_loaded = False
        for fname in ("ilustrasi_login.png", "ilustrasi.png",
                      "assets/ilustrasi_login.png", "assets/ilustrasi.png"):
            fpath = os.path.join(os.path.dirname(__file__), fname)
            if os.path.isfile(fpath):
                try:
                    img = Image.open(fpath).convert("RGBA")
                    img.thumbnail((220, 260), Image.LANCZOS)
                    ph  = ImageTk.PhotoImage(img)
                    self._blobs.append(ph)
                    cx = PANEL_W // 2
                    cy = WIN_H  // 2 - 20
                    cv.create_image(cx, cy, image=ph, anchor="center")
                    img_loaded = True
                    break
                except Exception:
                    pass

        if not img_loaded:
            cv.create_text(PANEL_W//2, WIN_H//2 - 50,
                           text="🏫", font=("Segoe UI Emoji", 52),
                           fill=C_MINT, anchor="center")
            cv.create_text(PANEL_W//2, WIN_H//2 + 30,
                           text="Business Center",
                           font=("Segoe UI", 14, "bold"),
                           fill=WHITE, anchor="center")
            cv.create_text(PANEL_W//2, WIN_H//2 + 56,
                           text="SMKN 13 Bandung",
                           font=("Segoe UI", 10),
                           fill=C_MINT, anchor="center")

        dots = [(30, 200), (PANEL_W-25, 150), (PANEL_W-40, WIN_H-140),
                (20, WIN_H-100), (PANEL_W//2-80, 30), (PANEL_W//2+70, WIN_H-40)]
        for dx, dy in dots:
            r = 6
            cv.create_oval(dx-r, dy-r, dx+r, dy+r, fill=C_MINT, outline="")

        cv.create_text(PANEL_W//2, WIN_H - 18,
                       text="© 2026 BC SMKN 13 Bandung",
                       font=("Segoe UI", 8),
                       fill=C_MUTED, anchor="center")

    def _build_right(self, parent):
        wrap = tk.Frame(parent, bg=WHITE)
        wrap.place(relx=.5, rely=.5, anchor="center")

        tk.Label(wrap, text="B U S I N E S S   C E N T E R",
                 font=("Segoe UI", 8, "bold"),
                 bg=WHITE, fg=C_MINT).pack(anchor="w", pady=(0, 2))

        tk.Label(wrap, text="Selamat Datang,",
                 font=("Segoe UI", 22, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(anchor="w")
        tk.Label(wrap, text="Silakan login untuk melanjutkan.",
                 font=("Segoe UI", 10),
                 bg=WHITE, fg=GRAY_TEXT).pack(anchor="w", pady=(2, 28))

        # Username
        tk.Label(wrap, text="Username",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(anchor="w", pady=(0, 6))

        self.var_user = tk.StringVar()
        f_user, self.entry_user = _rounded_entry(
            wrap, textvariable=self.var_user, w=280, h=44)
        f_user.pack(anchor="w", pady=(0, 16))
        self.entry_user.focus()

        # Password
        tk.Label(wrap, text="Password",
                 font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(anchor="w", pady=(0, 6))

        self.var_pass = tk.StringVar()
        f_pass, self.entry_pass = _rounded_entry(
            wrap, textvariable=self.var_pass, show="●", w=280, h=44)
        f_pass.pack(anchor="w", pady=(0, 6))

        # Toggle show password
        toggle_row = tk.Frame(wrap, bg=WHITE)
        toggle_row.pack(anchor="w", pady=(0, 24))
        self.var_show = tk.IntVar()
        tk.Checkbutton(toggle_row, text="Tampilkan password",
                       variable=self.var_show,
                       font=("Segoe UI", 8), bg=WHITE,
                       fg=GRAY_TEXT, activebackground=WHITE,
                       selectcolor=WHITE, cursor="hand2",
                       command=self._toggle_pw).pack(side="left")

        # Tombol Login
        btn = _pill_btn(wrap, text="Masuk  →", command=self._login,
                        w=280, h=46, r=23,
                        color=C_MID, hover=C_DARK)
        btn.pack(anchor="w")

        # Kembali
        back_f = tk.Frame(wrap, bg=WHITE)
        back_f.pack(anchor="w", pady=(16, 0))
        tk.Label(back_f, text="←", font=("Segoe UI", 10),
                 bg=WHITE, fg=C_MINT).pack(side="left")
        back_btn = tk.Label(back_f, text=" Kembali ke Menu Utama",
                            font=("Segoe UI", 9),
                            bg=WHITE, fg=C_MUTED, cursor="hand2")
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self._kembali())
        back_btn.bind("<Enter>",    lambda e: back_btn.config(fg=C_MID))
        back_btn.bind("<Leave>",    lambda e: back_btn.config(fg=C_MUTED))

        # Label error
        self.lbl_err = tk.Label(wrap, text="",
                                font=("Segoe UI", 9),
                                bg=WHITE, fg=ERR_CLR)
        self.lbl_err.pack(anchor="w", pady=(10, 0))

        # Bind Enter
        self.bind("<Return>", lambda e: self._login())

    def _kembali(self):
        self.destroy()
        self.master.deiconify()

    def _toggle_pw(self):
        self.show_pw = not self.show_pw
        self.entry_pass.config(show="" if self.show_pw else "●")

    def _login(self):
        username = self.var_user.get().strip()
        password = self.var_pass.get().strip()
        self.lbl_err.config(text="")

        if not username or not password:
            self.lbl_err.config(text="⚠️  Username dan password harus diisi.")
            return

        try:
            db = get_db()
            hashed_pw = hash_password(password)
            
            docs = db.collection('users')\
                     .where('username', '==', username)\
                     .where('password', '==', hashed_pw)\
                     .limit(1).get()
            
            if docs:
                admin_data = docs[0].to_dict()
                admin_data['id_user'] = docs[0].id
                
                self.destroy()
                from admin.dashboard import AdminDashboard
                dash = AdminDashboard(self.master, admin_data)
                dash.protocol("WM_DELETE_WINDOW",
                              lambda: self._on_dashboard_close(dash))
            else:
                self.lbl_err.config(text="❌  Username atau password salah.")
                self.entry_pass.delete(0, "end")
                self.entry_pass.focus()
                
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

    def _on_dashboard_close(self, dash):
        dash.destroy()
        self.master.deiconify()
