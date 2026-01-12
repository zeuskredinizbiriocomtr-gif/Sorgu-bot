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
DB_FILE = "veritabxxxani.json"
BASE_URL = "https://sorgu-bot.onrender.com" 
app = FastAPI()

# Başlangıçta veritabanı dosyası yoksa boş oluşturur
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

# --- ANA SAYFA (TÜM VERİLERİ JSON OLARAK GÖSTERİR) ---
@app.get("/")
async def tum_verileri_listele():
    """Tarayıcıdan girdiğinizde tüm yüklenen verileri JSON olarak gösterir."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        return db
    except Exception as e:
        return {"hata": f"Veri okunamadi: {str(e)}"}

# --- TEKİL SORGULAMA ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None, gsm: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        aranan = str(tc) if tc else str(gsm)
        if aranan in db:
            return {"durum": "basarili", "kayit": db[aranan]}
        return {"durum": "hata", "mesaj": "Kayit bulunamadi"}
    except:
        return {"durum": "hata"}

# --- VERİ AYIKLAMA FONKSİYONU ---
def veri_ayikla(metin):
    sonuclar = {}
    satirlar = metin.splitlines()
    for satir in satirlar:
        tc = re.search(r'(\d{11})', satir)
        gsm = re.search(r'(5\d{9})', satir)
        ad = re.search(r'(?:ADI|Adi|Ad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        soyad = re.search(r'(?:SOYADI|Soyadi|Soyad)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', satir)
        
        # TC yoksa GSM'i anahtar yapar
        key = tc.group(1) if tc else (gsm.group(1) if gsm else None)
        if key:
            sonuclar[str(key)] = {
                "TC": tc.group(1) if tc else "-",
                "GSM": gsm.group(1) if gsm else "-",
                "AD": ad.group(1).strip() if ad else "-",
                "SOYAD": soyad.group(1).strip() if soyad else "-"
            }
    return sonuclar

# --- BOT MESAJ İŞLEME ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    
    bilgi = await update.message.reply_text("📥 Dosya okunuyor ve API'ye aktarılıyor...")
    
    try:
        tg_file = await context.bot.get_file(doc.file_id)
        byte_data = await tg_file.download_as_bytearray()
        metin = byte_data.decode('utf-8', errors='ignore')
        
        temiz_veri = veri_ayikla(metin)
        
        if temiz_veri:
            veriyi_kaydet(temiz_veri)
            await bilgi.edit_text(
                f"✅ **Dosya Başarıyla İşlendi!**\n\n"
                f"📊 Eklenen Kayıt: {len(temiz_veri)}\n"
                f"🌐 **Tüm Verileri Gör (JSON):**\n{BASE_URL}"
            )
        else:
            await bilgi.edit_text("❌ Dosyada geçerli TC veya GSM formatı bulunamadı.")
            
    except Exception as e:
        await bilgi.edit_text(f"❌ İşlem sırasında hata: {str(e)}")

async def main():
    # Sunucu Başlat
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    
    # Bot Başlat
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
