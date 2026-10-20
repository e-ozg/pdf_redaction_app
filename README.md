# Bilirkişi & Arabulucu PDF Maskeleme Aracı (Legal PDF Redactor)

Hukuk ve aktüerya süreçlerinde UYAP evraklarındaki kişisel ve hassas verileri (TCKN, IBAN, telefon, plaka vb.) kalıcı olarak maskeleyen (true redaction) modern masaüstü uygulaması.

## Özellikler
- **Sürükle & Bırak (Drag-and-Drop):** PDF dosyalarını doğrudan arayüze bırakarak yükleme.
- **Kalıcı Dijital Karartma (True Redaction):** Hassas veriler yalnızca görsel olarak siyah bantla kapatılmaz; metin katmanı PDF kaynak kodundan kalıcı olarak silinir.
- **Otomatik Tespit (RegEx):** TCKN, IBAN, Telefon, Plaka, E-posta ve Dosya Numaraları otomatik taranır.
- **Özel İsim Desteği:** Taraf, şirket veya vekil isimleri büyük/küçük harf duyarsız olarak maskelenir.

## Kurulum ve Çalıştırma

```bash
pip install -r requirements.txt
python pdf_redaction_app.py