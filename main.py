import json
import os
import threading
import uvicorn
import uuid
from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8588597588:AAHqt9Uywb1C0ovMlS0_7-ehziHw1GOCqeE"
DB_FILE = "butun_veriler.json"
app = FastAPI()

# Veritabanını hazırla
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def veriyi_sakla(benzersiz_id, icerik):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[benzersiz_id] = icerik # Dosyadaki her şeyi olduğu gibi kaydeder
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- EVRENSEL API ---
@app.get("/api/sorgu/{veri_id}")
def api_oku(veri_id: str):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if veri_id in db:
        return {"id": veri_id, "data": db[veri_id]}
    return {"hata": "Veri bulunamadı"}

# --- BOT (DOSYA NE OLURSA OLSUN OKUR) ---
async def dosya_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    status = await update.message.reply_text("📥 Dosya sunucuya yazılıyor...")
    
    try:
        # Dosyayı indir ve metne çevir
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin_icerigi = content.decode('utf-8', errors='ignore')

        # Rastgele kısa bir ID oluştur (Sorgu için)
        sorgu_id = str(uuid.uuid4())[:8]
        
        # Veriyi kaydet
        veriyi_sakla(sorgu_id, metin_icerigi)
        
        base_url = f"https://sorgu-bot.onrender.com/api/sorgu/{sorgu_id}"
        await status.edit_text(
            f"✅ Dosya sisteme işlendi!\n\n"
            f"🔗 **API Erişim Linki:**\n`{base_url}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await status.edit_text(f"❌ Hata oluştu: {str(e)}")

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Herhangi bir .txt veya dosya gönder, API yapayım!")))
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_al))
    application.run_polling()
