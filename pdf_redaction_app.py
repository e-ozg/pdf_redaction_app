import pymupdf as fitz
import re
import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

# Modern koyu tema görünümü
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ModernPdfRedactor(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.title("Bilirkişi & Arabulucu PDF Maskeleme Aracı")
        self.geometry("580x620")
        self.resizable(False, False)

        self.secilen_pdf_yolu = None

        # --- ARAYÜZ ELEMANLARI ---
        
        # 1. Başlık
        self.lbl_baslik = ctk.CTkLabel(
            self, 
            text="Hassas Veri Maskeleme ve Redaction", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_baslik.pack(pady=(20, 10))

        # 2. Sürükle - Bırak Alanı (Drop Zone)
        self.drop_frame = ctk.CTkFrame(self, width=520, height=140, corner_radius=12, border_width=2, border_color="#3B8ED0")
        self.drop_frame.pack(pady=10, padx=30)
        self.drop_frame.pack_propagate(False)

        self.lbl_drop = ctk.CTkLabel(
            self.drop_frame, 
            text="📄 PDF Dosyasını Buraya Sürükleyip Bırakın\n(veya tıklayarak seçin)",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_drop.pack(expand=True)

        # Sürükle-bırak event tanımları
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.dosya_suruklendi)
        self.drop_frame.bind("<Button-1>", lambda e: self.dosya_sec_diyalog())
        self.lbl_drop.bind("<Button-1>", lambda e: self.dosya_sec_diyalog())

        # 3. Özel İsimler Giriş Alanı
        self.lbl_isimler = ctk.CTkLabel(
            self, 
            text="Kapatılacak Taraf / Şirket / Vekil İsimleri (virgülle ayırın):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_isimler.pack(anchor="w", padx=35, pady=(15, 5))

        self.txt_isimler = ctk.CTkTextbox(self, width=510, height=80, corner_radius=8)
        self.txt_isimler.pack(padx=30, pady=5)
        self.txt_isimler.insert("0.0", "Ahmet Yılmaz, ABC Nakliyat Ltd. Şti., Av. Mehmet Demir")

        # 4. Bilgi Kutusu
        self.lbl_otomatik = ctk.CTkLabel(
            self, 
            text="ℹ️ TCKN, IBAN, Telefon, Plaka, E-posta ve Dosya No otomatik taranır.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_otomatik.pack(pady=5)

        # 5. İşlem Butonu
        self.btn_islem = ctk.CTkButton(
            self, 
            text="Kalıcı Olarak Maskele ve Kaydet", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            command=self.maskeleme_yap
        )
        self.btn_islem.pack(pady=15, padx=30, fill="x")

        # 6. Durum Metni
        self.lbl_durum = ctk.CTkLabel(self, text="Hazır. Dosya bekleniyor...", font=ctk.CTkFont(size=12))
        self.lbl_durum.pack(pady=(5, 10))

    def dosya_suruklendi(self, event):
        dosya = event.data.strip('{}')  # Windows tırnak/süslü parantez temizliği
        if dosya.lower().endswith(".pdf"):
            self.dosya_yukle(dosya)
        else:
            messagebox.showerror("Hata", "Lütfen yalnızca PDF dosyası sürükleyin!")

    def dosya_sec_diyalog(self):
        from tkinter import filedialog
        dosya = filedialog.askopenfilename(filetypes=[("PDF Dosyaları", "*.pdf")])
        if dosya:
            self.dosya_yukle(dosya)

    def dosya_yukle(self, yol):
        self.secilen_pdf_yolu = yol
        dosya_adi = os.path.basename(yol)
        self.lbl_drop.configure(text=f"✅ Yüklendi:\n{dosya_adi}", text_color="#2CC985")
        self.lbl_durum.configure(text=f"Dosya hazır: {dosya_adi}")

    def maskeleme_yap(self):
        if not self.secilen_pdf_yolu:
            messagebox.showwarning("Uyarı", "Lütfen önce bir PDF dosyası bırakın veya seçin!")
            return

        isimler_ham = self.txt_isimler.get("0.0", "end").strip()
        ekstra_isimler = set()
        for i in isimler_ham.split(","):
            ad = i.strip()
            if ad:
                ekstra_isimler.add(ad)
                ekstra_isimler.add(ad.upper())
                ekstra_isimler.add(ad.lower())
                ekstra_isimler.add(ad.title())

        regex_kaliplari = [
            r'\b[1-9][0-9]{10}\b',                                            # TCKN
            r'\bTR\d{2}[0-9A-Z]{20,24}\b',                                    # IBAN
            r'\b(0?5\d{2}[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2})\b', # Telefon
            r'\b\d{2}\s?[A-Z]{1,3}\s?\d{2,4}\b',                             # Plaka
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',         # E-posta
            r'(?i)\b(?:sicil\s*(?:no)?|baro\s*sicil)\s*[:.-]?\s*\d{4,6}\b',  # Sicil No
            r'\b(20\d{2}/\d{1,6})\b'                                         # Dosya No
        ]

        self.lbl_durum.configure(text="İşleniyor, lütfen bekleyin...")
        self.update()

        try:
            doc = fitz.open(self.secilen_pdf_yolu)
            toplam_karartma = 0

            for sayfa in doc:
                sayfa_metni = sayfa.get_text()

                # Regex eşleşmeleri
                for desen in regex_kaliplari:
                    for eslesme in re.finditer(desen, sayfa_metni):
                        alanlar = sayfa.search_for(eslesme.group(0))
                        for alan in alanlar:
                            sayfa.add_redact_annot(alan, fill=(0, 0, 0))
                            toplam_karartma += 1

                # Özel isimler
                for isim in ekstra_isimler:
                    alanlar = sayfa.search_for(isim)
                    for alan in alanlar:
                        sayfa.add_redact_annot(alan, fill=(0, 0, 0))
                        toplam_karartma += 1

                sayfa.apply_redactions()

            dizin, dosya_adi = os.path.split(self.secilen_pdf_yolu)
            ad, uzanti = os.path.splitext(dosya_adi)
            cikis_yolu = os.path.join(dizin, f"{ad}_anonim{uzanti}")

            doc.save(cikis_yolu, garbage=4, deflate=True)
            doc.close()

            self.lbl_durum.configure(text=f"Tamamlandı! {toplam_karartma} veri maskelendi.")
            messagebox.showinfo("Başarılı", f"İşlem tamamlandı!\nToplam {toplam_karartma} hassas veri silindi.\n\nKaydedilen dosya:\n{cikis_yolu}")

        except Exception as e:
            self.lbl_durum.configure(text="Hata oluştu!")
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    app = ModernPdfRedactor()
    app.mainloop()