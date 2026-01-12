import json
import os
import threading
import uvicorn
import asyncio
import sys
import time
import re
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabani.json"
BASE_URL = "https://sorgu-bot.onrender.com" # Burayı kendi Render URL'nle güncelle
app = FastAPI()

# Veritabanı dosyasını oluştur
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_veritabanina_yaz(temiz_json_verisi):
    """Bellekte hazırlanan JSON verisini kalıcı dosyaya yazar."""
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            mevcut_db = json.load(f)
        
        # Yeni temizlenmiş veriyi mevcut veritabanıyla birleştir
        mevcut_db.update(temiz_json_verisi)
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(mevcut_db, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Yazma Hatası: {e}")
        return False

# --- API ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        if tc in db:
            return {"durum": "basarili", "kayit": db[tc]}
        return {"durum": "hata", "mesaj": "Veri bulunamadi"}
    except:
        return {"durum": "hata"}

# --- BOT İŞLEMLERİ ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        return
    
    status = await update.message.reply_text("⚙️ Veriler temizleniyor ve JSON formatına dönüştürülüyor...")
    
    try:
        # 1. Dosyayı indir ve oku
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        ham_metin = content.decode('utf-8', errors='ignore')

        # 2. Veriyi temizle ve JSON formatına (Dictionary) çevir
        islenmis_temiz_veri = {}
        for satir in ham_metin.splitlines():
            if not satir.strip(): continue
            
            # Sembolleri ve gereksiz ayraçları temizle, sadece kelime ve sayıları al
            parcalar = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s]', ' ', satir).split()
            
            tc, gsm, isim_listesi = None, "-", []
            
            for p in parcalar:
                if p.isdigit():
                    if len(p) == 11 and not tc:
                        tc = p # 11 haneli ise TC'dir
                    elif (len(p) == 10 or (len(p) == 11 and p.startswith(('0', '9')))) and gsm == "-":
                        gsm = p # GSM formatına uyuyorsa GSM'dir
                elif len(p) > 1:
                    isim_listesi.append(p.capitalize())

            # Eğer bir TC bulunduysa veriyi JSON yapısına ekle
            if tc:
                islenmis_temiz_veri[tc] = {
                    "gsm": gsm,
                    "ad": isim_listesi[0] if len(isim_listesi) > 0 else "-",
                    "soyad": " ".join(isim_listesi[1:]) if len(isim_listesi) > 1 else "-"
                }

        # 3. Hazırlanan temiz JSON verisini sunucuya yükle
        if islenmis_temiz_veri:
            basarili = veriyi_veritabanina_yaz(islenmis_temiz_veri)
            
            if basarili:
                # 4. Kullanıcıya API linkini gönder
                sample_tc = list(islenmis_temiz_veri.keys())[0]
                await status.edit_text(
                    f"✅ **İşlem Başarılı!**\n\n"
                    f"📝 **Durum:** Karmaşık veriler ayıklandı ve JSON olarak sisteme yüklendi.\n"
                    f"📊 **Yüklenen Kayıt:** {len(islenmis_temiz_veri)}\n\n"
                    f"🔗 **API Sorgu Linki:**\n`{BASE_URL}/api/sorgu?tc={sample_tc}`",
                    parse_mode="Markdown"
                )
            else:
                await status.edit_text("❌ Veriler temizlendi ancak sunucuya yazılamadı.")
        else:
            await status.edit_text("❌ Dosya içinde geçerli bir TC (11 hane) bulunamadı.")
            
    except Exception as e:
        await status.edit_text(f"❌ Kritik Hata: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Selam! Karmaşık verilerini içeren `.txt` dosyasını at, ben senin için JSON yapıp API'ye yükleyeyim.")

async def main():
    # API Sunucusu (FastAPI) başlat
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000), daemon=True).start()
    
    # Botu başlat
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
