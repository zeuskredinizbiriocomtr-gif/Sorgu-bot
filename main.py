import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
TOKEN = "8379343161:AAHuKHgLU4-BmXLkKhGVF4gLmCJxW77OFZ8"
TIMEOUT = 60

# Loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- RENDER İÇİN UYUMAZLIK SİSTEMİ (PORT 10000) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Aktif")

def run_health_check():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

# --- FORMATLAMA VE API MOTORU ---
def format_box(veri):
    if not veri: return "❌ Kayıt bulunamadı."
    if isinstance(veri, dict) and "hata" in veri: return f"⚠️ `{veri['hata']}`"
    
    res = veri[0] if isinstance(veri, list) and len(veri) > 0 else veri
    
    msg = "```\n➡ + Sorgu Başarılı\n━━━━━━━━━━━━━━━━━━━━\n"
    mapping = {
        "tc": "T.C", "ad": "ADI", "soyad": "SOYADI",
        "dogum_tarihi": "DOĞUM TARİHİ", "nufus_il": "NÜFUS İL",
        "nufus_ilce": "NÜFUS İLÇE", "anne_adi": "ANNE ADI",
        "anne_tc": "ANNE TC", "baba_adi": "BABA ADI",
        "baba_tc": "BABA TC", "uyruk": "UYRUK", "yas": "YAŞ",
        "adres": "ADRES", "gsm": "GSM"
    }
    for key, label in mapping.items():
        if key in res and res[key]:
            msg += f"➡ {label}: {res[key]}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n```"
    return msg

async def api_get(url, params):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        return response.json()
    except Exception as e:
        return {"hata": f"Bağlantı Hatası: {str(e)}"}

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Render üzerinde aktif!")

async def adsoyad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return await update.message.reply_text("Kullanım: /adsoyad AD SOYAD")
    res = await api_get("http://45.81.113.22:4014/api/v1/adsoyad", {"ad": context.args[0], "soyad": context.args[1]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def tckn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    res = await api_get("http://45.81.113.22:4014/api/v1/tc/adres", {"tc": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def aile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    res = await api_get("http://45.81.113.22:4014/api/v1/aile", {"tc": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def gsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    res = await api_get("http://45.81.113.22:4014/api/v1/gsm", {"q": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    # Health check'i ayrı bir kolda başlat (Render uyumasın diye)
    threading.Thread(target=run_health_check, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adsoyad", adsoyad))
    app.add_handler(CommandHandler("tckn", tckn))
    app.add_handler(CommandHandler("aile", aile))
    app.add_handler(CommandHandler("gsm", gsm))
    
    app.run_polling()
