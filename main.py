import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- AYARLAR ---
# Buraya @BotFather'dan aldığın GÜNCEL tokeni yapıştır
TOKEN = "8379343161:AAHuKHgLU4-BmXLkKhGVF4gLmCJxW77OFZ8" 
TIMEOUT = 5

# Loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- RENDER CANLI TUTMA SİSTEMİ ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Aktif")

def run_health_check():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

# --- GÖRSEL TASARIM VE API MOTORU ---
def format_box(veri, baslik="Sorgu Sonucu"):
    if not veri:
        return "❌ Aranan kritere uygun veri bulunamadı."
    if isinstance(veri, dict) and "hata" in veri:
        return f"⚠️ `{veri['hata']}`"

    item = veri[0] if isinstance(veri, list) and len(veri) > 0 else veri
    
    msg = "```\n"
    msg += "➡ + Sorgu Başarılı\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    mapping = {
        "tc": "T.C", "ad": "ADI", "soyad": "SOYADI",
        "dogum_tarihi": "DOĞUM TARİHİ", "nufus_il": "NÜFUS İL",
        "nufus_ilce": "NÜFUS İLÇE", "anne_adi": "ANNE ADI",
        "anne_tc": "ANNE TC", "baba_adi": "BABA ADI",
        "baba_tc": "BABA TC", "uyruk": "UYRUK", "yas": "YAŞ",
        "adres": "ADRES", "gsm": "GSM"
    }

    found = False
    for key, label in mapping.items():
        if key in item and item[key]:
            msg += f"➡ {label}: {item[key]}\n"
            found = True
    
    if not found: return "❌ Eşleşen veri bulunamadı."
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "```\n"
    msg += "📉 Kalan Limitiniz: 1\n\n"
    msg += "🛒 Market Menüsü: /market\n"
    msg += "🔗 Referans Linkiniz: /referansim"
    return msg

async def api_get(url, params):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        return {"hata": f"API Hatası (Kod: {response.status_code})"}
    except Exception as e:
        return {"hata": f"Bağlantı Hatası: Sunucuya ulaşılamıyor."}

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *Sorgu Paneli Botuna Hoşgeldiniz!*\n\n"
        "🔍 *Kullanabileceğiniz Komutlar:*\n"
        "➡ `/adsoyad AD SOYAD` - İsimden sorgu yapar\n"
        "➡ `/tckn TCNO` - TC No'dan bilgi getirir\n"
        "➡ `/aile TCNO` - Aile bilgilerini getirir\n"
        "➡ `/gsm NO` - GSM sorgusu yapar\n\n"
        "ℹ️ Örnek: `/adsoyad MEHMET ATAR`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def adsoyad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("❌ Kullanım: `/adsoyad AD SOYAD`")
    res = await api_get("http://45.81.113.22:4014/api/v1/adsoyad", {"ad": context.args[0], "soyad": context.args[1]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def tckn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/tckn TCNO`")
    res = await api_get("http://45.81.113.22:4014/api/v1/tc/adres", {"tc": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def aile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/aile TCNO`")
    res = await api_get("http://45.81.113.22:4014/api/v1/aile", {"tc": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

async def gsm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("❌ Kullanım: `/gsm 0555...`")
    res = await api_get("http://45.81.113.22:4014/api/v1/gsm", {"q": context.args[0]})
    await update.message.reply_text(format_box(res), parse_mode="MarkdownV2")

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    # Render uyumasın diye health check başlat
    threading.Thread(target=run_health_check, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adsoyad", adsoyad))
    app.add_handler(CommandHandler("tckn", tckn))
    app.add_handler(CommandHandler("aile", aile))
    app.add_handler(CommandHandler("gsm", gsm))
    
    print("🤖 Bot tüm komutlar yüklendi ve başlatıldı...")
    app.run_polling()
