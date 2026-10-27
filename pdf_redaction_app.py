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
        self.geometry("620x680")
        self.resizable(False, False)

        self.secilen_pdf_yolu = None

        # --- ARAYÜZ ELEMANLARI ---
        
        # 1. Başlık
        self.lbl_baslik = ctk.CTkLabel(
            self, 
            text="Hassas Veri Maskeleme & Rol Bazlı Etiketleme", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_baslik.pack(pady=(15, 8))

        # 2. Sürükle - Bırak Alanı (Drop Zone)
        self.drop_frame = ctk.CTkFrame(self, width=560, height=120, corner_radius=12, border_width=2, border_color="#3B8ED0")
        self.drop_frame.pack(pady=8, padx=30)
        self.drop_frame.pack_propagate(False)

        self.lbl_drop = ctk.CTkLabel(
            self.drop_frame, 
            text="📄 PDF Dosyasını Buraya Sürükleyip Bırakın\n(veya tıklayarak seçin)",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_drop.pack(expand=True)

        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.dosya_suruklendi)
        self.drop_frame.bind("<Button-1>", lambda e: self.dosya_sec_diyalog())
        self.lbl_drop.bind("<Button-1>", lambda e: self.dosya_sec_diyalog())

        # 3. Rol & İsim Eşleştirme Alanı
        self.lbl_isimler = ctk.CTkLabel(
            self, 
            text="Kişi/Kurum Eşleştirmeleri (Her satıra 'İsim = [ETİKET]' şeklinde yazın):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_isimler.pack(anchor="w", padx=35, pady=(12, 4))

        self.txt_isimler = ctk.CTkTextbox(self, width=560, height=130, corner_radius=8, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_isimler.pack(padx=30, pady=4)
        
        ornek_sablon = (
            "Ahmet Yılmaz = [DAVACI]\n"
            "Ayşe Yılmaz = [DAVALI]\n"
            "Kaya Lojistik Ltd. Şti. = [DAVALI_SIRKET]\n"
            "Av. Mehmet Demir = [DAVACI_VEKILI]"
        )
        self.txt_isimler.insert("0.0", ornek_sablon)

        # 4. Bilgi Kutusu
        self.lbl_otomatik = ctk.CTkLabel(
            self, 
            text="ℹ️ TCKN, IBAN, Tel, Plaka, E-posta, Dosya No otomatik taranır.\nEşittir konulmayan isimler varsayılan olarak [KİŞİ/KURUM] yapılır.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left"
        )
        self.lbl_otomatik.pack(anchor="w", padx=35, pady=4)

        # 5. İşlem Butonu
        self.btn_islem = ctk.CTkButton(
            self, 
            text="Rolleri Ata ve Kalıcı Olarak Maskele", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self.maskeleme_yap
        )
        self.btn_islem.pack(pady=12, padx=30, fill="x")

        # 6. Durum Metni
        self.lbl_durum = ctk.CTkLabel(self, text="Hazır. Dosya bekleniyor...", font=ctk.CTkFont(size=12))
        self.lbl_durum.pack(pady=(2, 8))

    def dosya_suruklendi(self, event):
        dosya = event.data.strip('{}')
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

        # Kullanıcı girdilerini satır satır ayrıştır
        satirlar = self.txt_isimler.get("0.0", "end").strip().splitlines()
        ozel_eslesmeler = []

        for satir in satirlar:
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue

            if "=" in satir:
                parcalar = satir.split("=", 1)
                isim = parcalar[0].strip()
                etiket = parcalar[1].strip()
            else:
                isim = satir.strip()
                etiket = "[KİŞİ/KURUM]"

            if isim:
                # Küçük, büyük ve baş harf varyasyonlarını eşle
                varyasyonlar = {isim, isim.upper(), isim.lower(), isim.title()}
                for v in varyasyonlar:
                    ozel_eslesmeler.append((v, etiket))

        # Uzun isimlerin önce eşleşmesi için (örn: "Ahmet Yılmaz" varken sadece "Ahmet"i önce yakalamasın)
        ozel_eslesmeler.sort(key=lambda x: len(x[0]), reverse=True)

        desen_haritasi = [
            (r'\b[1-9][0-9]{10}\b', "[TCKN]"),
            (r'\bTR\d{2}[0-9A-Z]{20,24}\b', "[IBAN]"),
            (r'\b(0?5\d{2}[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2})\b', "[TELEFON]"),
            (r'\b\d{2}\s?[A-Z]{1,3}\s?\d{2,4}\b', "[PLAKA]"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[E-POSTA]"),
            (r'(?i)\b(?:sicil\s*(?:no)?|baro\s*sicil)\s*[:.-]?\s*\d{4,6}\b', "[SİCİL_NO]"),
            (r'\b(20\d{2}/\d{1,6})\b', "[DOSYA_NO]")
        ]

        self.lbl_durum.configure(text="İşleniyor, lütfen bekleyin...")
        self.update()

        try:
            doc = fitz.open(self.secilen_pdf_yolu)
            toplam_karartma = 0

            dolgu_rengi = (0.88, 0.88, 0.88)  # Açık gri arka plan
            yazi_rengi = (0.1, 0.1, 0.1)      # Koyu gri yazı

            for sayfa in doc:
                sayfa_metni = sayfa.get_text()

                # 1. Regex Desenlerini Maskele
                for desen, etiket in desen_haritasi:
                    for eslesme in re.finditer(desen, sayfa_metni):
                        alanlar = sayfa.search_for(eslesme.group(0))
                        for alan in alanlar:
                            sayfa.add_redact_annot(
                                alan, 
                                text=etiket, 
                                fill=dolgu_rengi, 
                                text_color=yazi_rengi,
                                fontsize=8
                            )
                            toplam_karartma += 1

                # 2. Özel İsimleri ve Rolleri Maskele
                for isim, etiket in ozel_eslesmeler:
                    alanlar = sayfa.search_for(isim)
                    for alan in alanlar:
                        sayfa.add_redact_annot(
                            alan, 
                            text=etiket, 
                            fill=dolgu_rengi, 
                            text_color=yazi_rengi,
                            fontsize=8
                        )
                        toplam_karartma += 1

                # Kalıcı silme işlemini uygula
                sayfa.apply_redactions()

            dizin, dosya_adi = os.path.split(self.secilen_pdf_yolu)
            ad, uzanti = os.path.splitext(dosya_adi)
            cikis_yolu = os.path.join(dizin, f"{ad}_anonim{uzanti}")

            doc.save(cikis_yolu, garbage=4, deflate=True)
            doc.close()

            self.lbl_durum.configure(text=f"Tamamlandı! {toplam_karartma} veri rol bazlı etiketlendi.")
            messagebox.showinfo(
                "Başarılı", 
                f"İşlem tamamlandı!\nToplam {toplam_karartma} veri başarıyla etiketlendi.\n\nKaydedilen dosya:\n{cikis_yolu}"
            )

        except Exception as e:
            self.lbl_durum.configure(text="Hata oluştu!")
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    app = ModernPdfRedactor()
    app.mainloop()