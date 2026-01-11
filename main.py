import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = "8379343161:AAHuKHgLU4-BmXLkKhGVF4gLmCJxW77OFZ8" 
TIMEOUT = 30 # Yanıt süresini biraz kısalttık

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Sağlık Kontrolü
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Aktif")

def run_health_check():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

# Görsel Kutu Tasarımı
def format_box(veri):
    if not veri: return "❌ Veri bulunamadı."
    if isinstance(veri, dict) and "hata" in veri: return f"⚠️ {veri['hata']}"
    
    item = veri[0] if isinstance(veri, list) and len(veri) > 0 else veri
    
    msg = "```\n"
    msg += "➡ + Sorgu Başarılı\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    mapping = {
        "tc": "T.C", "ad": "ADI", "soyad": "SOYADI", "gsm": "GSM",
        "dogum_tarihi": "D. TARİHİ", "anne_adi": "ANNE ADI", "baba_adi": "BABA ADI"
    }

    for key, label in mapping.items():
        if key in item and item[key]:
            msg += f"➡ {label}: {item[key]}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "```\n"
    msg += "📉 Kalan Limitiniz: Sınırsız\n"
    msg += "🛒 Market: /market | Ref: /referansim"
    return msg

# Gelişmiş API İstek Motoru
async def api_get(url, params):
    try:
        # User-agent ekleyerek API'nin bizi bot sanıp engellemesini önlüyoruz
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return {"hata": f"API Sunucusu hata verdi (Kod: {response.status_code})"}
    except requests.exceptions.Timeout:
        return {"hata": "API sunucusu çok geç cevap veriyor (Zaman aşımı)."}
    except Exception as e:
        return {"hata": "API sunucusuna bağlanılamıyor. Lütfen IP/Port kontrol edin."}

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "✅ *Sorgu Botu Aktif!*\n\n"
        "🔍 *Komut Listesi:*\n"
        "➡ `/adsoyad AD SOYAD` \n"
        "➡ `/tckn TC` \n"
        "➡ `/gsm NUMARA` \n"
        "➡ `/aile TC` \n\n"
        "📢 *Bilgi:* Sorguları `/komut veri` şeklinde gönderin."
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def gsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/gsm 542...`")
    await update.message.reply_text("🔎 Sorgulanıyor, lütfen bekleyin...")
    res = await api_get("http://45.81.113.22:4014/api/v1/gsm", {"q": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def adsoyad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("❌ Kullanım: `/adsoyad AD SOYAD`")
    res = await api_get("http://45.81.113.22:4014/api/v1/adsoyad", {"ad": context.args[0], "soyad": context.args[1]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

# --- BAŞLATICI ---
if __name__ == "__main__":
    threading.Thread(target=run_health_check, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gsm", gsm))
    app.add_handler(CommandHandler("adsoyad", adsoyad))
    
    app.run_polling()
