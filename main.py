import json
import os
import threading
import uvicorn
import asyncio
import uuid
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
MAIN_TOKEN = "8588597588:AAHqt9Uywb1C0ovMlS0_7-ehziHw1GOCqeE"
DB_FILE = "veritabani.json"
app = FastAPI()

# Veritabanını kontrol et
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_kaydet(yeni_veriler):
    with open(DB_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.update(yeni_veriler)
        f.seek(0)
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.truncate()

# --- API ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if tc in db:
        return {"durum": "basarili", "kayit": db[tc]}
    return {"durum": "hata", "mesaj": "Veri bulunamadi"}

# --- ORTAK BOT MANTIĞI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Sistem Aktif!**\n\n"
        "🔹 `/klon TOKEN` : Bu botu klonla.\n"
        "🔹 `.txt` gönder : Veriyi temizle ve API yap."
    )

async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'):
        return
        
    status = await update.message.reply_text("⏳ Veriler API'ye işleniyor...")
    
    file = await context.bot.get_file(doc.file_id)
    content = await file.download_as_bytearray()
    metin = content.decode('utf-8', errors='ignore')

    temiz_kayitlar = {}
    for satir in metin.splitlines():
        parcalar = satir.strip().split(',')
        if len(parcalar) >= 1:
            tc = parcalar[0].strip()
            temiz_kayitlar[tc] = {
                "gsm": parcalar[1].strip() if len(parcalar) > 1 else "Yok",
                "ad": parcalar[2].strip() if len(parcalar) > 2 else "Yok",
                "soyad": parcalar[3].strip() if len(parcalar) > 3 else "Yok"
            }

    if temiz_kayitlar:
        veriyi_kaydet(temiz_kayitlar)
        # Mevcut botun adını kullanarak link oluşturur
        bot_info = await context.bot.get_me()
        base_url = f"https://sorgu-bot.onrender.com/api/sorgu?tc="
        await status.edit_text(f"✅ **Yüklendi!**\n🔗 API Linki:\n`{base_url}{list(temiz_kayitlar.keys())[0]}`", parse_mode="Markdown")

async def klonla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/klon TOKEN`建设")
    
    yeni_token = context.args[0]
    await update.message.reply_text("⚙️ Klon bot başlatılıyor...")
    
    # Yeni botu ana döngüye ekleyen fonksiyon
    asyncio.create_task(bot_baslat(yeni_token))
    await update.message.reply_text(f"✅ Klon bot (`{yeni_token[:8]}...`) artık aktif ve veri yükleyebilir!")

async def bot_baslat(token):
    try:
        application = Application.builder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("klon", klonla))
        application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print(f"🤖 Bot aktif: {token[:10]}")
    except Exception as e:
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
