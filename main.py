import json
import os
import threading
import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8124126646:AAFZngD3nT76FLPQzP1cXDaGyi1CLEnjUkA"
DB_FILE = "veritabani.json"
app = FastAPI()

# Veritabanı dosyasını kontrol et ve oluştur
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_toplu_kaydet(yeni_veriler):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(yeni_veriler)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Veritabanı yazma hatası: {e}")

# --- GERÇEK API (DIŞ ERİŞİM) ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if tc in db:
        return {"durum": "basarili", "kayit": db[tc]}
    return {"durum": "hata", "mesaj": "Veri bulunamadi"}

# --- TELEGRAM BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 **Veri API Yükleme Botu Aktif!**\n\n"
        "Bana içinde veri olan bir `.txt` dosyası gönderin.\n"
        "Format (Virgüllü): `TC,GSM,AD,SOYAD,ADRES`"
    )

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.txt'):
        return await update.message.reply_text("❌ Lütfen sadece `.txt` dosyası gönderin.")

    await update.message.reply_text("⏳ Dosya sunucuya işleniyor...")
    
    file = await context.bot.get_file(doc.file_id)
    content = await file.download_as_bytearray()
    metin = content.decode('utf-8')

    yeni_kayitlar = {}
    for satir in metin.split('\n'):
        parcalar = satir.strip().split(',')
        if len(parcalar) >= 4:
            tc = parcalar[0]
            yeni_kayitlar[tc] = {
                "gsm": parcalar[1],
                "ad": parcalar[2],
                "soyad": parcalar[3],
                "adres": parcalar[4] if len(parcalar) > 4 else "Belirtilmemiş"
            }

    veriyi_toplu_kaydet(yeni_kayitlar)
    
    base_url = f"https://sorgu-bot.onrender.com/api/sorgu?tc="
    await update.message.reply_text(
        f"✅ Başarıyla yüklendi!\n"
        f"📊 Toplam Kayıt: {len(yeni_kayitlar)}\n\n"
        f"🔗 Örnek API Linkiniz:\n`{base_url}{list(yeni_kayitlar.keys())[0]}`",
        parse_mode="Markdown"
    )

# --- ÇALIŞTIRMA SİSTEMİ ---
def run_api():
    # Render'da çalışması için portu 10000 yapıyoruz
    uvicorn.run(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    # API'yi ayrı bir kanalda başlat
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Botu ana kanalda başlat
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    print("🤖 Bot ve API başlatılıyor...")
    application.run_polling()
