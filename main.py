import json
import os
import threading
import asyncio
import uvicorn
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8124126646:AAFZngD3nT76FLPQzP1cXDaGyi1CLEnjUkA"
DB_FILE = "veritabani.json"
app = FastAPI()

# Veritabanı dosyasını hazırla
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_toplu_kaydet(yeni_veriler):
    with open(DB_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.update(yeni_veriler) # Mevcut verilerin üzerine ekler
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()

# --- GERÇEK API (DIŞ ERİŞİM) ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if tc in db:
        return {"durum": "basarili", "kayit": db[tc]}
    return {"durum": "hata", "mesaj": "Veri bulunamadi"}

# --- TELEGRAM BOT (DOSYA YÜKLEME) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 **Toplu Veri Yükleme Botu**\n\n"
        "İçinde veri olan bir `.txt` dosyası gönderin.\n"
        "Format her satırda şu şekilde olmalı:\n"
        "`TC,GSM,AD,SOYAD,ADRES`"
    )

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.txt'):
        return await update.message.reply_text("❌ Lütfen sadece `.txt` uzantılı dosya gönderin.")

    await update.message.reply_text("⏳ Dosya okunuyor ve API'ye aktarılıyor...")
    
    # Dosyayı indir
    yeni_dosya = await context.bot.get_file(doc.file_id)
    dosya_icerik = await yeni_dosya.download_as_bytearray()
    metin = dosya_icerik.decode('utf-8')

    yeni_kayitlar = {}
    hatali_satirlar = 0

    for satir in metin.split('\n'):
        parcalar = satir.strip().split(',') # Virgül ile ayrılmış veri bekler
        if len(parcalar) >= 4:
            tc = parcalar[0]
            yeni_kayitlar[tc] = {
                "gsm": parcalar[1],
                "ad": parcalar[2],
                "soyad": parcalar[3],
                "adres": parcalar[4] if len(parcalar) > 4 else "Bilinmiyor"
            }
        else:
            if satir.strip(): hatali_satirlar += 1

    veriyi_toplu_kaydet(yeni_kayitlar)
    
    ana_link = f"https://{context.bot.username}.onrender.com/api/sorgu?tc="
    await update.message.reply_text(
        f"✅ İşlem Tamamlandı!\n"
        f"📊 Yüklenen Kayıt: {len(yeni_kayitlar)}\n"
        f"⚠️ Hatalı Satır: {hatali_satirlar}\n\n"
        f"🔗 API Örnek Link:\n`{ana_link}{list(yeni_kayitlar.keys())[0]}`",
        parse_mode="Markdown"
    )

# --- BAŞLATICI ---
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

async def main():
    threading.Thread(target=run_api, daemon=True).start()
    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    # Dosya (Belge) gönderildiğinde çalışacak handler
    bot.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    await bot.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
