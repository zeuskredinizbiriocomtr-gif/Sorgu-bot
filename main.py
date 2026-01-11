import json
import os
import threading
import uvicorn
import asyncio
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8124126646:AAFZngD3nT76FLPQzP1cXDaGyi1CLEnjUkA" # Kendi tokenini buraya koy
DB_FILE = "veritabani.json"
app = FastAPI()

# Veritabanı dosyasını kontrol et ve oluştur
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_toplu_kaydet(yeni_veriler):
    try:
        # Mevcut verileri oku
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
            
        # Yeni verileri üzerine ekle
        data.update(yeni_veriler)
        
        # Geri yaz
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Veritabanı yazma hatası: {e}")
        return False

# --- GERÇEK API (DIŞ ERİŞİM) ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        if tc in db:
            return {"durum": "basarili", "kayit": db[tc]}
        return {"durum": "hata", "mesaj": "Veri bulunamadi"}
    except:
        return {"durum": "hata", "mesaj": "Sunucu veri okuyamiyor"}

# --- TELEGRAM BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **API Veri Sistemi Aktif!**\n\n"
        "İçinde veri olan bir `.txt` dosyası gönderin.\n"
        "Format: `TC,GSM,AD,SOYAD,ADRES` (Virgülle ayrılmış)"
    )

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        return await update.message.reply_text("❌ Lütfen sadece `.txt` dosyası gönderin.")

    status_msg = await update.message.reply_text("⏳ Dosya indiriliyor ve API'ye aktarılıyor...")
    
    try:
        # Dosyayı indir
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')

        yeni_kayitlar = {}
        for satir in metin.splitlines():
            if not satir.strip(): continue
            parcalar = satir.strip().split(',')
            if len(parcalar) >= 4:
                tc = parcalar[0].strip()
                yeni_kayitlar[tc] = {
                    "gsm": parcalar[1].strip(),
                    "ad": parcalar[2].strip(),
                    "soyad": parcalar[3].strip(),
                    "adres": parcalar[4].strip() if len(parcalar) > 4 else "Belirtilmemiş"
                }

        if yeni_kayitlar:
            # Senkron kaydetme işlemini bir thread'e taşıyoruz ki bot donmasın
            success = await asyncio.to_thread(veriyi_toplu_kaydet, yeni_kayitlar)
            
            if success:
                # Render URL'ni otomatik bulmaya çalışalım (yoksa manuel yazabilirsin)
                base_url = f"https://sorgu-bot.onrender.com/api/sorgu?tc="
                sample_tc = list(yeni_kayitlar.keys())[0]
                await status_msg.edit_text(
                    f"✅ **İşlem Başarılı!**\n"
                    f"📊 Yüklenen Kayıt: {len(yeni_kayitlar)}\n\n"
                    f"🔗 API Linkiniz:\n`{base_url}{sample_tc}`",
                    parse_mode="Markdown"
                )
            else:
                await status_msg.edit_text("❌ Veritabanına yazılırken bir hata oluştu.")
        else:
            await status_msg.edit_text("⚠️ Dosya okundu ama uygun formatta veri bulunamadı. Format: `TC,GSM,AD,SOYAD,ADRES` olmalı.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Kritik Hata: {str(e)}")

# --- ÇALIŞTIRMA SİSTEMİ ---
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    # API Sunucusunu arka planda başlat
    threading.Thread(target=run_api, daemon=True).start()

    # Botu ana döngüde başlat
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    print("🤖 Bot ve API hazır...")
    application.run_polling()
