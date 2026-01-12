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
BASE_URL = "https://sorgu-bot.onrender.com" # Render adresin
app = FastAPI()

# Veritabanı başlangıç kontrolü
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
@app.get("/")
def home():
    return {"durum": "aktif", "mesaj": "API Calisiyor. Lütfen /api/sorgu?tc=XXXXXXXXXXX seklinde sorgu yapın."}

@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        if tc and tc in db:
            return {"durum": "basarili", "kayit": db[tc]}
        return {"durum": "hata", "mesaj": "Kayit bulunamadi"}
    except:
        return {"durum": "hata"}

# --- AKILLI AYIKLAYICI ---
def akilli_temizle(metin):
    sonuclar = {}
    # Hem süslü blokları hem de düz JSON yapılarını yakalar
    bloklar = re.split(r'(?:T\.C|TCKN|TC)[:\s]*', metin)
    for blok in bloklar:
        if not blok.strip(): continue
        tc = re.search(r'(\d{11})', blok)
        ad = re.search(r'(?:ADI|Adi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        soyad = re.search(r'(?:SOYADI|Soyadi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        if tc:
            tckn = tc.group(1)
            sonuclar[tckn] = {
                "TCKN": tckn,
                "Adi": ad.group(1).strip() if ad else "-",
                "Soyadi": soyad.group(1).strip() if soyad else "-"
            }
    return sonuclar

# --- BOT ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    status = await update.message.reply_text("🔬 Veriler ayıklanıyor...")
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')
        temiz_veri = akilli_temle(metin) if "ADI" in metin else json.loads(metin)
        if isinstance(temiz_veri, dict):
            # Eğer veri zaten düz JSON ise key'leri TCKN yapalım
            if "TCKN" in temiz_veri: temiz_veri = {temiz_veri["TCKN"]: temiz_veri}
            veriyi_kaydet(temiz_veri)
            sample_tc = list(temiz_veri.keys())[0]
            await status.edit_text(f"✅ Başarılı!\n🔗 API: `{BASE_URL}/api/sorgu?tc={sample_tc}`")
    except Exception as e:
        await status.edit_text(f"❌ Hata: {str(e)}")

async def main():
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000), daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
