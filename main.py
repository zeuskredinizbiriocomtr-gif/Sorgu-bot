import json
import os
import threading
import uvicorn
import asyncio
import sys
import subprocess
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
MAIN_TOKEN = "8588597588:AAHqt9Uywb1C0ovMlS0_7-ehziHw1GOCqeE"
DB_FILE = "veritabani.json"
app = FastAPI()

# Klon botları takip etmek için liste
klon_surecleri = {}

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# --- API ---
@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if tc in db:
        return {"durum": "basarili", "kayit": db[tc]}
    return {"durum": "hata", "mesaj": "Veri bulunamadi"}

# --- BOT FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Master Bot Aktif!**\n\n"
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
