import json
import os
import uvicorn
import asyncio
import re
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8588597588:AAHqt9Uywb1C0ovMlS0_7-ehziHw1GOCqeE"
DB_FILE = "veritabanlari.json"
BASE_URL = "https://sorgu-bot.onrender.com" 
app = FastAPI()

# Çoklu veritabanı yapısını başlat
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def dosya_verisini_kaydet(api_ismi, yeni_veriler):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Dosya ismine özel alana veriyi kaydet
        data[api_ismi] = yeni_veriler
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# --- DOSYAYA ÖZEL API SAYFASI (Google'da Tüm Dosya İçeriğini Gösterir) ---
@app.get("/api/{api_ismi}")
async def dosyayi_gor(api_ismi: str):
    """Örn: /api/tcgsm -> Bu dosyadaki tüm JSON verilerini gösterir."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        return db.get(api_ismi, {"hata": "Bu isimde bir dosya API'si bulunamadı"})
    except:
        return {"hata": "Veri okunamadı"}

# --- DOSYAYA ÖZEL SORGULAMA ---
@app.get("/api/{api_ismi}/sorgu")
def api_sorgu(api_ismi: str, tc: str = None, gsm: str = None):
    """Örn: /api/tcgsm/sorgu?tc=123..."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        dosya_verisi = db.get(api_ismi, {})
        aranan = str(tc) if tc else str(gsm)
        
        if aranan in dosya_verisi:
            return {"durum": "basarili", "kayit": dosya_verisi[aranan]}
        return {"durum": "hata", "mesaj": "Kayit bulunamadi"}
    except:
        return {"durum": "hata"}

# --- VERİ AYIKLAYICI ---
def ayikla(metin):
    sonuclar = {}
    satirlar = metin.splitlines()
    for satir in satirlar:
        tc = re.search(r'(\d{11})', satir)
        gsm = re.search(r'(5\d{9})', satir)
        ad = re.search(r'(?:ADI|Adi|Ad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        soyad = re.search(r'(?:SOYADI|Soyadi|Soyad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        
        key = tc.group(1) if tc else (gsm.group(1) if gsm else None)
        if key:
            sonuclar[str(key)] = {
                "TC": tc.group(1) if tc else "-",
                "GSM": gsm.group(1) if gsm else "-",
                "AD": ad.group(1).strip() if ad else "-",
                "SOYAD": soyad.group(1).strip() if soyad else "-"
            }
    return sonuclar

# --- BOT ---
async def dosya_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    
    # Dosya adından .txt kısmını atıp API ismi yapıyoruz
    api_ismi = doc.file_name.replace(".txt", "").replace(" ", "_").lower()
    msg = await update.message.reply_text(f"🚀 `{api_ismi}` için özel API hazırlanıyor...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')
        
        temiz_veri = ayikla(metin)
        
        if temiz_veri:
            dosya_verisini_kaydet(api_ismi, temiz_veri)
            await msg.edit_text(
                f"✅ **Özel API Oluşturuldu!**\n\n"
                f"📁 Dosya: `{doc.file_name}`\n"
                f"📊 Kayıt: {len(temiz_veri)}\n\n"
                f"🔗 **Tüm Verileri Gör (JSON):**\n{BASE_URL}/api/{api_ismi}\n\n"
                f"🔍 **Sorgu API Linki:**\n`{BASE_URL}/api/{api_ismi}/sorgu?tc=...`",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text("❌ Dosyada veri bulunamadı.")
    except Exception as e:
        await msg.edit_text(f"❌ Hata: {str(e)}")

async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_al))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
