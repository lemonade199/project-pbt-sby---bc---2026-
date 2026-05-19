"""
user/transaksi.py - Halaman Transaksi User (Tanpa Login) + Foto Produk + Midtrans
Aplikasi Business Center SMKN 13 Bandung
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import os
<<<<<<< HEAD
import webbrowser
import threading
=======
import requests
from io import BytesIO
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72

from db import get_db, get_drive_service, DRIVE_FOLDER_ID, IMAGES_DIR, API_URL

API_BASE_URL = API_URL

PRIMARY    = "#CC0000"
PRIMARY_DK = "#A00000"
WHITE      = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
DARK_TEXT  = "#212121"
GRAY_TEXT  = "#757575"
ACCENT_G   = "#2E7D32"
ACCENT_G_DK= "#1B5E20"
CARD_BG    = "#FFFFFF"
CARD_HOVER = "#FFF0F0"
SHADOW_CLR = "#E0E0E0"

CARD_IMG_SIZE = (90, 90)


def _load_card_image(foto: str, stok: int):
    """Muat gambar produk dari local atau API. Return None jika tidak ada."""
    if not foto: return None
    try:
        # Nama file cache yang bersih
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
            if not service: return None

            # Cari file ID berdasarkan nama di folder yang ditentukan
            query = f"name = '{foto}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
            results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if not items:
                # Jika tidak ketemu dengan nama, cek apakah 'foto' mungkin sebuah ID
                if "." in str(foto) or len(str(foto)) < 20:
                    pass # Bukan ID
                else:
                    file_id = foto
                    # Download media
                    request = service.files().get_media(fileId=file_id)
                    img_data = request.execute()
                    with Image.open(BytesIO(img_data)) as img:
                        img_ready = img.convert("RGBA")
                        try:
                            img_ready.save(local_path)
                        except: pass
                        return _process_card_image(img_ready, stok)
            else:
                file_id = items[0]['id']
                # Download media
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
            with Image.new("RGBA", CARD_IMG_SIZE, (255, 255, 255, 0)) as img:
                return _process_card_image(img, stok)
            
        return None
    except Exception:
        return None

def _process_card_image(img, stok):
    """Helper untuk memproses resize dan canvas."""
    # Buat copy agar tidak memodifikasi original jika diperlukan
    img_thumb = img.copy()
    img_thumb.thumbnail(CARD_IMG_SIZE, Image.LANCZOS)
    
    canvas = Image.new("RGBA", CARD_IMG_SIZE, (255, 255, 255, 0))
    offset = ((CARD_IMG_SIZE[0] - img_thumb.width)  // 2,
                (CARD_IMG_SIZE[1] - img_thumb.height) // 2)
    canvas.paste(img_thumb, offset, img_thumb)

    if stok <= 0:
        draw = ImageDraw.Draw(canvas)
        line_width = 8
        w, h = CARD_IMG_SIZE
        color = (204, 0, 0, 200) # PRIMARY (red) dengan alpha
        draw.line((15, 15, w-15, h-15), fill=color, width=line_width)
        draw.line((15, h-15, w-15, 15), fill=color, width=line_width)

    return ImageTk.PhotoImage(canvas)


class TransaksiWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master      = master
        self.keranjang   = {}   # {id_barang: {"nama","harga","jumlah","stok"}}
        self.barang_data = []
        self._card_imgs  = {}   # simpan PhotoImage agar tidak GC

        self.title("Transaksi - Business Center SMKN 13 Bandung")
        self.geometry("1100x660")
        self.configure(bg=LIGHT_GRAY)
        self._center(1100, 660)
        self._build_ui()
        self._load_barang()
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Layout utama ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PRIMARY, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Transaksi - Business Center SMKN 13 Bandung",
                 font=("Segoe UI", 13, "bold"), bg=PRIMARY, fg=WHITE).pack(
                     side="left", padx=20, pady=16)
        tk.Button(hdr, text="Kembali", font=("Segoe UI", 9),
                  bg=PRIMARY_DK, fg=WHITE, relief="flat", padx=12, pady=5,
                  cursor="hand2", command=self._kembali).pack(side="right", padx=16)

        body = tk.Frame(self, bg=LIGHT_GRAY)
        body.pack(fill="both", expand=True)

        # ── Panel kiri: Katalog ────────────────────────────────────────────
        left = tk.Frame(body, bg=LIGHT_GRAY)
        left.pack(side="left", fill="both", expand=True, padx=(14, 8), pady=10)

        search_row = tk.Frame(left, bg=LIGHT_GRAY)
        search_row.pack(fill="x", pady=(0, 6))
        tk.Label(search_row, text="Cari Barang:", font=("Segoe UI", 10),
                 bg=LIGHT_GRAY, fg=DARK_TEXT).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_barang())
        tk.Entry(search_row, textvariable=self.search_var,
                 font=("Segoe UI", 10), width=22, relief="solid", bd=1).pack(
                     side="left", padx=8, ipady=5)
        tk.Button(search_row, text="Refresh", font=("Segoe UI", 9),
                  bg=LIGHT_GRAY, relief="flat", cursor="hand2",
                  command=self._load_barang).pack(side="left")

        tk.Label(left, text="Daftar Barang", font=("Segoe UI", 11, "bold"),
                 bg=LIGHT_GRAY, fg=DARK_TEXT).pack(anchor="w", pady=(0, 4))

        # Canvas scrollable
        cont = tk.Frame(left, bg=LIGHT_GRAY)
        cont.pack(fill="both", expand=True)

        self.cat_canvas = tk.Canvas(cont, bg=LIGHT_GRAY, highlightthickness=0)
        cat_sb = ttk.Scrollbar(cont, orient="vertical", command=self.cat_canvas.yview)
        self.cat_canvas.configure(yscrollcommand=cat_sb.set)
        cat_sb.pack(side="right", fill="y")
        self.cat_canvas.pack(side="left", fill="both", expand=True)

        self.cat_frame  = tk.Frame(self.cat_canvas, bg=LIGHT_GRAY)
        self.cat_window = self.cat_canvas.create_window((0, 0), window=self.cat_frame, anchor="nw")

        self.cat_frame.bind("<Configure>",
                             lambda e: self.cat_canvas.configure(
                                 scrollregion=self.cat_canvas.bbox("all")))
        self.cat_canvas.bind("<Configure>",
                              lambda e: self.cat_canvas.itemconfig(
                                  self.cat_window, width=e.width))
        self.cat_canvas.bind_all("<MouseWheel>",
                                  lambda e: self.cat_canvas.yview_scroll(
                                      int(-1*(e.delta/120)), "units"))

        # ── Panel kanan: Keranjang ─────────────────────────────────────────
        right = tk.Frame(body, bg=WHITE, width=310)
        right.pack(side="right", fill="y", padx=(8, 14), pady=10)
        right.pack_propagate(False)

        cart_hdr = tk.Frame(right, bg=PRIMARY, height=44)
        cart_hdr.pack(fill="x")
        cart_hdr.pack_propagate(False)
        tk.Label(cart_hdr, text="Keranjang Belanja",
                 font=("Segoe UI", 11, "bold"), bg=PRIMARY, fg=WHITE).pack(expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Cart.Treeview",
                        font=("Segoe UI", 9), rowheight=28,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Cart.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background="#424242", foreground=WHITE, relief="flat")
        style.map("Cart.Treeview", background=[("selected", "#FFD6D6")])

        cart_tf = tk.Frame(right, bg=WHITE)
        cart_tf.pack(fill="both", expand=True)

        cart_cols = ("Barang", "Qty", "Subtotal")
        self.cart_tree = ttk.Treeview(cart_tf, columns=cart_cols,
                                       show="headings", style="Cart.Treeview")
        self.cart_tree.heading("Barang",   text="Nama Barang")
        self.cart_tree.heading("Qty",      text="Qty")
        self.cart_tree.heading("Subtotal", text="Subtotal")
        self.cart_tree.column("Barang",   width=130, anchor="w")
        self.cart_tree.column("Qty",      width=36,  anchor="center")
        self.cart_tree.column("Subtotal", width=100, anchor="e")
        cart_sb2 = ttk.Scrollbar(cart_tf, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_sb2.set)
        cart_sb2.pack(side="right", fill="y")
        self.cart_tree.pack(fill="both", expand=True)

        tk.Button(right, text="Hapus Item Dipilih",
                  font=("Segoe UI", 9), bg=LIGHT_GRAY, fg=PRIMARY, relief="flat",
                  pady=5, cursor="hand2", command=self._hapus_item).pack(fill="x")

        tk.Frame(right, bg=SHADOW_CLR, height=1).pack(fill="x")

        total_f = tk.Frame(right, bg=WHITE)
        total_f.pack(fill="x", padx=14, pady=8)
        tk.Label(total_f, text="Total:", font=("Segoe UI", 10),
                 bg=WHITE, fg=GRAY_TEXT).pack(side="left")
        self.lbl_total = tk.Label(total_f, text="Rp 0",
                                   font=("Segoe UI", 14, "bold"),
                                   bg=WHITE, fg=PRIMARY)
        self.lbl_total.pack(side="right")

        self.lbl_item_count = tk.Label(right, text="0 jenis item",
                                        font=("Segoe UI", 9), bg=WHITE, fg=GRAY_TEXT)
        self.lbl_item_count.pack(anchor="e", padx=14)

        self.btn_checkout = tk.Button(right, text="💳 BAYAR SEKARANG",
                                       font=("Segoe UI", 12, "bold"),
                                       bg="#CC0000", fg=WHITE, relief="flat",
                                       pady=12, cursor="hand2", state="disabled",
                                       activebackground="#A00000", command=self._checkout)
        self.btn_checkout.pack(fill="x", pady=(6, 0))

        tk.Button(right, text="Kosongkan Keranjang",
                  font=("Segoe UI", 9), bg=LIGHT_GRAY, fg=GRAY_TEXT,
                  relief="flat", pady=6, cursor="hand2",
                  command=self._kosongkan).pack(fill="x")

        self.lbl_notif = tk.Label(right, text="", font=("Segoe UI", 9),
                                   bg=WHITE, fg=ACCENT_G, wraplength=280, justify="center")
        self.lbl_notif.pack(fill="x", padx=8, pady=4)

    # ── Katalog ───────────────────────────────────────────────────────────────
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
            messagebox.showerror("Error DB", str(e))
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

        COLS = 3
        for idx, item in enumerate(data):
            try:
                r, c = divmod(idx, COLS)
                self._make_card(item, r, c)
                self.cat_frame.grid_columnconfigure(c, weight=1)
            except Exception as e:
                print(f"Error rendering item {item.get('id_barang')}: {e}")
                continue

        if not data:
            tk.Label(self.cat_frame, text="Tidak ada barang.",
                     font=("Segoe UI", 11), bg=LIGHT_GRAY, fg=GRAY_TEXT).grid(
                         column=0, row=0, padx=20, pady=30)

    def _make_card(self, item, row, col):
        id_b  = item["id_barang"]
        nama  = item["nama_barang"]
        try:
            harga = float(item["harga_barang"] or 0)
        except (ValueError, TypeError):
            harga = 0
        stok  = item["stok"]
        foto  = item.get("foto")

        card = tk.Frame(self.cat_frame, bg=CARD_BG, relief="flat",
                        highlightbackground=SHADOW_CLR, highlightthickness=1,
                        width=200, height=200)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        card.pack_propagate(False)

        # ── Foto produk / ikon default ─────────────────────────────────────
        img = _load_card_image(foto, stok)
        if img:
            self._card_imgs[id_b] = img
            img_lbl = tk.Label(card, image=img, bg=CARD_BG)
            img_lbl.pack(pady=(10, 2))
        else:
            img_lbl = tk.Label(card, text="📦", font=("Segoe UI", 30), bg=CARD_BG)
            img_lbl.pack(pady=(10, 2))

        tk.Label(card, text=nama, font=("Segoe UI", 9, "bold"),
                 bg=CARD_BG, fg=DARK_TEXT, wraplength=175, justify="center").pack(padx=4)
        tk.Label(card, text=f"Rp {harga:,.0f}", font=("Segoe UI", 10, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack()

        stok_color = ACCENT_G if stok > 5 else ("#E65100" if stok > 0 else PRIMARY_DK)
        stok_text  = f"Stok: {stok}" if stok > 0 else "Stok Habis"
        tk.Label(card, text=stok_text, font=("Segoe UI", 8),
                 bg=CARD_BG, fg=stok_color).pack()

        if stok > 0:
            btn = tk.Button(card, text="+ Tambah", font=("Segoe UI", 8, "bold"),
                            bg=PRIMARY, fg=WHITE, relief="flat", padx=10, pady=3,
                            cursor="hand2",
                            command=lambda i=item: self._tambah_ke_keranjang(i))
            btn.pack(pady=(4, 8))

            # Hover hanya di frame & label, bukan button
            for w in [card, img_lbl]:
                w.bind("<Enter>", lambda e, c=card: c.config(bg=CARD_HOVER))
                w.bind("<Leave>", lambda e, c=card: c.config(bg=CARD_BG))
        else:
            tk.Label(card, text="Stok Habis", font=("Segoe UI", 8),
                     bg=CARD_BG, fg=GRAY_TEXT).pack(pady=(4, 8))

    # ── Keranjang ─────────────────────────────────────────────────────────────
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
                self._notif(f"Stok \"{item.get('nama_barang', '')}\" tidak mencukupi!", error=True)
                return
            self.keranjang[id_b]["jumlah"] += 1
        else:
            if stok_db <= 0:
                self._notif("Stok habis!", error=True)
                return
            self.keranjang[id_b] = {
                "nama": item.get("nama_barang", ""), "harga": float(item.get("harga_barang", 0)),
                "jumlah": 1, "stok": stok_db
            }
        self._update_cart_ui()
        self._notif(f"\"{item.get('nama_barang', '')}\" ditambahkan.")

    def _hapus_item(self):
        sel = self.cart_tree.selection()
        if sel:
            del self.keranjang[str(sel[0])]
            self._update_cart_ui()

    def _kosongkan(self):
        if self.keranjang and messagebox.askyesno("Kosongkan", "Kosongkan keranjang?", parent=self):
            self.keranjang.clear()
            self._update_cart_ui()

    def _update_cart_ui(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        total = 0
        for id_b, d in self.keranjang.items():
            sub    = d["harga"] * d["jumlah"]
            total += sub
            self.cart_tree.insert("", "end", iid=str(id_b),
                                  values=(d["nama"], d["jumlah"], f"Rp {sub:,.0f}"))
        self.lbl_total.config(text=f"Rp {total:,.0f}")
        n = len(self.keranjang)
        self.lbl_item_count.config(text=f"{n} jenis item")
        self.btn_checkout.config(state="normal" if n > 0 else "disabled")

    # ── Checkout + Midtrans ───────────────────────────────────────────────────
    def _dialog_nama(self) -> str:
        """Tampilkan dialog input nama pembeli. Return nama atau '' jika dilewati."""
        nama = simpledialog.askstring(
            "Nama Pembeli",
            "Masukkan nama Anda (opsional):",
            parent=self,
            initialvalue=""
        )
        return (nama or "").strip()

    def _checkout(self):
        if not self.keranjang:
            return

        total     = sum(v["harga"]*v["jumlah"] for v in self.keranjang.values())
        item_list = "\n".join(
            f"  - {v['nama']} x{v['jumlah']} = Rp {v['harga']*v['jumlah']:,.0f}"
            for v in self.keranjang.values()
        )
        # Dialog Nama & Metode
        dialog = tk.Toplevel(self)
        dialog.title("Checkout")
        dialog.geometry("350x300")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="Konfirmasi Checkout", font=("Segoe UI", 12, "bold"),
                 bg="#FFFFFF").pack(pady=15)

        tk.Label(dialog, text="Nama Pembeli:", bg="#FFFFFF").pack(anchor="w", padx=40)
        ent_nama = tk.Entry(dialog, font=("Segoe UI", 11), relief="solid", bd=1)
        ent_nama.pack(fill="x", padx=40, pady=5, ipady=4)
        ent_nama.insert(0, "Pembeli Umum")

        tk.Label(dialog, text="Metode Pembayaran:", bg="#FFFFFF").pack(anchor="w", padx=40, pady=(10,0))
        var_me = tk.StringVar(value="midtrans")
        tk.Radiobutton(dialog, text="Online (QRIS, VA, E-Wallet)", variable=var_me,
                        value="midtrans", bg="#FFFFFF").pack(anchor="w", padx=50)
        tk.Radiobutton(dialog, text="Cash (Bayar di Toko)", variable=var_me,
                        value="cash", bg="#FFFFFF").pack(anchor="w", padx=50)

        def _do_checkout():
            nama = ent_nama.get().strip()
            meth = var_me.get().upper()
            if not nama:
                messagebox.showwarning("Peringatan", "Isi nama pembeli!")
                return
            dialog.destroy()
            self._process_checkout(nama, meth)

        tk.Button(dialog, text="PROSES SEKARANG", bg="#CC0000", fg="#FFFFFF",
                  font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=10,
                  command=_do_checkout).pack(pady=20)

    def _process_checkout(self, nama_pembeli: str, method: str):
        total = sum(d["harga"]*d["jumlah"] for d in self.keranjang.values())
        try:
<<<<<<< HEAD
            # 1. Simpan pesanan ke DB (status awal)
            id_pesanan = execute_query(
                "INSERT INTO pesanan (tanggal, total_harga, status, nama_pembeli, payment_status, payment_method) VALUES (NOW(), %s, 'pending', %s, 'unpaid', %s)",
                (total, nama_pembeli, method), fetch=False
            )

            # 2. Simpan detail
            for id_b, item in self.keranjang.items():
                execute_query(
                    "INSERT INTO detail_pesanan (id_pesanan, id_barang, jumlah, subtotal) VALUES (%s, %s, %s, %s)",
                    (id_pesanan, id_b, item["jumlah"], item["harga"]*item["jumlah"])
                )

            # 3. Jika Midtrans, buat token
            if method == "MIDTRANS":
                from midtrans_snap import create_snap_transaction
                items_midtrans = [{"id": str(id_b), "price": int(d["harga"]), "quantity": d["jumlah"], "name": d["nama"][:50]} for id_b, d in self.keranjang.items()]
                snap_token = create_snap_transaction(id_pesanan, total, nama_pembeli, items_midtrans)
                execute_query(
                    "UPDATE pesanan SET snap_token=%s WHERE id_pesanan=%s",
                    (snap_token, id_pesanan)
                )
                import webbrowser
                from midtrans_config import WEBHOOK_BASE
                webbrowser.open(f"{WEBHOOK_BASE}/pay/{snap_token}")

            # 4. Kosongkan keranjang & refresh
=======
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
            doc_ref.set({
                "tanggal": now_str,
                "total_harga": total,
                "status": "pending",
                "detail_pesanan": details
            })
            
            id_pesanan = doc_ref.id[:8]
            self._show_sukses(id_pesanan, total)
>>>>>>> 099d9731109ffb4053743896f150a6ec4c3aae72
            self.keranjang.clear()
            self._update_cart_ui()
            self._load_barang()

            # 5. Tampilkan window status
            self._show_payment_status(id_pesanan)

        except Exception as e:
            messagebox.showerror("Error Checkout", str(e))

    def _show_payment_status(self, id_pesanan):
        """Tampilkan window status pembayaran dan polling DB."""
        win = tk.Toplevel(self)
        win.title("Status Pembayaran")
        win.geometry("400x460")
        win.resizable(False, False)
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        # Center
        x = self.winfo_x() + (self.winfo_width()  - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 460) // 2
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="Informasi Pembayaran", font=("Segoe UI", 13, "bold"),
                 bg="#FFFFFF", fg="#212121").pack(pady=(20, 10))

        frame = tk.Frame(win, bg="#F5F5F5", padx=20, pady=15, relief="solid", bd=1)
        frame.pack(fill="x", padx=30)

        lbl_id = tk.Label(frame, text=f"Order ID: # {id_pesanan}", font=("Segoe UI", 10), bg="#F5F5F5")
        lbl_id.pack(anchor="w")

        lbl_meth = tk.Label(frame, text="Metode: -", font=("Segoe UI", 10), bg="#F5F5F5")
        lbl_meth.pack(anchor="w", pady=2)

        lbl_status = tk.Label(frame, text="Status: CHECKING...", font=("Segoe UI", 11, "bold"),
                               bg="#F5F5F5", fg="#CC0000")
        lbl_status.pack(anchor="w", pady=(5, 0))

        lbl_msg = tk.Label(win, text="Mohon tunggu...", font=("Segoe UI", 9),
                            bg="#FFFFFF", fg="#757575", wraplength=340, justify="center")
        lbl_msg.pack(pady=15)

        btn_action = tk.Button(win, text="BAYAR SEKARANG", font=("Segoe UI", 10, "bold"),
                                bg="#CC0000", fg="#FFFFFF", relief="flat", padx=20, pady=8)
        btn_action.pack(pady=5)
        btn_action.pack_forget()

        btn_change = tk.Button(win, text="🔄 Ganti Metode Pembayaran", font=("Segoe UI", 9),
                                bg="#F5F5F5", fg="#212121", relief="flat", padx=10, pady=5)
        btn_change.pack(pady=5)

        polling = [True]

        def _get_status():
            if not polling[0] or not win.winfo_exists():
                return
            try:
                r = execute_query(
                    "SELECT payment_status, payment_method, snap_token FROM pesanan WHERE id_pesanan=%s",
                    (id_pesanan,), fetch=True
                )[0]
                st = r["payment_status"]
                me = (r["payment_method"] or "Belum dipilih").upper()
                tk_snap = r["snap_token"]

                lbl_meth.config(text=f"Metode: {me}")
                lbl_status.config(text=f"Status: {st.replace('_',' ').upper()}")

                # Warna status
                colors = {
                    "paid": "#2E7D32", 
                    "pending": "#1565C0", 
                    "waiting_confirmation": "#E65100",
                    "rejected": "#B71C1C",
                    "failed": "#B71C1C",
                    "expired": "#757575",
                    "unpaid": "#CC0000"
                }
                lbl_status.config(fg=colors.get(st, "#CC0000"))

                msg = "Mohon tunggu konfirmasi dari sistem."
                if st == "paid":
                    msg = "✅ Pembayaran Berhasil!\nPesanan Anda sedang diproses oleh admin."
                    btn_action.pack_forget()
                    btn_change.pack_forget()
                    polling[0] = False
                elif st == "waiting_confirmation":
                    msg = "🕒 Menunggu konfirmasi admin untuk pembayaran Cash.\nSilakan serahkan uang ke kasir."
                    btn_action.pack_forget()
                elif st == "rejected":
                    msg = "❌ Pembayaran Cash ditolak admin.\nSilakan hubungi admin atau ganti metode pembayaran."
                elif st == "unpaid" or st == "pending":
                    if me == "CASH":
                        msg = "Silakan tekan tombol di bawah untuk konfirmasi\nbahwa Anda akan membayar cash di kasir."
                        btn_action.config(text="SAYA AKAN BAYAR CASH", command=lambda: _set_cash(id_pesanan))
                        btn_action.pack()
                    else:
                        msg = "Silakan selesaikan pembayaran Anda\nmelalui jendela Midtrans di browser."
                        btn_action.config(text="BAYAR VIA MIDTRANS", command=lambda: _open_midtrans(tk_snap))
                        btn_action.pack()

                lbl_msg.config(text=msg)
            except Exception: pass
            
            if polling[0] and win.winfo_exists():
                win.after(4000, _get_status)

        def _set_cash(oid):
            if messagebox.askyesno("Konfirmasi", "Yakin ingin bayar cash langsung ke toko?"):
                execute_query(
                    "UPDATE pesanan SET payment_method='CASH', payment_status='waiting_confirmation' WHERE id_pesanan=%s",
                    (oid,)
                )
                _get_status()

        def _open_midtrans(token):
            import webbrowser
            from midtrans_config import WEBHOOK_BASE
            webbrowser.open(f"{WEBHOOK_BASE}/pay/{token}")

        def _change_method():
            m = messagebox.askquestion("Ganti Metode", "Ingin ganti ke Midtrans (Online) atau Cash (Offline)?\n\n'Yes' untuk Online, 'No' untuk Cash")
            new_me = "MIDTRANS" if m == "yes" else "CASH"
            new_st = "pending" if new_me == "MIDTRANS" else "unpaid"
            execute_query(
                "UPDATE pesanan SET payment_method=%s, payment_status=%s WHERE id_pesanan=%s",
                (new_me, new_st, id_pesanan)
            )
            _get_status()

        btn_change.config(command=_change_method)
        _get_status()

        def _on_close():
            polling[0] = False
            win.destroy()
        
        win.protocol("WM_DELETE_WINDOW", _on_close)

    def _kembali(self):
        """Tutup window transaksi dan kembali ke halaman pilih mode."""
        if hasattr(self.master, "_on_child_close"):
            self.master._on_child_close(self)
        else:
            self.destroy()
            self.master.deiconify()

    def _notif(self, msg: str, error: bool = False):
        self.lbl_notif.config(text=msg, fg=PRIMARY if error else ACCENT_G)
        if msg:
            self.after(3000, lambda: self.lbl_notif.config(text=""))