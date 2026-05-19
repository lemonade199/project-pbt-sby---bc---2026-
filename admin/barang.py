"""
admin/barang.py - Panel Kelola Barang (CRUD) + Foto Produk
Aplikasi Business Center SMKN 13 Bandung
"""

import sys
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import shutil
import threading
import time
import requests
from io import BytesIO

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
ROW_ALT    = "#FFF5F5"


# ─── Helper validasi input ────────────────────────────────────────────────────
def _make_digit_validator(root):
    """Return (vcmd, 'key') untuk Entry agar hanya menerima digit."""
    def _validate(new_val):
        return new_val == "" or new_val.isdigit()
    vcmd = (root.register(_validate), "%P")
    return vcmd


def _apply_harga_x1000(entry: tk.Entry, preview_lbl: tk.Label = None):
    """FocusOut: ambil angka di entry, kalikan 1000, tulis kembali."""
    raw = entry.get().strip()
    if raw.isdigit() and raw != "":
        nilai = int(raw) * 1000
        entry.delete(0, "end")
        entry.insert(0, str(nilai))
        if preview_lbl:
            preview_lbl.config(text=f"= Rp {nilai:,.0f}")
    elif preview_lbl:
        preview_lbl.config(text="")


def _on_harga_keyrelease(entry: tk.Entry, preview_lbl: tk.Label):
    """KeyRelease: tampilkan preview × 1000 secara realtime."""
    raw = entry.get().strip()
    if raw.isdigit() and raw != "":
        preview_lbl.config(text=f"→ Rp {int(raw) * 1000:,.0f}")
    else:
        preview_lbl.config(text="")


def load_thumbnail(foto: str, size=(50, 50)):
    if not foto: return None
    try:
        # Coba lokal dulu untuk cache
        # Pastikan kita konsisten dengan penamaan cache
        clean_name = "".join([c for c in str(foto) if c.isalnum() or c in "._- "])
        local_path = os.path.join(IMAGES_DIR, f"{clean_name}.png")
        
        if os.path.exists(local_path):
            try:
                with Image.open(local_path) as img:
                    img_thumb = img.convert("RGBA")
                    img_thumb.thumbnail(size, Image.LANCZOS)
                    return ImageTk.PhotoImage(img_thumb)
            except:
                pass # Jika file cache korup, lanjut download

        # Ambil dari Google Drive
        service = get_drive_service()
        if not service: return None
        
        # Cari file ID berdasarkan nama di folder yang ditentukan
        query = f"name = '{foto}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if not items:
            # Jika tidak ketemu dengan nama, cek apakah 'foto' mungkin sebuah ID
            # GDrive ID biasanya alphanumeric tanpa titik dan panjang (misal 33 char)
            if "." in str(foto) or len(str(foto)) < 20:
                # Ini kemungkinan nama file yang tidak ditemukan
                return None
            file_id = foto
        else:
            file_id = items[0]['id']

        # Download media menggunakan file_id yang ditemukan
        try:
            request = service.files().get_media(fileId=file_id)
            img_data = request.execute()
            with Image.open(BytesIO(img_data)) as img:
                img_conv = img.convert("RGBA")
                # Simpan ke lokal sebagai cache
                img_conv.save(local_path)
                img_conv.thumbnail(size, Image.LANCZOS)
                return ImageTk.PhotoImage(img_conv)
        except Exception as e:
            # Sering terjadi jika fileId 404 atau invalid
            return None
            
    except Exception as e:
        print(f"Error loading thumbnail from GDrive: {e}")
        return None


