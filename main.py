import json
import os
import threading
import uvicorn
import asyncio
import sys
import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- AYARLAR ---
TOKEN = "8089422686:AAFxaI4pBWZCoRtPbEKmWTPaEJ7lEvfQEZA"
DB_FILE = "veritabani.json"
BASE_URL = "https://sorgu-bot.onrender.com" 
app = FastAPI()

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

# --- WEB ARAYÜZÜ (Verilerin Güzel Görünmesi İçin) ---
@app.get("/", response_class=HTMLResponse)
async def index():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        rows = ""
        for tc, info in db.items():
            rows += f"<tr><td>{tc}</td><td>{info.get('Adi','-')}</td><td>{info.get('Soyadi','-')}</td><td>{info.get('AnneAdi','-')}</td><td>{info.get('BabaAdi','-')}</td></tr>"
        
        html_content = f"""
        <html>
            <head>
                <title>Veri Paneli</title>
                <style>
                    body {{ font-family: sans-serif; background: #f4f4f9; padding: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; background: white; }}
                    th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
                    th {{ background-color: #007bff; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h2>📊 Sistemdeki Kayıtlar ({len(db)})</h2>
                <table>
                    <tr><th>TCKN</th><th>Ad</th><th>Soyad</th><th>Anne Adı</th><th>Baba Adı</th></tr>
                    {rows}
                </table>
            </body>
        </html>
        """
        return html_content
    except:
        return "<h3>Henüz veri yüklenmedi.</h3>"

@app.get("/api/sorgu")
def api_sorgu(tc: str = None):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    if tc in db:
        return {"durum": "basarili", "kayit": db[tc]}
    return {"durum": "hata", "mesaj": "Kayit bulunamadi"}

# --- AKILLI AYIKLAYICI ---
def akilli_ayikla(metin):
    sonuclar = {}
    # Süslü blokları ayırır
    bloklar = re.split(r'(?:T\.C|TCKN|TC)[:\s]*', metin)
    for blok in bloklar:
        if not blok.strip(): continue
        tc = re.search(r'(\d{11})', blok)
        ad = re.search(r'(?:ADI|Adi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        soyad = re.search(r'(?:SOYADI|Soyadi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        anne = re.search(r'(?:ANNE ADI|AnneAdi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        baba = re.search(r'(?:BABA ADI|BabaAdi)[:\s]*([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)', blok)
        
        if tc:
            tckn = tc.group(1)
            sonuclar[tckn] = {
                "TCKN": tckn,
                "Adi": ad.group(1).strip() if ad else "-",
                "Soyadi": soyad.group(1).strip() if soyad else "-",
                "AnneAdi": anne.group(1).strip() if anne else "-",
                "BabaAdi": baba.group(1).strip() if baba else "-"
            }
    return sonuclar

# --- BOT İŞLEMLERİ ---
async def dosya_isle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.txt'): return
    status = await update.message.reply_text("📥 İşleniyor...")
    try:
        file = await context.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        metin = content.decode('utf-8', errors='ignore')
        
        # Karmaşık formatı JSON'a çevir
        temiz_veri = akilli_ayikla(metin)
        
        if temiz_veri:
            veriyi_kaydet(temiz_veri)
            await status.edit_text(f"✅ {len(temiz_veri)} Kayıt Yüklendi!\n🌐 Site: {BASE_URL}")
        else:
            await status.edit_text("❌ Geçerli bir veri bulunamadı.")
    except Exception as e:
        await status.edit_text(f"❌ Hata: {str(e)}")

async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=10000)
    server = uvicorn.Server(config)
    loop = asyncio.get_event_loop()
    loop.create_task(server.serve())
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.Document.ALL, dosya_isle))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
