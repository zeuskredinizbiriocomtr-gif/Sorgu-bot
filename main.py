import json
import os
import threading
import uvicorn
import asyncio
import sys
import time
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabani.json"
RESTART_INTERVAL = 36000 # 10 Saat
BASE_URL = "https://sorgu-bot.onrender.com" # Render adresini buraya yaz
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
    except Exception as e:
        print(f"Hata: {e}")
        return False

# --- API SUNUCUSU ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        if tc in db:
            return {"durum": "basarili", "kayit": db[tc]}
        return {"durum": "hata", "mesaj": "Kayit bulunamadi"}
    except:
        return {"durum": "hata"}

# --- TELEGRAM BOT MANTIĞI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 **Sorgu API Botu Aktif!**\n\nLütfen sisteme eklemek istediğiniz `.txt` dosyasını gönderin.")

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        return
    
    status = await update.message.reply_text("📥 Dosya işleniyor, lütfen bekleyin...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')

        temiz_kayitlar = {}
        for satir in metin.splitlines():
            if not satir.strip():
                continue
            # Ayraçları (virgül, noktalı virgül, tab) temizle ve parçala
            p = satir.replace(';', ',').replace('\t', ',').split(',')
            
            if len(p) >= 1:
                tc = p[0].strip()
                # Verileri her zaman aynı formatta düzenler
                temiz_kayitlar[tc] = {
                    "gsm": p[1].strip() if len(p) > 1 else "-",
                    "ad": p[2].strip() if len(p) > 2 else "-",
                    "soyad": p[3].strip() if len(p) > 3 else "-"
                }

        if temiz_kayitlar:
            veriyi_kaydet(temiz_kayitlar)
            sample_tc = list(temiz_kayitlar.keys())[0]
            # İşlem biter bitmez direkt API linkini verir
            await status.edit_text(
                f"✅ **Veri Başarıyla Yüklendi!**\n\n"
                f"📊 **Kayıt Sayısı:** {len(temiz_kayitlar)}\n"
                f"🔗 **API Linki (Örnek):**\n`{BASE_URL}/api/sorgu?tc={sample_tc}`",
                parse_mode="Markdown"
            )
        else:
            await status.edit_text("❌ Dosyada geçerli veri bulunamadı.")
            
    except Exception as e:
        await status.edit_text(f"❌ Bir hata oluştu: {str(e)}")

# --- SİSTEM DÖNGÜLERİ ---
def auto_restart():
    time.sleep(RESTART_INTERVAL)
    os.execv(sys.executable, ['python'] + sys.argv)

async def main():
    # API Sunucusunu ayrı kolda başlat
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000), daemon=True).start()
    # Restart döngüsünü başlat
    threading.Thread(target=auto_restart, daemon=True).start()
    
    # Botu başlat
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
