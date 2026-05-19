"""
user/transaksi.py - Halaman Transaksi User (Full Redesign Premium)
Aplikasi Business Center SMKN 13 Bandung
Palet: Dark Green #051F20 → Pale Mint #DAF1DE
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import webbrowser
import threading
import requests
from io import BytesIO
from db import get_db, get_drive_service, DRIVE_FOLDER_ID, IMAGES_DIR, API_URL

# ─── Palet Warna (seragam seluruh aplikasi) ───────────────────
C_DARKEST   = "#051F20"   # Sidebar / header gelap
C_DARK      = "#0B2B26"   # Header hover / elemen gelap
C_MID       = "#163832"   # Tombol utama
C_MUTED     = "#235347"   # Aksen sekunder
C_MINT      = "#8EB69B"   # Border, ikon, teks sekunder hijau
C_PALE      = "#DAF1DE"   # Background input focus, badge, highlight
WHITE       = "#FFFFFF"
BG_MAIN     = "#F4FAF6"   # Background utama sedikit kehijauan
BG_CARD     = "#FFFFFF"
BG_CARD_HVR = "#F0FAF4"
BORDER_CLR  = "#D1E8D8"
DARK_TEXT   = "#1A2E22"   # Teks utama
GRAY_TEXT   = "#5C7A68"   # Teks sekunder
LIGHT_TEXT  = "#9DB8A8"   # Teks hint
STOCK_OK    = "#163832"
STOCK_LOW   = "#C07A00"
STOCK_OUT   = "#B83232"
REMOVE_CLR  = "#B83232"
SIDEBAR_W   = 310
CARD_IMG_SZ = (84, 84)
COLS        = 3


# ─── Helper: load foto produk ─────────────────────────────────────────────────
def _load_card_image(foto: str, stok: int):
    """Muat gambar produk dari local atau GDrive. Return None jika tidak ada."""
    if not foto: return None
    try:
        clean_name = "".join([c for c in str(foto) if c.isalnum() or c in "._- "])
        local_filename = f"{clean_name}.png" if not clean_name.endswith(".png") else clean_name
        local_path = os.path.join(IMAGES_DIR, local_filename)

        # 1. Coba dari lokal dulu
        if os.path.isfile(local_path):
            try:
                with Image.open(local_path) as img:
                    img_ready = img.convert("RGBA")
                    return _process_card_image(img_ready, stok)
            except:
                pass
        
        # 2. Jika tidak ada di lokal, coba dari Google Drive
        try:
            service = get_drive_service()
            if service:
                query = f"name = '{foto}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
                results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                items = results.get('files', [])
                
                file_id = None
                if not items:
                    if "." not in str(foto) and len(str(foto)) >= 20:
                        file_id = foto
                else:
                    file_id = items[0]['id']

                if file_id:
                    request = service.files().get_media(fileId=file_id)
                    img_data = request.execute()
                    with Image.open(BytesIO(img_data)) as img:
                        img_ready = img.convert("RGBA")
                        try:
                            img_ready.save(local_path)
                        except: pass
                        return _process_card_image(img_ready, stok)

        except Exception as e:
            print(f"Error fetching image from GDrive: {e}")
        
        # 3. Default jika gagal download (stok habis)
        if stok <= 0:
            with Image.new("RGBA", CARD_IMG_SZ, (255, 255, 255, 0)) as img:
                return _process_card_image(img, stok)
            
        return None
    except Exception:
        return None


def _process_card_image(img, stok):
    img_thumb = img.copy()
    img_thumb.thumbnail(CARD_IMG_SZ, Image.LANCZOS)
    
    canvas = Image.new("RGBA", CARD_IMG_SZ, (255, 255, 255, 0))
    offset = ((CARD_IMG_SZ[0] - img_thumb.width)  // 2,
              (CARD_IMG_SZ[1] - img_thumb.height) // 2)
    canvas.paste(img_thumb, offset, img_thumb)

    if stok <= 0:
        d = ImageDraw.Draw(canvas)
        w, h = CARD_IMG_SZ
        d.line((8,8,w-8,h-8), fill=(184,50,50,210), width=5)
        d.line((8,h-8,w-8,8), fill=(184,50,50,210), width=5)

    return ImageTk.PhotoImage(canvas)


# ─── Helper: pill button Canvas ───────────────────────────────────────────────
def _pill(parent, text, command, w=120, h=32, r=16,
          color=C_MID, hover=C_DARK, fg=WHITE,
          font=("Segoe UI", 8, "bold")):
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


# ─── Helper: Rounded Entry (untuk checkout) ──────────────────────────────────
def _rounded_entry(parent, textvariable=None, w=220, h=38, r=10, bg="#F4FAF6",
                   font=("Segoe UI", 10)):
    frame = tk.Frame(parent, bg=parent["bg"])
    cv = tk.Canvas(frame, width=w, height=h, bg=parent["bg"],
                   highlightthickness=0)
    cv.pack()

    def _draw_bg(fill, border):
        cv.delete("bg")
        cv.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=fill, outline=border, tags="bg")
        cv.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=fill, outline=border, tags="bg")
        cv.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=fill, outline=border, tags="bg")
        cv.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=fill, outline=border, tags="bg")
        cv.create_rectangle(r, 0, w-r, h, fill=fill, outline=fill, tags="bg")
        cv.create_rectangle(0, r, w, h-r, fill=fill, outline=fill, tags="bg")
        cv.create_line(r, 0, w-r, 0, fill=border, tags="bg")
        cv.create_line(r, h, w-r, h, fill=border, tags="bg")
        cv.create_line(0, r, 0, h-r, fill=border, tags="bg")
        cv.create_line(w, r, w, h-r, fill=border, tags="bg")

    _draw_bg(bg, BORDER_CLR)

    pad = 12
    ent = tk.Entry(frame, textvariable=textvariable,
                   font=font, relief="flat", bd=0,
                   bg=bg, fg=DARK_TEXT,
                   insertbackground=C_MID,
                   highlightthickness=0,
                   width=int((w - pad*2) / 7))

    ent.place(x=pad, y=(h - ent.winfo_reqheight()) // 2 + 1,
              width=w - pad*2)

    def _focus_in(e):
        _draw_bg(C_PALE, C_MINT)
    def _focus_out(e):
        _draw_bg(bg, BORDER_CLR)

    ent.bind("<FocusIn>",  _focus_in)
    ent.bind("<FocusOut>", _focus_out)

    return frame, ent


class TransaksiWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master            = master
        self.keranjang         = {}
        self.barang_data       = []
        self._card_imgs        = {}
        self._checkout_enabled = False

        self.title("Transaksi — Business Center SMKN 13 Bandung")
        self.geometry("1200x700")
        self.minsize(960, 600)
        self.configure(bg=BG_MAIN)
        self._center(1200, 700)
        self._build_styles()
        self._build_ui()
        self._load_barang()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_styles(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Thin.Vertical.TScrollbar",
                    gripcount=0, background=C_MINT,
                    troughcolor=BG_MAIN, borderwidth=0,
                    arrowsize=0, width=5)
        s.map("Thin.Vertical.TScrollbar",
              background=[("active", C_MUTED)])
        s.configure("Cart.Treeview",
                    font=("Segoe UI", 9), rowheight=34,
                    background=WHITE, fieldbackground=WHITE,
                    foreground=DARK_TEXT, borderwidth=0)
        s.configure("Cart.Treeview.Heading",
                    font=("Segoe UI", 8, "bold"),
                    background=BG_MAIN, foreground=GRAY_TEXT,
                    relief="flat", borderwidth=0)
        s.map("Cart.Treeview",
              background=[("selected", C_PALE)],
              foreground=[("selected", C_DARKEST)])

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True)
        self._build_catalog(body)
        self._build_sidebar(body)

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_DARKEST, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left_f = tk.Frame(hdr, bg=C_DARKEST)
        left_f.pack(side="left", fill="y", padx=20)
        tk.Label(left_f, text="🏫", font=("Segoe UI Emoji", 18),
                 bg=C_DARKEST).pack(side="left", padx=(0,10))
        title_col = tk.Frame(left_f, bg=C_DARKEST)
        title_col.pack(side="left", fill="y", pady=10)
        tk.Label(title_col,
                 text="Business Center  SMKN 13 Bandung",
                 font=("Segoe UI", 12, "bold"),
                 bg=C_DARKEST, fg=WHITE, anchor="w").pack(anchor="w")
        tk.Label(title_col, text="Halaman Transaksi Pelanggan",
                 font=("Segoe UI", 8),
                 bg=C_DARKEST, fg=C_MINT, anchor="w").pack(anchor="w")

        back = _pill(hdr, text="← Kembali", command=self._kembali,
                     w=110, h=34, r=17,
                     color=C_MUTED, hover=C_MID, fg=WHITE,
                     font=("Segoe UI", 9, "bold"))
        back.pack(side="right", padx=18, pady=14)
        back.config(bg=C_DARKEST)

    def _kembali(self):
        if hasattr(self.master, "_on_child_close"):
            self.master._on_child_close(self)
        else:
            self.destroy()
            self.master.deiconify()

    def _build_catalog(self, body):
        left = tk.Frame(body, bg=BG_MAIN)
        left.pack(side="left", fill="both", expand=True,
                  padx=(16,8), pady=14)

        # Search + Refresh
        sr = tk.Frame(left, bg=BG_MAIN)
        sr.pack(fill="x", pady=(0,12))

        sb_outer = tk.Frame(sr, bg=C_MINT, padx=1, pady=1)
        sb_outer.pack(side="left")
        sb_inner = tk.Frame(sb_outer, bg=WHITE)
        sb_inner.pack()
        tk.Label(sb_inner, text="🔍", font=("Segoe UI Emoji", 10),
                 bg=WHITE, fg=C_MINT).pack(side="left", padx=(10,4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_barang())
        ent = tk.Entry(sb_inner, textvariable=self.search_var,
                       font=("Segoe UI", 10), width=28,
                       relief="flat", bg=WHITE,
                       fg=DARK_TEXT, insertbackground=C_MID)
        ent.pack(side="left", ipady=9, padx=(0,10))
        ent.bind("<FocusIn>",  lambda e: sb_outer.config(bg=C_MID))
        ent.bind("<FocusOut>", lambda e: sb_outer.config(bg=C_MINT))

        btn_ref = _pill(sr, text="↻  Refresh", command=self._load_barang,
                        w=96, h=36, r=18,
                        color=BG_MAIN, hover=C_PALE, fg=C_MID,
                        font=("Segoe UI", 9, "bold"))
        btn_ref.pack(side="left", padx=10)
        btn_ref.config(bg=BG_MAIN)

        # Label section
        lrow = tk.Frame(left, bg=BG_MAIN)
        lrow.pack(fill="x", pady=(0,8))
        tk.Frame(lrow, bg=C_MID, width=4, height=20).pack(side="left")
        tk.Label(lrow, text="  Daftar Barang",
                 font=("Segoe UI", 10, "bold"),
                 bg=BG_MAIN, fg=DARK_TEXT).pack(side="left")
        self.lbl_prod_count = tk.Label(lrow, text="",
                                       font=("Segoe UI", 9),
                                       bg=BG_MAIN, fg=GRAY_TEXT)
        self.lbl_prod_count.pack(side="left", padx=6)

        # Grid scrollable
        wrap = tk.Frame(left, bg=BG_MAIN)
        wrap.pack(fill="both", expand=True)
        self.cat_canvas = tk.Canvas(wrap, bg=BG_MAIN, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical",
                            command=self.cat_canvas.yview,
                            style="Thin.Vertical.TScrollbar")
        self.cat_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.cat_canvas.pack(side="left", fill="both", expand=True)
        self.cat_frame = tk.Frame(self.cat_canvas, bg=BG_MAIN)
        self.cat_win   = self.cat_canvas.create_window(
            (0,0), window=self.cat_frame, anchor="nw")
        self.cat_frame.bind("<Configure>", lambda e:
            self.cat_canvas.configure(
                scrollregion=self.cat_canvas.bbox("all")))
        self.cat_canvas.bind("<Configure>", lambda e:
            self.cat_canvas.itemconfig(self.cat_win, width=e.width))
        self.cat_canvas.bind_all("<MouseWheel>",
            lambda e: self.cat_canvas.yview_scroll(
                int(-1*(e.delta/120)), "units"))

    def _build_sidebar(self, body):
        side = tk.Frame(body, bg=WHITE, width=SIDEBAR_W)
        side.pack(side="right", fill="y", padx=(8,14), pady=14)
        side.pack_propagate(False)

        # Header sidebar
        s_hdr = tk.Frame(side, bg=C_DARKEST, height=56)
        s_hdr.pack(fill="x")
        s_hdr.pack_propagate(False)
        h_inner = tk.Frame(s_hdr, bg=C_DARKEST)
        h_inner.pack(fill="both", expand=True, padx=16)
        tk.Label(h_inner, text="🛒  Keranjang Belanja",
                 font=("Segoe UI", 11, "bold"),
                 bg=C_DARKEST, fg=WHITE).pack(side="left", pady=16)
        self.badge = tk.Label(h_inner, text="",
                              font=("Segoe UI", 8, "bold"),
                              bg=STOCK_OUT, fg=WHITE,
                              padx=7, pady=2)
        self.badge.pack(side="right", pady=18)

        # Footer sidebar (Aksi, Total, Checkout ditaruh paling bawah)
        footer = tk.Frame(side, bg=WHITE)
        footer.pack(side="bottom", fill="x")

        # Treeview
        tree_wrap = tk.Frame(side, bg=WHITE)
        tree_wrap.pack(side="top", fill="both", expand=True)
        cols = ("Barang", "Qty", "Subtotal")
        self.cart_tree = ttk.Treeview(
            tree_wrap, columns=cols, show="headings",
            style="Cart.Treeview", selectmode="browse")
        self.cart_tree.heading("Barang",   text="Nama Barang")
        self.cart_tree.heading("Qty",      text="Qty")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.column("Barang",   width=130, anchor="w",  stretch=True)
        self.cart_tree.column("Qty",      width=34,  anchor="center", stretch=False)
        self.cart_tree.column("Subtotal", width=96,  anchor="e",  stretch=False)
        tsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                            command=self.cart_tree.yview,
                            style="Thin.Vertical.TScrollbar")
        self.cart_tree.configure(yscrollcommand=tsb.set)
        tsb.pack(side="right", fill="y")
        self.cart_tree.pack(fill="both", expand=True)

        tk.Frame(footer, bg=BORDER_CLR, height=1).pack(fill="x")

        # Aksi
        act = tk.Frame(footer, bg=WHITE)
        act.pack(fill="x")
        tk.Button(act, text="❌  Hapus Item",
                  font=("Segoe UI", 8, "bold"), bg=WHITE, fg=REMOVE_CLR,
                  relief="flat", pady=8, cursor="hand2",
                  activebackground="#FFF0F0",
                  command=self._hapus_item).pack(side="left", fill="x", expand=True)
        tk.Frame(act, bg=BORDER_CLR, width=1).pack(side="left", fill="y")
        tk.Button(act, text="🗑  Kosongkan",
                  font=("Segoe UI", 8, "bold"), bg=WHITE, fg=GRAY_TEXT,
                  relief="flat", pady=8, cursor="hand2",
                  activebackground=BG_MAIN,
                  command=self._kosongkan).pack(side="left", fill="x", expand=True)

        tk.Frame(footer, bg=BORDER_CLR, height=1).pack(fill="x")

        # Total
        tot_f = tk.Frame(footer, bg=WHITE)
        tot_f.pack(fill="x", padx=16, pady=12)
        top = tk.Frame(tot_f, bg=WHITE)
        top.pack(fill="x")
        tk.Label(top, text="Total Belanja",
                 font=("Segoe UI", 9),
                 bg=WHITE, fg=GRAY_TEXT).pack(side="left")
        self.lbl_item_count = tk.Label(top, text="0 item",
                                       font=("Segoe UI", 8),
                                       bg=WHITE, fg=LIGHT_TEXT)
        self.lbl_item_count.pack(side="right")
        self.lbl_total = tk.Label(tot_f, text="Rp 0",
                                   font=("Segoe UI", 22, "bold"),
                                   bg=WHITE, fg=C_MID)
        self.lbl_total.pack(anchor="e", pady=(4,0))

        # Notif
        self.lbl_notif = tk.Label(footer, text="",
                                   font=("Segoe UI", 8),
                                   bg=WHITE, fg=STOCK_OK,
                                   wraplength=270, justify="center")
        self.lbl_notif.pack(fill="x", padx=10, pady=(0,4))

        # Checkout canvas button
        self.checkout_cv = tk.Canvas(footer, width=SIDEBAR_W, height=52,
                                      bg=WHITE, highlightthickness=0)
        self.checkout_cv.pack(fill="x")
        self._draw_checkout(False)
        self.checkout_cv.bind("<Button-1>", lambda e: self._checkout())

    def _draw_checkout(self, enabled: bool):
        cv   = self.checkout_cv
        w, h = SIDEBAR_W, 52
        fill = C_MID if enabled else C_MINT
        txt  = "Konfirmasi Pemesanan" if enabled else "Keranjang Kosong"
        cv.delete("all")
        cv.create_rectangle(0, 0, w, h, fill=fill, outline=fill)
        cv.create_text(w//2, h//2, text=txt,
                       fill=WHITE, font=("Segoe UI", 12, "bold"),
                       anchor="center")
        cv.config(cursor="hand2" if enabled else "arrow")
        self._checkout_enabled = enabled
        if enabled:
            cv.bind("<Enter>", lambda e: (
                cv.delete("all"),
                cv.create_rectangle(0,0,w,h,fill=C_DARK,outline=C_DARK),
                cv.create_text(w//2,h//2,text=txt,fill=WHITE,
                               font=("Segoe UI",12,"bold"),anchor="center")))
            cv.bind("<Leave>", lambda e: self._draw_checkout(True))
        else:
            cv.unbind("<Enter>")
            cv.unbind("<Leave>")

    def _load_barang(self):
        try:
            db = get_db()
            docs = db.collection('barang').stream()
            self.barang_data = []
            for doc in docs:
                b = doc.to_dict()
                b["id_barang"] = doc.id
                self.barang_data.append(b)
            self.barang_data.sort(key=lambda x: x.get("nama_barang", "").lower())
        except Exception as e:
            messagebox.showerror("Error DB", str(e), parent=self)
            self.barang_data = []
        self.search_var.set("")
        self._render_katalog(self.barang_data)

    def _filter_barang(self):
        kw = self.search_var.get().lower()
        self._render_katalog([b for b in self.barang_data if kw in b["nama_barang"].lower()])

    def _render_katalog(self, data):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self._card_imgs.clear()
        self.lbl_prod_count.config(text=f"({len(data)} produk)" if data else "")
        
        for idx, item in enumerate(data):
            try:
                r, c = divmod(idx, COLS)
                self._make_card(item, r, c)
            except Exception as e:
                print(f"Error rendering item {item.get('id_barang')}: {e}")
                continue
        for c in range(COLS):
            self.cat_frame.grid_columnconfigure(c, weight=1, uniform="col")

        if not data:
            tk.Label(self.cat_frame, text="Tidak ada produk ditemukan.",
                     font=("Segoe UI", 11), bg=BG_MAIN, fg=LIGHT_TEXT).grid(
                         column=0, row=0, columnspan=COLS, padx=20, pady=60)

    def _make_card(self, item, row, col):
        id_b  = item["id_barang"]
        nama  = item["nama_barang"]
        try:
            harga = float(item["harga_barang"] or 0)
        except (ValueError, TypeError):
            harga = 0
        stok  = item["stok"]
        foto  = item.get("foto")
        oos   = stok <= 0

        card = tk.Frame(self.cat_frame, bg=BG_CARD,
                        highlightbackground=BORDER_CLR, highlightthickness=1,
                        width=208, height=222)
        card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
        card.pack_propagate(False)
        card.grid_propagate(False)

        # Garis aksen atas
        tk.Frame(card, bg=C_MINT if not oos else "#CCCCCC", height=3).pack(fill="x")

        # Area gambar
        img_area = tk.Frame(card, bg=C_PALE if not oos else "#F0F0F0", width=84, height=84)
        img_area.pack(pady=(12,4))
        img_area.pack_propagate(False)

        photo = _load_card_image(foto, stok)
        if photo:
            self._card_imgs[id_b] = photo
            tk.Label(img_area, image=photo, bg=img_area["bg"]).pack(expand=True)
        else:
            if oos:
                cv_ph = tk.Canvas(img_area, width=84, height=84, bg="#F0F0F0", highlightthickness=0)
                cv_ph.pack()
                cv_ph.create_text(42,42,text="📦", font=("Segoe UI Emoji",24), fill="#CCCCCC")
                cv_ph.create_line(10,10,74,74,fill=STOCK_OUT,width=4)
                cv_ph.create_line(10,74,74,10,fill=STOCK_OUT,width=4)
            else:
                tk.Label(img_area, text="📦", font=("Segoe UI Emoji", 28), bg=C_PALE).pack(expand=True)

        # Nama
        tk.Label(card, text=nama, font=("Segoe UI", 9, "bold"),
                 bg=BG_CARD, fg=DARK_TEXT, wraplength=188, justify="center").pack(padx=6)

        # Harga
        tk.Label(card, text=f"Rp {harga:,.0f}", font=("Segoe UI", 11, "bold"),
                 bg=BG_CARD, fg=C_MID).pack(pady=(1,0))

        # Stok
        if stok > 5:
            sc, st = STOCK_OK,  f"● Stok: {stok}"
        elif stok > 0:
            sc, st = STOCK_LOW, f"⚠️ Stok: {stok} (menipis)"
        else:
            sc, st = STOCK_OUT, "❌ Stok Habis"
        tk.Label(card, text=st, font=("Segoe UI", 7, "bold"),
                 bg=BG_CARD, fg=sc).pack()

        # Tombol
        if not oos:
            btn = _pill(card, text="+ Tambah",
                        command=lambda i=item: self._tambah_ke_keranjang(i),
                        w=116, h=30, r=15,
                        color=C_MID, hover=C_DARK)
            btn.pack(pady=(5,10))
            btn.config(bg=BG_CARD)
            card.bind("<Enter>", lambda e, c=card: c.config(bg=BG_CARD_HVR, highlightbackground=C_MINT))
            card.bind("<Leave>", lambda e, c=card: c.config(bg=BG_CARD, highlightbackground=BORDER_CLR))
        else:
            tk.Label(card, text="Tidak Tersedia", font=("Segoe UI", 8),
                     bg=BG_CARD, fg=LIGHT_TEXT).pack(pady=(5,10))

    def _tambah_ke_keranjang(self, item):
        id_b = item["id_barang"]
        try:
            db = get_db()
            doc = db.collection('barang').document(id_b).get()
            stok_db = doc.to_dict().get("stok", 0) if doc.exists else 0
        except Exception:
            stok_db = item.get("stok", 0)

        if id_b in self.keranjang:
            if self.keranjang[id_b]["jumlah"] >= stok_db:
                self._notif(f"Stok \"{item.get('nama_barang', '')}\" tidak mencukupi!", err=True)
                return
            self.keranjang[id_b]["jumlah"] += 1
        else:
            if stok_db <= 0:
                self._notif("Stok habis!", err=True)
                return
            self.keranjang[id_b] = {
                "nama": item.get("nama_barang", ""), "harga": float(item.get("harga_barang", 0)),
                "jumlah": 1, "stok": stok_db
            }
        self._update_cart()
        self._notif(f"✅  \"{item.get('nama_barang', '')}\" ditambahkan.")

    def _hapus_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            self._notif("Pilih item yang ingin dihapus.", err=True)
            return
        id_b = sel[0]
        nama = self.keranjang[id_b]["nama"]
        del self.keranjang[id_b]
        self._update_cart()
        self._notif(f"❌  \"{nama}\" dihapus.")

    def _kosongkan(self):
        if not self.keranjang:
            return
        if messagebox.askyesno("Kosongkan Keranjang", "Yakin ingin mengosongkan keranjang?", parent=self):
            self.keranjang.clear()
            self._update_cart()

    def _update_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        total = 0
        total_qty = 0
        for id_b, d in self.keranjang.items():
            sub        = d["harga"] * d["jumlah"]
            total     += sub
            total_qty += d["jumlah"]
            self.cart_tree.insert("", "end", iid=str(id_b),
                                  values=(d["nama"], d["jumlah"], f"Rp {sub:,.0f}"))
        n = len(self.keranjang)
        self.lbl_total.config(text=f"Rp {total:,.0f}")
        self.lbl_item_count.config(text=f"{n} jenis • {total_qty} item" if n else "0 item")
        self.badge.config(text=f" {n} " if n else "")
        self._draw_checkout(enabled=n > 0)

    def _checkout(self):
        if not self._checkout_enabled or not self.keranjang:
            return

        # Modal Checkout premium
        dialog = tk.Toplevel(self)
        dialog.title("Checkout")
        dialog.geometry("380x320")
        dialog.resizable(False, False)
        dialog.configure(bg=WHITE)
        dialog.transient(self)
        dialog.grab_set()

        # Center
        x = self.winfo_x() + (self.winfo_width()  - 380) // 2
        y = self.winfo_y() + (self.winfo_height() - 320) // 2
        dialog.geometry(f"+{x}+{y}")

        # Top bar accent
        tk.Frame(dialog, bg=C_DARKEST, height=4).pack(fill="x")

        tk.Label(dialog, text="Konfirmasi Pemesanan", font=("Segoe UI", 13, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(pady=(18, 12))

        # Nama Pembeli
        tk.Label(dialog, text="Nama Pembeli", font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=GRAY_TEXT).pack(anchor="w", padx=44, pady=(4,2))
        
        var_nama = tk.StringVar(value="Pembeli Umum")
        f_name, ent_nama = _rounded_entry(dialog, textvariable=var_nama, w=290, h=38)
        f_name.pack(padx=44)
        ent_nama.focus()

        # Metode Pembayaran
        tk.Label(dialog, text="Metode Pembayaran", font=("Segoe UI", 9, "bold"),
                 bg=WHITE, fg=GRAY_TEXT).pack(anchor="w", padx=44, pady=(12,2))
        
        var_me = tk.StringVar(value="qris")
        
        rf = tk.Frame(dialog, bg=WHITE)
        rf.pack(anchor="w", padx=44)
        tk.Radiobutton(rf, text="QRIS", variable=var_me,
                        value="qris", bg=WHITE, activebackground=WHITE,
                        selectcolor=WHITE, font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")
        tk.Radiobutton(rf, text="Pemesanan Langsung", variable=var_me,
                        value="langsung", bg=WHITE, activebackground=WHITE,
                        selectcolor=WHITE, font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")

        def _do_checkout():
            nama = var_nama.get().strip()
            meth = var_me.get().upper()
            if not nama:
                messagebox.showwarning("Peringatan", "Isi nama pembeli!", parent=dialog)
                return
            dialog.destroy()
            self._process_checkout(nama, meth)

        btn_pay = _pill(dialog, text="PROSES SEKARANG  →", command=_do_checkout,
                        w=290, h=40, r=20, color=C_MID, hover=C_DARK,
                        font=("Segoe UI", 10, "bold"))
        btn_pay.config(bg=WHITE)
        btn_pay.pack(pady=22)

    def _process_checkout(self, nama_pembeli: str, method: str):
        total = sum(d["harga"]*d["jumlah"] for d in self.keranjang.values())
        try:
            import datetime
            db = get_db()
            doc_ref = db.collection('pesanan').document()
            
            details = []
            for id_b, d in self.keranjang.items():
                details.append({
                    "id_barang": id_b,
                    "nama_barang": d["nama"],
                    "jumlah": d["jumlah"],
                    "subtotal": d["harga"] * d["jumlah"]
                })
            
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            order_data = {
                "tanggal": now_str,
                "total_harga": total,
                "status": "pending",
                "nama_pembeli": nama_pembeli,
                "payment_status": "unpaid",
                "payment_method": method,
                "detail_pesanan": details
            }
            
            # 3. Jika QRIS (Midtrans), buat token
            if method == "QRIS":
                from midtrans_snap import create_snap_transaction
                items_midtrans = [{"id": str(id_b), "price": int(d["harga"]), "quantity": d["jumlah"], "name": d["nama"][:50]} for id_b, d in self.keranjang.items()]
                snap_token = create_snap_transaction(doc_ref.id, total, nama_pembeli, items_midtrans)
                order_data["snap_token"] = snap_token
                order_data["payment_status"] = "pending"
                
                import webbrowser
                from midtrans_config import WEBHOOK_BASE
                webbrowser.open(f"{WEBHOOK_BASE}/pay/{snap_token}")
            
            doc_ref.set(order_data)
            
            id_pesanan = doc_ref.id
            self.keranjang.clear()
            self._update_cart()
            self._load_barang()

            # 5. Tampilkan window status
            self._show_payment_status(id_pesanan)

        except Exception as e:
            messagebox.showerror("Error Checkout", str(e), parent=self)

    def _show_payment_status(self, id_pesanan):
        """Tampilkan window status pembayaran dan polling DB."""
        win = tk.Toplevel(self)
        win.title("Status Pembayaran")
        win.geometry("400x470")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.transient(self)
        win.grab_set()

        # Center
        x = self.winfo_x() + (self.winfo_width()  - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 470) // 2
        win.geometry(f"+{x}+{y}")

        tk.Frame(win, bg=C_DARKEST, height=4).pack(fill="x")

        tk.Label(win, text="Informasi Pembayaran", font=("Segoe UI", 14, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(pady=(22, 12))

        frame = tk.Frame(win, bg=C_PALE, padx=22, pady=18,
                         highlightbackground=BORDER_CLR, highlightthickness=1)
        frame.pack(fill="x", padx=36)

        lbl_id = tk.Label(frame, text=f"Order ID: #{id_pesanan[:8]}", font=("Segoe UI", 10, "bold"),
                          bg=C_PALE, fg=C_DARKEST, anchor="w")
        lbl_id.pack(anchor="w")

        lbl_meth = tk.Label(frame, text="Metode: -", font=("Segoe UI", 9), bg=C_PALE, fg=GRAY_TEXT)
        lbl_meth.pack(anchor="w", pady=2)

        lbl_status = tk.Label(frame, text="Status: CHECKING...", font=("Segoe UI", 11, "bold"),
                               bg=C_PALE, fg=STOCK_OUT)
        lbl_status.pack(anchor="w", pady=(5, 0))

        lbl_msg = tk.Label(win, text="Mohon tunggu...", font=("Segoe UI", 9),
                            bg=WHITE, fg=GRAY_TEXT, wraplength=320, justify="center")
        lbl_msg.pack(pady=18)

        # Tombol aksi placeholder (kita akan pack/forget dinamis)
        self.btn_action_frame = tk.Frame(win, bg=WHITE)
        self.btn_action_frame.pack(pady=4)

        btn_change = tk.Button(win, text="🔄 Ganti Metode Pembayaran", font=("Segoe UI", 9, "bold"),
                                bg=WHITE, fg=C_MUTED, relief="flat", cursor="hand2",
                                activebackground=BG_MAIN, activeforeground=C_MID)
        btn_change.pack(pady=10)

        polling = [True]

        def _get_status():
            if not polling[0] or not win.winfo_exists():
                return
            try:
                db = get_db()
                doc = db.collection('pesanan').document(id_pesanan).get()
                if not doc.exists:
                    return
                r = doc.to_dict()
                st = r.get("payment_status", "unpaid")
                me = (r.get("payment_method") or "Belum dipilih").upper()
                tk_snap = r.get("snap_token", "")

                lbl_meth.config(text=f"Metode: {me}")
                lbl_status.config(text=f"Status: {st.replace('_',' ').upper()}")

                # Warna status
                colors = {
                    "paid": STOCK_OK, 
                    "pending": "#1565C0", 
                    "waiting_confirmation": STOCK_LOW,
                    "rejected": STOCK_OUT,
                    "failed": STOCK_OUT,
                    "expired": GRAY_TEXT,
                    "unpaid": STOCK_OUT
                }
                lbl_status.config(fg=colors.get(st, STOCK_OUT))

                # Render button dynamically
                for w in self.btn_action_frame.winfo_children():
                    w.destroy()

                msg = "Mohon tunggu konfirmasi dari sistem."
                if st == "paid":
                    msg = "✅ Pembayaran Berhasil!\nPesanan Anda sedang diproses oleh admin."
                    btn_change.pack_forget()
                    polling[0] = False
                elif st == "waiting_confirmation":
                    msg = "🕒 Menunggu konfirmasi admin untuk pemesanan langsung.\nSilakan bayar di kasir."
                elif st == "rejected" or st == "failed":
                    msg = "❌ Pemesanan Langsung ditolak admin.\nSilakan hubungi admin atau ganti metode pembayaran."
                elif st == "unpaid" or st == "pending":
                    if me == "LANGSUNG":
                        msg = "Silakan tekan tombol di bawah untuk konfirmasi\nbahwa Anda akan melakukan pemesanan langsung."
                        b = _pill(self.btn_action_frame, text="KONFIRMASI PEMESANAN",
                                  command=lambda: _set_cash(id_pesanan), w=200, h=38, r=19,
                                  color=C_MID, hover=C_DARK)
                        b.config(bg=WHITE)
                        b.pack()
                    else:
                        msg = "Silakan selesaikan pembayaran Anda\nmelalui jendela QRIS di browser."
                        b = _pill(self.btn_action_frame, text="BAYAR VIA QRIS",
                                  command=lambda: _open_midtrans(tk_snap), w=200, h=38, r=19,
                                  color=C_MID, hover=C_DARK)
                        b.config(bg=WHITE)
                        b.pack()

                lbl_msg.config(text=msg)
            except Exception as e:
                print(f"Status checking error: {e}")
            
            if polling[0] and win.winfo_exists():
                win.after(4000, _get_status)

        def _set_cash(oid):
            if messagebox.askyesno("Konfirmasi", "Yakin ingin melakukan pemesanan langsung?", parent=win):
                db = get_db()
                db.collection('pesanan').document(oid).update({
                    'payment_method': 'LANGSUNG',
                    'payment_status': 'waiting_confirmation'
                })
                _get_status()

        def _open_midtrans(token):
            from midtrans_config import WEBHOOK_BASE
            webbrowser.open(f"{WEBHOOK_BASE}/pay/{token}")

        def _change_method():
            m = messagebox.askquestion("Ganti Metode", "Ingin ganti ke QRIS (Online) atau Pemesanan Langsung?\n\n'Yes' untuk QRIS, 'No' untuk Langsung", parent=win)
            new_me = "QRIS" if m == "yes" else "LANGSUNG"
            new_st = "pending" if new_me == "QRIS" else "unpaid"
            db = get_db()
            db.collection('pesanan').document(id_pesanan).update({
                'payment_method': new_me,
                'payment_status': new_st
            })
            _get_status()

        btn_change.config(command=_change_method)
        _get_status()

        def _on_close():
            polling[0] = False
            win.destroy()
        
        win.protocol("WM_DELETE_WINDOW", _on_close)

    def _notif(self, msg: str, err: bool = False):
        self.lbl_notif.config(text=msg, fg=STOCK_OUT if err else STOCK_OK)
        if msg:
            self.after(3000, lambda: self.lbl_notif.config(text=""))