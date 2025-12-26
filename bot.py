import telebot
import requests
import random
import time

TOKEN = "8452891749:AAEN5yfQyUEv2hfT9nnnxC6ybPzTMGB7VLA"  # Token'ı değiştir
bot = telebot.TeleBot(TOKEN, parse_mode=None)

ADMIN = "@nabiyetkiliservis"
KANAL = "@nabisystemyeni"

CALISAN_API = {
    "tc": "https://f3api.onrender.com/Api/tc.php",
    "tcgsm": "https://f3api.onrender.com/Api/tcgsm.php",
    "gsmtc": "https://f3api.onrender.com/Api/gsmtc.php",
    "ip": "https://f3api.onrender.com/Api/ip.php",
    "adsoyad": "https://f3api.onrender.com/Api/adsoyad.php"
}

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def api_get(url, params, retries=7):
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, headers=get_headers(), timeout=40)
            if r.status_code == 200:
                return r.json()
            time.sleep(6)
        except:
            time.sleep(6)
    return {"error": "Sunucu şu an yoğun veya kısıtlı. Birkaç dakika sonra tekrar dene."}

def sadece_veri(data):
    if "error" in data and data["error"] != False:
        return f"❌ HATA: {data.get('error', 'Bilinmeyen hata')}"
    if not data or "veri" not in data or not data["veri"]:
        return "❌ VERİ BULUNAMADI\n\n💡 Veritabanında kayıtlı değil veya API kısıtlı."
    
    out = "✅ BULUNAN VERİLER:\n\n"
    count = 0
    for row in data["veri"]:
        count += 1
        for k, v in row.items():
            out += f"<b>{k.upper()}:</b> {v}\n"
        out += "\n"
        if count >= 20:  # Çok fazla veri varsa kes (gsmtc için)
            out += "... (Devamı çok, tam liste için panel kullan)\n"
            break
    return out.strip()

def footer():
    return f"\n—\n👤 Admin: {ADMIN}\n📢 Kanal: {KANAL}"

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "🔥 NABİ SORGU BOTU AKTİF!\n/komut yaz.")

@bot.message_handler(commands=["komut"])
def komut(m):
    bot.send_message(m.chat.id, """
📋 ÇALIŞAN KOMUTLAR (2025 Güncel):

/gsmtc GSM (En iyi çalışıyor ✅)
/tc TC
/tcgsm TC
/ip IP
/adsoyad AD SOYAD İL İLÇE

💡 Veri çıkmazsa veritabanında yok veya kısıtlı. Gerçek kayıtlı numara dene!
    """)

def sorgu_handler(cmd, param_name, api_key, validation=None):
    def handler(m):
        args = m.text.split()
        if len(args) < 2:
            bot.reply_to(m, f"❌ Kullanım: /{cmd} {param_name}")
            return
        value = args[1].strip()
        if validation and not validation(value):
            bot.reply_to(m, validation.__doc__)
            return
        params = {param_name: value}
        if api_key == "gsmtc":
            params = {"gsm": value}
        elif api_key == "tcgsm":
            params = {"tc": value}
        elif api_key == "tc":
            params = {"tc": value}
        elif api_key == "ip":
            params = {"ip": value}
        data = api_get(CALISAN_API[api_key], params)
        bot.send_message(m.chat.id, sadece_veri(data) + footer(), parse_mode="HTML")
    return handler

def tc_validate(val): 
    "❌ TC 11 haneli rakam olmalı!"
    return len(val) == 11 and val.isdigit()

def gsm_validate(val):
    "❌ GSM 10 haneli ve 5 ile başlamalı!"
    return len(val) == 10 and val.isdigit() and val.startswith("5")

bot.message_handler(commands=["tc"])(sorgu_handler("tc", "TC", "tc", tc_validate))
bot.message_handler(commands=["tcgsm"])(sorgu_handler("tcgsm", "TC", "tcgsm", tc_validate))
bot.message_handler(commands=["gsmtc"])(sorgu_handler("gsmtc", "GSM", "gsmtc", gsm_validate))
bot.message_handler(commands=["ip"])(sorgu_handler("ip", "IP", "ip"))

@bot.message_handler(commands=["adsoyad"])
def adsoyad(m):
    args = m.text.split()
    if len(args) < 3:
        bot.reply_to(m, "❌ Kullanım: /adsoyad AD SOYAD İL İLÇE")
        return
    params = {"ad": args[1], "soyad": args[2], "il": args[3] if len(args)>3 else "", "ilce": args[4] if len(args)>4 else ""}
    data = api_get(CALISAN_API["adsoyad"], params)
    bot.send_message(m.chat.id, sadece_veri(data) + footer(), parse_mode="HTML")

print("BOT AKTİF - 2025 Güncel 🔥")
bot.polling(none_stop=True)￼Enter
