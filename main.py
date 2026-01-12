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
BASE_URL = "https://sorgu-bot.onrender.com" # Burayı Render adresinle aynı yap
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
        print(f"Veri Kayıt Hatası: {e}")
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
    await update.message.reply_text(
        "💎 **Sistem Aktif!**\n\n"
        "Lütfen sisteme eklemek istediğiniz `.txt` dosyasını gönderin. "
        "Veriler otomatik temizlenip API formatına getirilecektir."
    )

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        return
    
    status = await update.message.reply_text("📥 Dosya okunuyor ve API havuzuna işleniyor...")
    
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')

        temiz_kayitlar = {}
        for satir in metin.splitlines():
            if not satir.strip(): continue
            
            # Ayraçları (virgül, noktalı virgül, tab) standardize et
            p = satir.replace(';', ',').replace('\t', ',').split(',')
            
            if len(p) >= 1:
                tc = p[0].strip()
                # Verileri düzgün formatta sözlüğe ekle
                temiz_kayitlar[tc] = {
                    "gsm": p[1].strip() if len(p) > 1 else "-",
                    "ad": p[2].strip() if len(p) > 2 else "-",
                    "soyad": p[3].strip() if len(p) > 3 else "-"
                }

        if temiz_kayitlar:
            veriyi_kaydet(temiz_kayitlar)
            sample_tc = list(temiz_kayitlar.keys())[0]
            # İşlem biter bitmez linki ver
            await status.edit_text(
                f"✅ **Veri Başarıyla İşlendi!**\n\n"
                f"📊 **Toplam Kayıt:** {len(temiz_kayitlar)}\n"
                f"🔗 **API Linki (Örnek):**\n`{BASE_URL}/api/sorgu?tc={sample_tc}`",
                parse_mode="Markdown"
            )
        else:
            await status.edit_text("❌ Dosya içinde uygun formatta veri bulunamadı.")
            
    except Exception as e:
        await status.edit_text(f"❌ İşlem sırasında bir hata oluştu: {str(e)}")

# --- SİSTEM DÖNGÜLERİ ---
def auto_restart():
    time.sleep(RESTART_INTERVAL)
    os.execv(sys.executable, ['python'] + sys.argv)

async def main():
    # API Sunucusunu başlat (Port 10000)
    threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=10000), daemon=True).start()
    
    # 10 saatlik restart döngüsünü başlat
    threading.Thread(target=auto_restart, daemon=True).start()
    
    # Botu yapılandır
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    # Botu başlat
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Programın kapanmasını engelle
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
        else:
            await status.edit_text("❌ Dosya içinde geçerli veri bulunamadı.")
            
    except Exception as e:
        await status.edit_text(f"❌ İşlem hatası: {str(e)}")

async def klonla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/klon TOKEN`")
    yeni_token = context.args[0]
    asyncio.create_task(bot_baslat(yeni_token))
    await update.message.reply_text(f"✅ Klon bot (`{yeni_token[:8]}...`) aktif edildi!")

async def bot_baslat(token):
    try:
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("klon", klonla))
        application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Bot Hatasi: {e}")

# --- DÖNGÜ VE API BAŞLATICI ---

def auto_restart():
    time.sleep(RESTART_INTERVAL)
    os.execv(sys.executable, ['python'] + sys.argv)

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

async def main():
    threading.Thread(target=run_api, daemon=True).start()
    threading.Thread(target=auto_restart, daemon=True).start()
    await bot_baslat(TOKEN)
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
cept Exception as e:
        print(f"❌ Bot başlatma hatası ({token[:5]}): {e}")

# --- ÇALIŞTIRMA ---

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

async def main():
    # API Sunucusunu başlat
    threading.Thread(target=run_api, daemon=True).start()
    
    # Ana botu başlat
    await bot_baslat(MAIN_TOKEN)
    
    # Programın kapanmaması için sonsuz döngü
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
        "🔹 `/klon TOKEN` : Kendi botunu oluştur.\n"
        "🔹 `.txt` gönder : Veri yükle."
    )

async def klonla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/klon NEW_BOT_TOKEN`建设")
    
    yeni_token = context.args[0]
    await update.message.reply_text(f"⚙️ Bot klonlanıyor... Token: `{yeni_token[:10]}...`", parse_mode="Markdown")

    try:
        # Yeni botu arka planda ayrı bir Python işlemi olarak başlatır
        p = subprocess.Popen([sys.executable, "main.py", yeni_token])
        klon_surecleri[yeni_token] = p.pid
        await update.message.reply_text("✅ Klon bot başarıyla başlatıldı ve ana sunucuya bağlandı!")
    except Exception as e:
        await update.message.reply_text(f"❌ Klonlama hatası: {str(e)}")

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    # ... (Önceki dosya işleme kodlarının aynısı buraya gelecek)
    await update.message.reply_text("✅ Veri ortak havuzuna eklendi.")

# --- BAŞLATICI ---
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    # Eğer komut satırından bir token gelmişse (klon bot ise)
    if len(sys.argv) > 1:
        CURRENT_TOKEN = sys.argv[1]
        print(f"📡 Klon bot çalışıyor... PID: {os.getpid()}")
    else:
        CURRENT_TOKEN = MAIN_TOKEN
        # Sadece ana bot API sunucusunu başlatır
        threading.Thread(target=run_api, daemon=True).start()
        print("👑 Ana Master Bot ve API başlatıldı.")

    # Botu çalıştır
    application = Application.builder().token(CURRENT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("klon", klonla))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    
    application.run_polling()
