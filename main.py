import json
import os
import uvicorn
import asyncio
import re
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabanix.json"
BASE_URL = "https://sorgu-bot.onrender.com" 
app = FastAPI()

# Veritabanı dosyasını kontrol et
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_kaydet(yeni_veriler):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(yeni_veriler) # Yeni gelenleri üzerine ekler
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# --- API (Google'dan girince veriyi gösteren yer) ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None, gsm: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        aranan = str(tc) if tc else str(gsm)
        if aranan and aranan in db:
            return {"durum": "basarili", "kayit": db[aranan]}
        return {"durum": "hata", "mesaj": "Kayit bulunamadi"}
    except:
        return {"durum": "hata", "mesaj": "Veritabani okunurken hata oluştu"}

# --- DOSYA AYIKLAYICI ---
def veriyi_temizle(metin):
    sonuclar = {}
    # Satır satır tarayarak TC ve GSM'leri ayıklar
    satirlar = metin.splitlines()
    for satir in satirlar:
        if not satir.strip(): continue
        
        tc_bul = re.search(r'(\d{11})', satir)
        gsm_bul = re.search(r'(5\d{9})', satir)
        ad_bul = re.search(r'(?:ADI|Adi|Ad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        soyad_bul = re.search(r'(?:SOYADI|Soyadi|Soyad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        
        anahtar = tc_bul.group(1) if tc_bul else (gsm_bul.group(1) if gsm_bul else None)
        
        if anahtar:
            sonuclar[str(anahtar)] = {
                "TC": tc_bul.group(1) if tc_bul else "-",
                "GSM": gsm_bul.group(1) if gsm_bul else "-",
                "AD": ad_bul.group(1).strip() if ad_bul else "-",
                "SOYAD": soyad_bul.group(1).strip() if soyad_bul else "-"
            }
    return sonuclar

# --- BOT İŞLEMLERİ ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    
    msg = await update.message.reply_text("⏳ Dosya işleniyor, veriler API'ye aktarılıyor...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        byte_data = await file.download_as_bytearray()
        metin = byte_data.decode('utf-8', errors='ignore')
        
        # Veriyi temizle ve JSON yapısına sok
        temiz_veri = veriyi_temizle(metin)
        
        if temiz_veri:
            veriyi_kaydet(temiz_veri)
            ornek_key = list(temiz_veri.keys())[0]
            param = "tc" if len(ornek_key) == 11 else "gsm"
            
            await msg.edit_text(
                f"✅ **API Güncellendi!**\n\n"
                f"📊 Eklenen Kayıt: {len(temiz_veri)}\n"
                f"🔗 **Google Sorgu Linki:**\n"
                f"`{BASE_URL}/api/sorgu?{param}={ornek_key}`",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text("❌ Dosya içinde geçerli bir veri (TC/GSM) bulunamadı.")
            
    except Exception as e:
        await msg.edit_text(f"❌ Hata: {str(e)}")

async def main():
    # API Sunucusu
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    # Telegram Botu
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
