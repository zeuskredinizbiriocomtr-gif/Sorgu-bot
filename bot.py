import telebot
import requests
import random
import time
import os

# Token'ı Replit Secrets'ten al (güvenli!)
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("HATA: TOKEN bulunamadı! Replit Secrets'e 'TOKEN' ekleyin.")
    exit()

bot = telebot.TeleBot(TOKEN, parse_mode=None)

ADMIN = "@nabiyetkiliservis"
KANAL = "@nabisystemyeni"

API = {
    "tc": "https://f3api.onrender.com/Api/tc.php",
    "tcgsm": "https://f3api.onrender.com/Api/tcgsm.php",
    "gsmtc": "https://f3api.onrender.com/Api/gsmtc.php",
    "aile": "https://f3api.onrender.com/Api/aile.php",
    "adres": "https://f3api.onrender.com/Api/adres.php",
    "sulale": "https://f3api.onrender.com/Api/sulale.php",
    "adsoyad": "https://f3api.onrender.com/Api/adsoyad.php"
}

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def api_get(url, params):
    try:
        r = requests.get(url, params=params, headers=get_headers(), timeout=40)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"error": "Sunucu hatası veya bağlantı sorunu. Tekrar dene."}

def format_veri(data):
    if "error" in data and data["error"] != False:
        return f"❌ HATA: {data['error']}"
    
    if not data or "veri" not in data or not data["veri"]:
        return "❌ VERİ BULUNAMADI\n\n💡 Kişi veritabanında kayıtlı değil veya API kısıtlı."
    
    out = "✅ BULUNAN VERİLER:\n\n"
    count = 0
    for row in data["veri"]:
        count += 1
        for k, v in row.items():
            out += f"<b>{k.upper()}:</b> {v}\n"
        out += "\n"
        if count >= 20:  # Çok veri varsa kes (özellikle gsmtc)
            out += "... (Devamı çok, tam liste için panel kullan)\n"
            break
    return out.strip()

def footer():
    return f"\n—\n👤 Admin: {ADMIN}\n📢 Kanal: {KANAL}"

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "🔥 NABİ SORGU BOTU AKTİF!\n\nKomutları görmek için /komut yaz.")

@bot.message_handler(commands=["komut"])
def komut(m):
    bot.send_message(m.chat.id, """
📋 KOMUTLAR

/tc 11111111111 → Kişi bilgisi
/tcgsm 11111111111 → TC'ye kayıtlı GSM'ler
/gsmtc 5xxxxxxxxxx → GSM'ye kayıtlı TC'ler (en iyi çalışan)
/aile 11111111111 → Aile bilgileri
/adsoyad AD SOYAD İL İLÇE → Ad soyad arama

/adres ve /sulale şu an API'de hata veriyor.
    """)

def sorgu_handler(cmd, param_key, api_key, validation=None):
    def handler(m):
        args = m.text.split()
        if len(args) < 2:
            bot.reply_to(m, f"❌ Kullanım: /{cmd} <değer>")
            return
        value = args[1].strip()
        if validation and not validation(value):
            bot.reply_to(m, validation.__doc__)
            return
        params = {param_key: value}
        data = api_get(API[api_key], params)
        bot.send_message(m.chat.id, format_veri(data) + footer(), parse_mode="HTML")
    return handler

def tc_validate(t):
    "❌ TC 11 haneli rakam olmalı!"
    return len(t) == 11 and t.isdigit()

def gsm_validate(g):
    "❌ GSM 10 haneli ve 5 ile başlamalı!"
    return len(g) == 10 and g.isdigit() and g.startswith("5")

# Komutlar
bot.message_handler(commands=["tc"])(sorgu_handler("tc", "tc", "tc", tc_validate))
bot.message_handler(commands=["tcgsm"])(sorgu_handler("tcgsm", "tc", "tcgsm", tc_validate))
bot.message_handler(commands=["gsmtc"])(sorgu_handler("gsmtc", "gsm", "gsmtc", gsm_validate))
bot.message_handler(commands=["aile"])(sorgu_handler("aile", "tc", "aile", tc_validate))

@bot.message_handler(commands=["adsoyad"])
def adsoyad(m):
    args = m.text.split()
    if len(args) < 3:
        bot.reply_to(m, "❌ Kullanım: /adsoyad AD SOYAD İL İLÇE")
        return
    params = {
        "ad": args[1],
        "soyad": args[2],
        "il": args[3] if len(args) > 3 else "",
        "ilce": args[4] if len(args) > 4 else ""
    }
    data = api_get(API["adsoyad"], params)
    bot.send_message(m.chat.id, format_veri(data) + footer(), parse_mode="HTML")

@bot.message_handler(commands=["adres", "sulale"])
def kapali(m):
    bot.reply_to(m, "❌ Bu komut şu an API'de hata veriyor veya kapalı. Yakında düzelirse eklerim.")

print("NABİ SORGU BOTU REPLIT'TE ÇALIŞIYOR 🔥")
bot.polling(none_stop=True)￼Enter
