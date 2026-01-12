import json
import os
import threading
import uvicorn
import asyncio
import re
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabani.json"
BASE_URL = "https://gu-bot.onrender.com" 
app = FastAPI()

# Çoklu API yapısı için veritabanını başlat
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"apis": {}}, f)

def api_kaydet(api_id, veri_listesi, dosya_adi):
    """Her dosyayı kendine özel bir ID ile veritabanına kaydeder."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        db["apis"][api_id] = {
            "dosya_adi": dosya_adi,
            "veriler": veri_listesi
        }
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# --- DİNAMİK API SORGULAMA ---
@app.get("/api/{api_id}/sorgu")
def dinamik_sorgu(api_id: str, tc: str = None, gsm: str = None):
    """
    Her dosyanın API linki farklıdır:
    Örn: /api/gsm-dosyasi-id/sorgu?gsm=532...
    Örn: /api/tc-dosyasi-id/sorgu?tc=123...
    """
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    if api_id not in db["apis"]:
        return {"durum": "hata", "mesaj": "Böyle bir API bulunamadı"}
    
    veriler = db["apis"][api_id]["veriler"]
    
    # TC veya GSM ile arama yap
    for kayit in veriler.values():
        if tc and kayit.get("TCKN") == tc:
            return {"durum": "basarili", "kayit": kayit}
        if gsm and kayit.get("GSM") == gsm:
            return {"durum": "basarili", "kayit": kayit}
            
    return {"durum": "hata", "mesaj": "Kayit bulunamadi"}

# --- AKILLI AYIKLAYICI (GSM VE TC DESTEKLİ) ---
def dosya_cozumle(metin):
    sonuclar = {}
    # Blokları ayır
    bloklar = re.split(r'(?:T\.C|TCKN|TC|GSM)[:\s]*', metin)
    
    for blok in bloklar:
        if not blok.strip(): continue
        tc = re.search(r'(\d{11})', blok)
        gsm = re.search(r'(5\d{9})', blok) # 5 ile başlayan 10 haneli GSM
        ad = re.search(r'(?:ADI|Adi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        soyad = re.search(r'(?:SOYADI|Soyadi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        
        anahtar = tc.group(1) if tc else (gsm.group(1) if gsm else None)
        
        if anahtar:
            sonuclar[anahtar] = {
                "TCKN": tc.group(1) if tc else "-",
                "GSM": gsm.group(1) if gsm else "-",
                "Adi": ad.group(1).strip() if ad else "-",
                "Soyadi": soyad.group(1).strip() if soyad else "-"
            }
    return sonuclar

# --- BOT DOSYA İŞLEME ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    
    api_id = str(uuid.uuid4())[:8] # Her dosyaya özel 8 haneli benzersiz ID
    msg = await update.message.reply_text(f"🚀 `{doc.file_name}` işleniyor. Özel API oluşturuluyor...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')
        
        islenmis_veri = dosya_cozumle(metin)
        
        if islenmis_veri:
            api_kaydet(api_id, islenmis_veri, doc.file_name)
            
            # Örnek link oluşturma
            ornek_key = list(islenmis_veri.keys())[0]
            param = "tc" if len(ornek_key) == 11 else "gsm"
            
            await msg.edit_text(
                f"✅ **Dosyaya Özel API Hazır!**\n\n"
                f"📁 **Dosya:** `{doc.file_name}`\n"
                f"🆔 **API ID:** `{api_id}`\n"
                f"📊 **Kayıt:** {len(islenmis_veri)}\n\n"
                f"🔗 **Özel Sorgu Linkin:**\n"
                f"`{BASE_URL}/api/{api_id}/sorgu?{param}={ornek_key}`",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text("❌ Dosya içinde uygun veri formatı bulunamadı.")
            
    except Exception as e:
        await msg.edit_text(f"❌ Hata: {str(e)}")

async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