class BarangPanel(tk.Frame):
    def __init__(self, parent, dashboard):
        super().__init__(parent, bg=LIGHT_GRAY)
        self.dashboard    = dashboard
        self.selected_id  = None
        self._thumb_refs  = {}   # simpan referensi agar tidak di-GC
        self._build()
        self._load_data()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=WHITE, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Kelola Barang", font=("Segoe UI", 15, "bold"),
                 bg=WHITE, fg=DARK_TEXT).pack(side="left", padx=24, pady=14)
        tk.Button(hdr, text="+ Tambah Barang", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._open_form_tambah).pack(side="right", padx=20, pady=12)

        # ── Search bar ────────────────────────────────────────────────────────
        sb = tk.Frame(self, bg=LIGHT_GRAY)
        sb.pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(sb, text="Cari:", font=("Segoe UI", 10),
                 bg=LIGHT_GRAY, fg=DARK_TEXT).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        tk.Entry(sb, textvariable=self.search_var,
                 font=("Segoe UI", 10), width=28, relief="solid", bd=1).pack(
                     side="left", padx=8, ipady=5)

        # ── Treeview ──────────────────────────────────────────────────────────
        table_frame = tk.Frame(self, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Barang.Treeview",
                        font=("Segoe UI", 10), rowheight=52,
                        background=WHITE, fieldbackground=WHITE, foreground=DARK_TEXT)
        style.configure("Barang.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background=PRIMARY, foreground=WHITE, relief="flat")
        style.map("Barang.Treeview",
                  background=[("selected", "#FFD6D6")],
                  foreground=[("selected", DARK_TEXT)])

        cols = ("Nama Barang", "Harga", "Stok")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                  show="tree headings", style="Barang.Treeview")
        self.tree.heading("#0",         text="Foto")
        self.tree.heading("Nama Barang",text="Nama Barang")
        self.tree.heading("Harga",      text="Harga")
        self.tree.heading("Stok",       text="Stok")

        self.tree.column("#0",          width=65,  anchor="center", stretch=tk.NO)
        self.tree.column("Nama Barang", width=280, anchor="w")
        self.tree.column("Harga",       width=150, anchor="e")
        self.tree.column("Stok",        width=80,  anchor="center")

        sb2 = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Context Menu ──────────────────────────────────────────────────────
        self.menu_context = tk.Menu(self, tearoff=0, font=("Segoe UI", 10))
        self.menu_context.add_command(label="✏️ Edit Barang", command=self._open_form_edit)
        self.menu_context.add_command(label="⚡ Update Cepat (Stok/Foto)", command=self._open_form_update_cepat)
        self.menu_context.add_separator()
        self.menu_context.add_command(label="🗑️ Hapus Barang", command=self._hapus, foreground=PRIMARY)
        
        self.tree.bind("<Button-3>", self._on_right_click)

        # ── Action bar bawah ──────────────────────────────────────────────────
        act = tk.Frame(self, bg=WHITE)
        act.pack(fill="x", padx=20, pady=(0, 10))

        self.btn_edit = tk.Button(act, text="Edit Barang",
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#1565C0", fg=WHITE, relief="flat",
                                   padx=14, pady=7, cursor="hand2",
                                   state="disabled", command=self._open_form_edit)
        self.btn_edit.pack(side="left", padx=(16, 8), pady=10)

        self.btn_hapus = tk.Button(act, text="Hapus Barang",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=PRIMARY, fg=WHITE, relief="flat",
                                    padx=14, pady=7, cursor="hand2",
                                    state="disabled", command=self._hapus)
        self.btn_hapus.pack(side="left", pady=10)

        self.lbl_info = tk.Label(act, text="Pilih baris untuk edit/hapus",
                                  font=("Segoe UI", 9), bg=WHITE, fg=GRAY_TEXT)
        self.lbl_info.pack(side="right", padx=16)

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_data(self):
        self.all_data = []
        try:
            db = get_db()
            docs = db.collection('barang').stream()
            for doc in docs:
                r = doc.to_dict()
                r["id_barang"] = doc.id
                self.all_data.append(r)
            self.all_data.sort(key=lambda x: x.get("nama_barang", "").lower())
        except Exception as e:
            messagebox.showerror("Error DB", str(e))
        self._render_table(self.all_data)

    def _render_table(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._thumb_refs.clear()

        for i, row in enumerate(data):
            thumb = load_thumbnail(row.get("foto"), size=(44, 44))
            harga = f"Rp {row['harga_barang']:,.0f}"
            tag   = "alt" if i % 2 == 0 else ""

            if thumb:
                self._thumb_refs[str(row["id_barang"])] = thumb
                self.tree.insert("", "end", iid=str(row["id_barang"]),
                                 image=thumb, text="",
                                 values=(row["nama_barang"], harga, row["stok"]),
                                 tags=(tag,))
            else:
                self.tree.insert("", "end", iid=str(row["id_barang"]),
                                 text="📦",
                                 values=(row["nama_barang"], harga, row["stok"]),
                                 tags=(tag,))

        self.tree.tag_configure("alt", background=ROW_ALT)

    def _filter(self):
        kw = self.search_var.get().lower()
        filtered = [r for r in self.all_data if kw in r["nama_barang"].lower()]
        self._render_table(filtered)

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel:
            self.selected_id = str(sel[0])
            self.btn_edit.config(state="normal")
            self.btn_hapus.config(state="normal")
            nama = self.tree.item(sel[0])["values"][0]
            self.lbl_info.config(text=f"Dipilih: {nama}")
        else:
            self.selected_id = None
            self.btn_edit.config(state="disabled")
            self.btn_hapus.config(state="disabled")
            self.lbl_info.config(text="Pilih baris untuk edit/hapus")

    def _on_right_click(self, event):
        """Tampilkan menu klik kanan pada item yang ditunjuk."""
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self._on_select(None)
            self.menu_context.post(event.x_root, event.y_root)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def _open_form_tambah(self):
        BarangForm(self, mode="tambah")

    def _open_form_edit(self):
        if not self.selected_id:
            return
        try:
            db = get_db()
            doc = db.collection('barang').document(self.selected_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id_barang"] = doc.id
                BarangForm(self, mode="edit", data=data)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_form_update_cepat(self):
        UpdateCepatForm(self, id_barang=self.selected_id)

    def _hapus(self):
        if not self.selected_id:
            return
        
        try:
            db = get_db()
            doc = db.collection('barang').document(self.selected_id).get()
            if not doc.exists:
                messagebox.showwarning("Peringatan", "Data barang sudah tidak ada.")
                self.refresh()
                return
            
            data = doc.to_dict()
            nama = data.get("nama_barang", "Barang")
            foto_id = data.get("foto")

            if messagebox.askyesno("Hapus Barang", f"Yakin hapus barang:\n\"{nama}\"?\n\nData dan foto di Drive akan dihapus permanen.", icon="warning"):
                # 1. Hapus dari Firestore
                db.collection('barang').document(self.selected_id).delete()
                
                # 2. Hapus dari Google Drive (Jika ada ID foto)
                # Pastikan foto_id adalah ID GDrive (bukan nama file lama)
                if foto_id and "." not in str(foto_id) and len(str(foto_id)) >= 20:
                    def delete_drive_file(fid):
                        try:
                            service = get_drive_service()
                            if service:
                                service.files().delete(fileId=fid).execute()
                        except Exception as e:
                            print(f"Gagal hapus file di Drive: {e}")

                    # Jalankan di thread agar tidak membekukan UI
                    threading.Thread(target=delete_drive_file, args=(foto_id,), daemon=True).start()
                
                # 3. Hapus cache lokal
                if foto_id:
                    clean_name = "".join([c for c in str(foto_id) if c.isalnum() or c in "._- "])
                    local_path = os.path.join(IMAGES_DIR, f"{clean_name}.png")
                    if os.path.exists(local_path):
                        try: os.remove(local_path)
                        except: pass

                messagebox.showinfo("Berhasil", f"Barang \"{nama}\" berhasil dihapus.")
                self.selected_id = None
                self.refresh()

        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat menghapus: {e}")

    def refresh(self):
        self.selected_id = None
        self._load_data()


# ─── Form Tambah / Edit Barang ────────────────────────────────────────────────
class BarangForm(tk.Toplevel):
    def __init__(self, panel: BarangPanel, mode: str, data: dict = None):
        super().__init__(panel)
        self.panel       = panel
        self.mode        = mode
        self.data        = data or {}
        self._foto_path  = None   # path file asli yang dipilih
        self._foto_nama  = self.data.get("foto") or None  # nama file di images/
        self._img_ref    = None   # simpan PhotoImage agar tidak GC

        title = "Tambah Barang" if mode == "tambah" else "Edit Barang"
        self.title(title)
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self._center(480, 520)
        self._build()
        self.grab_set()
        self.transient(panel)

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        title_text = "Tambah Barang Baru" if self.mode == "tambah" else "Edit Data Barang"
        hdr = tk.Frame(self, bg=PRIMARY, height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title_text, font=("Segoe UI", 12, "bold"),
                 bg=PRIMARY, fg=WHITE).pack(expand=True)

        body = tk.Frame(self, bg=WHITE, padx=28, pady=18)
        body.pack(fill="both", expand=True)

        # ── Field teks ────────────────────────────────────────────────────────
        vcmd = _make_digit_validator(self)

        # Nama Barang
        tk.Label(body, text="Nama Barang", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        self.entries = {}
        ent_nama = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1, bg=LIGHT_GRAY)
        ent_nama.pack(fill="x", ipady=7, pady=(0, 10))
        self.entries["nama"] = ent_nama

        # Harga — hanya angka + ×1000 saat focus out
        tk.Label(body, text="Harga (Rp)  ✦ ketik angka → otomatis ×1000",
                 font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        ent_harga = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                             bg=LIGHT_GRAY, validate="key", validatecommand=vcmd)
        ent_harga.pack(fill="x", ipady=7, pady=(0, 2))
        self.entries["harga"] = ent_harga

        self.lbl_harga_preview = tk.Label(body, text="",
                                           font=("Segoe UI", 9, "italic"),
                                           bg=WHITE, fg="#1565C0", anchor="e")
        self.lbl_harga_preview.pack(fill="x", pady=(0, 8))

        ent_harga.bind("<KeyRelease>",
                       lambda e: _on_harga_keyrelease(ent_harga, self.lbl_harga_preview))
        ent_harga.bind("<FocusOut>",
                       lambda e: _apply_harga_x1000(ent_harga, self.lbl_harga_preview))

        # Stok — hanya angka
        tk.Label(body, text="Stok", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 2))
        ent_stok = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                            bg=LIGHT_GRAY, validate="key", validatecommand=vcmd)
        ent_stok.pack(fill="x", ipady=7, pady=(0, 10))
        self.entries["stok"] = ent_stok

        if self.mode == "edit" and self.data:
            self.entries["nama"].insert(0,  self.data.get("nama_barang", ""))
            # Harga edit: tampilkan nilai asli (sudah dalam ribuan)
            harga_asli = str(int(self.data.get("harga_barang", 0)))
            self.entries["harga"].insert(0, harga_asli)
            self.lbl_harga_preview.config(text=f"= Rp {int(harga_asli):,.0f}")
            self.entries["stok"].insert(0,  str(self.data.get("stok", "")))

        # ── Foto ──────────────────────────────────────────────────────────────
        tk.Label(body, text="Foto Produk", font=("Segoe UI", 10, "bold"),
                 bg=WHITE, fg=DARK_TEXT, anchor="w").pack(fill="x", pady=(0, 4))

        foto_row = tk.Frame(body, bg=WHITE)
        foto_row.pack(fill="x", pady=(0, 12))

        # Preview box
        self.preview_frame = tk.Frame(foto_row, bg=LIGHT_GRAY, width=100, height=100,
                                       relief="solid", bd=1)
        self.preview_frame.pack(side="left")
        self.preview_frame.pack_propagate(False)

        self.lbl_preview = tk.Label(self.preview_frame, text="Belum ada\nfoto",
                                     font=("Segoe UI", 8), bg=LIGHT_GRAY, fg=GRAY_TEXT,
                                     justify="center")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        # Tombol foto
        btn_col = tk.Frame(foto_row, bg=WHITE)
        btn_col.pack(side="left", padx=12, fill="y")

        tk.Button(btn_col, text="Pilih Foto",
                  font=("Segoe UI", 9, "bold"),
                  bg="#1565C0", fg=WHITE, relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._pilih_foto).pack(pady=(8, 6))

        self.btn_hapus_foto = tk.Button(btn_col, text="Hapus Foto",
                                         font=("Segoe UI", 9),
                                         bg=LIGHT_GRAY, fg=PRIMARY, relief="flat",
                                         padx=12, pady=6, cursor="hand2",
                                         command=self._hapus_foto)
        self.btn_hapus_foto.pack()

        self.lbl_foto_nama = tk.Label(btn_col, text="Format: JPG, PNG, WEBP",
                                       font=("Segoe UI", 8), bg=WHITE, fg=GRAY_TEXT,
                                       justify="left")
        self.lbl_foto_nama.pack(pady=(6, 0))

        # Load preview jika edit dan sudah ada foto
        if self._foto_nama:
            self._show_preview_from_file(os.path.join(IMAGES_DIR, self._foto_nama))

        # ── Tombol aksi ───────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(btn_row, text="Batal", font=("Segoe UI", 10),
                  bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=14, pady=7,
                  cursor="hand2", command=self.destroy).pack(side="left")
        self.btn_simpan = tk.Button(btn_row, text="Simpan", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=7,
                  cursor="hand2", command=self._simpan)
        self.btn_simpan.pack(side="right")

        self.entries["nama"].focus()
        self.bind("<Return>", lambda e: self._simpan())

    # ── Foto helper ───────────────────────────────────────────────────────────
    def _pilih_foto(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Pilih Foto Produk",
            filetypes=[
                ("Gambar", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"),
                ("Semua File", "*.*")
            ]
        )
        if not path:
            return
        self._foto_path = path
        ext  = os.path.splitext(path)[1].lower()
        nama = os.path.basename(path)
        self._foto_nama = nama
        self.lbl_foto_nama.config(text=nama[:28] + ("..." if len(nama) > 28 else ""))
        self._show_preview_from_file(path)

    def _show_preview_from_file(self, path: str):
        if not os.path.isfile(path):
            return
        try:
            img = Image.open(path).convert("RGBA")
            img.thumbnail((96, 96), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._img_ref = photo
            self.lbl_preview.config(image=photo, text="")
            self.lbl_preview.image = photo
        except Exception as e:
            self.lbl_foto_nama.config(text=f"Error: {e}")

    def _hapus_foto(self):
        self._foto_path = None
        self._foto_nama = None
        self._img_ref   = None
        self.lbl_preview.config(image="", text="Belum ada\nfoto")
        self.lbl_foto_nama.config(text="Format: JPG, PNG, WEBP")

    def _salin_foto_ke_images(self, custom_id: str = None) -> str | None:
        """Upload foto ke Google Drive, return File ID. Nama file menggunakan custom_id."""
        if not self._foto_path or not os.path.isfile(self._foto_path):
            return self._foto_nama

        try:
            service = get_drive_service()
            if not service:
                raise Exception("Drive service not initialized")

            # Resize dulu secara lokal agar upload ringan
            # Gunakan unique temp filename untuk menghindari WinError 32
            ext = os.path.splitext(self._foto_path)[1].lower() or ".jpg"
            temp_name = f"temp_upd_{int(time.time()*1000)}{ext}"
            temp_path = os.path.join(IMAGES_DIR, temp_name)
            
            with Image.open(self._foto_path) as img:
                img_proc = img.convert("RGB")
                img_proc.thumbnail((800, 800), Image.LANCZOS)
                img_proc.save(temp_path, quality=85)
            
            # Gunakan custom_id jika ada, jika tidak gunakan timestamp
            nama_file = f"{custom_id or int(time.time())}{ext}"
            
            # Metadata untuk GDrive
            file_metadata = {
                'name': nama_file,
                'parents': [DRIVE_FOLDER_ID]
            }
            
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(temp_path, mimetype='image/jpeg', resumable=True)
            
            # Upload
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            gdrive_id = file.get('id')
            
            # Hapus file sementara dengan pengamanan
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass # Abaikan jika masih terkunci, akan dibersihkan nanti
            
            # Simpan juga ke folder images lokal sebagai cache
            final_local_path = os.path.join(IMAGES_DIR, f"{gdrive_id}.png")
            with Image.open(self._foto_path) as img:
                img_cache = img.convert("RGBA")
                img_cache.save(final_local_path)
                
            return gdrive_id
        except Exception as e:
            print(f"Error upload Google Drive: {e}")
            return self._foto_nama


    # ── Simpan ────────────────────────────────────────────────────────────────
    def _simpan(self):
        # Pastikan harga sudah di-×1000 sebelum simpan
        _apply_harga_x1000(self.entries["harga"], self.lbl_harga_preview)

        nama  = self.entries["nama"].get().strip()
        harga = self.entries["harga"].get().strip()
        stok  = self.entries["stok"].get().strip()

        if not nama:
            messagebox.showwarning("Validasi", "Nama barang tidak boleh kosong!", parent=self)
            return
        try:
            harga_val = float(harga) if harga else 0.0
            stok_val  = int(stok)    if stok  else 0
            if harga_val < 0 or stok_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validasi", "Harga dan stok harus angka positif!", parent=self)
            return

        # Disable button agar tidak double klik
        self.btn_simpan.config(state="disabled", text="Proses...")
        
        def worker():
            try:
                db = get_db()
                
                if self.mode == "tambah":
                    # Generate ID dulu agar bisa dipakai buat nama file di GDrive
                    doc_ref = db.collection('barang').document()
                    product_id = doc_ref.id
                    
                    # Salin foto dengan penamaan ID
                    foto_file = self._salin_foto_ke_images(custom_id=product_id)
                    
                    doc_ref.set({
                        "nama_barang": nama,
                        "harga_barang": harga_val,
                        "stok": stok_val,
                        "foto": foto_file
                    })
                    self.after(0, lambda: self._on_success("Barang berhasil ditambahkan!"))
                else:
                    product_id = self.data["id_barang"]
                    # Salin foto dengan penamaan ID
                    foto_file = self._salin_foto_ke_images(custom_id=product_id)
                    
                    db.collection('barang').document(product_id).update({
                        "nama_barang": nama,
                        "harga_barang": harga_val,
                        "stok": stok_val,
                        "foto": foto_file
                    })
                    self.after(0, lambda: self._on_success("Barang berhasil diperbarui!"))
            except Exception as e:
                self.after(0, lambda ex=e: self._on_error(ex))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, msg):
        messagebox.showinfo("Berhasil", msg, parent=self)
        self.panel.refresh()
        self.destroy()

    def _on_error(self, err):
        messagebox.showerror("Error DB", str(err), parent=self)
        # Re-enable button
        self.btn_simpan.config(state="normal", text="Simpan")

class UpdateCepatForm(tk.Toplevel):
    def __init__(self, panel: BarangPanel, id_barang: str = None):
        super().__init__(panel)
        self.panel = panel
        self.target_id = id_barang
        self.all_barang = []
        self._foto_path = None
        self._foto_nama = None
        self._img_ref = None
        
        self.title("Update Cepat Stok & Foto")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.transient(panel)
        self._center(450, 520)
        
        # Gunakan data yang sudah ada di panel agar tidak membekukan UI (stream DB lambat)
        self.all_barang = list(self.panel.all_data)
        
        self._build()
        
        if self.target_id:
            self._preselect_target()
            
        self.grab_set()

    def _preselect_target(self):
        for i, b in enumerate(self.all_barang):
            if b["id_barang"] == self.target_id:
                self.combo.current(i)
                self._on_select_barang(None)
                break

    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _load_barang(self):
        """Metode ini sudah tidak dipanggil di __init__ karena lambat."""
        pass

    def _build(self):
        hdr = tk.Frame(self, bg="#FF8F00", height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Update Cepat (Stok & Foto)", font=("Segoe UI", 12, "bold"), bg="#FF8F00", fg=WHITE).pack(expand=True)

        body = tk.Frame(self, bg=WHITE, padx=20, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Pilih Barang", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w")
        self.combo = ttk.Combobox(body, font=("Segoe UI", 11), state="readonly")
        
        self.combo["values"] = [f"[{b['id_barang']}] {b['nama_barang']}" for b in self.all_barang]
        self.combo.pack(fill="x", pady=(2, 15), ipady=5)
        self.combo.bind("<<ComboboxSelected>>", self._on_select_barang)

        tk.Label(body, text="Tambah Stok (opsional)", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w")
        vcmd_uc = _make_digit_validator(self)
        self.ent_stok = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                                  bg=LIGHT_GRAY, validate="key", validatecommand=vcmd_uc)
        self.ent_stok.pack(fill="x", pady=(2, 15), ipady=7)

        tk.Label(body, text="Update Foto", font=("Segoe UI", 10, "bold"), bg=WHITE).pack(anchor="w", pady=(0, 4))

        foto_row = tk.Frame(body, bg=WHITE)
        foto_row.pack(fill="x", pady=(0, 15))

        self.preview_frame = tk.Frame(foto_row, bg=LIGHT_GRAY, width=100, height=100, relief="solid", bd=1)
        self.preview_frame.pack(side="left")
        self.preview_frame.pack_propagate(False)

        self.lbl_preview = tk.Label(self.preview_frame, text="Belum ada\nfoto", font=("Segoe UI", 8), bg=LIGHT_GRAY, fg=GRAY_TEXT, justify="center")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        btn_col = tk.Frame(foto_row, bg=WHITE)
        btn_col.pack(side="left", padx=12, fill="y")
        tk.Button(btn_col, text="Pilih Foto", font=("Segoe UI", 9, "bold"), bg="#1565C0", fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2", command=self._pilih_foto).pack(pady=(8, 6))
        self.lbl_foto_nama = tk.Label(btn_col, text="", font=("Segoe UI", 8), bg=WHITE, fg=GRAY_TEXT, justify="left")
        self.lbl_foto_nama.pack(pady=(6, 0))

        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x", pady=(10, 0))
        tk.Button(btn_row, text="Batal", font=("Segoe UI", 10), bg=LIGHT_GRAY, fg=DARK_TEXT, relief="flat", padx=14, pady=7, cursor="hand2", command=self.destroy).pack(side="left")
        self.btn_simpan = tk.Button(btn_row, text="Simpan Update", font=("Segoe UI", 10, "bold"), bg=ACCENT_G, fg=WHITE, relief="flat", padx=14, pady=7, cursor="hand2", command=self._simpan)
        self.btn_simpan.pack(side="right")

    def _on_select_barang(self, _):
        idx = self.combo.current()
        if idx >= 0:
            b = self.all_barang[idx]
            self._foto_nama = b.get("foto")
            self._foto_path = None
            if self._foto_nama:
                # Coba lokal dulu
                local_p = os.path.join(IMAGES_DIR, f"{self._foto_nama}.png")
                if os.path.exists(local_p):
                    self._show_preview_from_file(local_p)
                else:
                    # Jika tidak ada, coba dari API secara async
                    self._show_preview_from_file(f"{API_BASE_URL}/images/{self._foto_nama}")
            else:
                self.lbl_preview.config(image="", text="Belum ada\nfoto")
                self.lbl_foto_nama.config(text="Tidak ada foto.")

    def _pilih_foto(self):
        path = filedialog.askopenfilename(parent=self, title="Pilih Foto Baru", filetypes=[("Gambar", "*.jpg *.jpeg *.png *.webp *.bmp *.gif")])
        if not path: return
        self._foto_path = path
        nama = os.path.basename(path)
        self.lbl_foto_nama.config(text=nama)
        self._show_preview_from_file(path)

    def _show_preview_from_file(self, path: str):
        def _task():
            try:
                if path.startswith("http"):
                    res = requests.get(path, stream=True, timeout=5)
                    img = Image.open(res.raw).convert("RGBA")
                else:
                    if not os.path.isfile(path): return
                    img = Image.open(path).convert("RGBA")
                
                img.thumbnail((96, 96), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: self._update_preview_ui(photo))
            except Exception as e:
                print(f"Preview error: {e}")
        
        threading.Thread(target=_task, daemon=True).start()

    def _update_preview_ui(self, photo):
        self._img_ref = photo
        self.lbl_preview.config(image=photo, text="")
        self.lbl_preview.image = photo

    def _simpan(self):
        idx = self.combo.current()
        if idx < 0:
            messagebox.showwarning("Validasi", "Pilih barang terlebih dahulu!", parent=self)
            return

        b = self.all_barang[idx]
        id_b = b["id_barang"]
        
        tambah_stok = self.ent_stok.get().strip()
        stok_val = 0
        if tambah_stok:
            if not tambah_stok.isdigit() or int(tambah_stok) <= 0:
                messagebox.showwarning("Validasi", "Tambah stok harus angka positif!", parent=self)
                return
            stok_val = int(tambah_stok)

        # Disable button
        self.btn_simpan.config(state="disabled", text="Updating...")

        def worker():
            try:
                new_foto = b.get("foto")
                if self._foto_path and os.path.isfile(self._foto_path):
                    service = get_drive_service()
                    if not service: raise Exception("Drive service error")

                    ext = os.path.splitext(self._foto_path)[1].lower() or ".jpg"
                    nama_file = f"update_{id_b}_{int(time.time())}{ext}"
                    
                    temp_name = f"temp_upd_fast_{int(time.time()*1000)}{ext}"
                    temp_path = os.path.join(IMAGES_DIR, temp_name)
                    with Image.open(self._foto_path) as img:
                        img_proc = img.convert("RGB")
                        img_proc.thumbnail((800, 800), Image.LANCZOS)
                        img_proc.save(temp_path, quality=85)
                    
                    # Upload ke Google Drive
                    file_metadata = {'name': nama_file, 'parents': [DRIVE_FOLDER_ID]}
                    from googleapiclient.http import MediaFileUpload
                    media = MediaFileUpload(temp_path, mimetype='image/jpeg', resumable=True)
                    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    
                    new_foto = file.get('id')
                    try:
                        if os.path.exists(temp_path): os.remove(temp_path)
                    except: pass
                    
                    # Simpan cache lokal
                    with Image.open(self._foto_path) as img:
                        img.convert("RGBA").save(os.path.join(IMAGES_DIR, f"{new_foto}.png"))

                from firebase_admin import firestore
                db = get_db()
                update_data = {}
                if new_foto:
                    update_data["foto"] = new_foto
                if stok_val > 0:
                    update_data["stok"] = firestore.Increment(stok_val)
                    
                if update_data:
                    db.collection('barang').document(id_b).update(update_data)
                
                self.after(0, self._on_success)
            except Exception as e:
                self.after(0, lambda ex=e: self._on_error(ex))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self):
        messagebox.showinfo("Berhasil", "Data berhasil diupdate!", parent=self)
        self.panel.refresh()
        self.destroy()

    def _on_error(self, err):
        messagebox.showerror("Error DB", str(err), parent=self)
        self.btn_simpan.config(state="normal", text="Simpan Update")
