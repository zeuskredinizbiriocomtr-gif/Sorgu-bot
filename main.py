import json
import os
import threading
import uvicorn
import asyncio
import sys
import re
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabani.json"
BASE_URL = "https://sorgu-bot.onrender.com"
app = FastAPI()

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_kaydet(yeni_veriler):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(yeni_veriler)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# --- API ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        return db.get(tc, {"durum": "hata", "mesaj": "Kayit bulunamadi"})
    except:
        return {"durum": "hata"}

# --- GELİŞMİŞ AYIKLAMA MANTIĞI ---
def akilli_temizleyici(metin):
    """Süslü blokları ve karmaşık metinleri temizleyip JSON yapar."""
    temiz_sonuc = {}
    
    # Blokları ayır (Her T.C: veya TCKN: ile başlayan bölümü yeni bir kayıt sayar)
    kayitlar = re.split(r'(?:T\.C|TCKN|TC)[:\s]*', metin)
    
    for blok in kayitlar:
        if not blok.strip(): continue
        
        # Regex ile anahtar kelimeleri ve yanındaki değerleri yakala
        tc_match = re.search(r'(\d{11})', blok)
        ad_match = re.search(r'(?:ADI|Adi|Ad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        soyad_match = re.search(r'(?:SOYADI|Soyadi|Soyad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        dogum_match = re.search(r'(?:DOĞUM TARİHİ|DogumTarihi|Dogum)[:\s]*([\d\.]+)', blok)
        anne_match = re.search(r'(?:ANNE ADI|AnneAdi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        baba_match = re.search(r'(?:BABA ADI|BabaAdi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        il_match = re.search(r'(?:NUFUS IL|NufusIl)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        ilce_match = re.search(r'(?:NUFUS ILCE|NufusIlce)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)

        if tc_match:
            tckn = tc_match.group(1)
            # Veriyi temizle ve objeye dönüştür
            temiz_sonuc[tckn] = {
                "TCKN": tckn,
                "Adi": ad_match.group(1).strip() if ad_match else "-",
                "Soyadi": soyad_match.group(1).strip() if soyad_match else "-",
                "DogumTarihi": dogum_match.group(1).strip() if dogum_match else "-",
                "AnneAdi": anne_match.group(1).strip() if anne_match else "-",
                "BabaAdi": baba_match.group(1).strip() if baba_match else "-",
                "NufusIl": il_match.group(1).strip() if il_match else "-",
                "NufusIlce": ilce_match.group(1).strip() if ilce_match else "-"
            }
    
    return temiz_sonuc

# --- BOT İŞLEMLERİ ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    
    status = await update.message.reply_text("🔍 Süslü veriler ayıklanıyor ve JSON'a dönüştürülüyor...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')

        # Önce metin halindeki süslü veriyi JSON'a çeviriyoruz
        temizlenmis_json = akilli_temizleyici(metin)

        if temizlenmis_json:
            # Temizlenmiş JSON verisini veritabanına kaydediyoruz
            veriyi_kaydet(temizlenmis_json)
            sample_tc = list(temizlenmis_json.keys())[0]
            
            await status.edit_text(
                f"✅ **Dönüştürme ve Yükleme Tamam!**\n\n"
                f"📦 **İşlem:** Süslü metin blokları temizlendi.\n"
                f"📊 **Kayıt Sayısı:** {len(temizlenmis_json)}\n\n"
                f"🔗 **API Sorgu Linki:**\n`{BASE_URL}/api/sorgu?tc={sample_tc}`",
                parse_mode="Markdown"
            )
        else:
            await status.edit_text("❌ Dosyada geçerli bir obje veya T.C. numarası bulunamadı.")
            
    except Exception as e:
        await status.edit_text(f"❌ Hata oluştu: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 **Veri Ayıklayıcı & API Yükleyici**\n\nSüslü kutu mesajlarını veya karmaşık listeleri içeren .txt dosyasını atın, ben tertemiz JSON yapıp API'ye yükleyeyim.")

async def main():
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000), daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
