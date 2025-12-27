import telebot, requests, threading, time, random
from flask import Flask # 7/24 çalışması için gerekli

# --- AYARLAR ---
TOKEN = "BURAYA_BOT_TOKEN_YAZ"
ID = "BURAYA_CHAT_ID_YAZ"
bot = telebot.TeleBot(TOKEN)

# --- 7/24 HAYATTA TUTMA SİSTEMİ (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Annie Bot 7/24 Aktif!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

# --- TIKTOK BEĞENİ MOTORU ---
class TurboEngine:
    def __init__(self, chat_id, url):
        self.chat_id, self.url = chat_id, url
        self.sent, self.target = 0, 120
        self.lock = threading.Lock()

    def attack(self, amount, delay):
        while self.sent < self.target:
            try:
                # Replit üzerinden yüksek hızlı API çıkışı
                r = requests.post("https://api.v1.free-interaction.io/tiktok/v2", 
                                 json={"url": self.url, "mode": "turbo", "amount": amount}, 
                                 timeout=15)
                if r.status_code == 200:
                    with self.lock: self.sent += amount
                    bot.send_message(self.chat_id, f"🚀 **Hız:** +{amount} Beğeni Gönderildi! ({self.sent}/{self.target})")
                if self.sent >= self.target: break
                time.sleep(delay)
            except: time.sleep(20)

# --- BOT KOMUTLARI ---
@bot.message_handler(commands=['start'])
def start(message):
    if str(message.chat.id) != ID: return
    bot.reply_to(message, "👑 **7/24 Replit Turbo Liker Aktif!**\nLinki at, ben arka planda 10 dakikada bitireyim.")

@bot.message_handler(func=lambda m: "tiktok.com" in m.text)
def handle(message):
    if str(message.chat.id) != ID: return
    engine = TurboEngine(message.chat.id, message.text)
    # İki kanaldan eş zamanlı saldırı
    threading.Thread(target=engine.attack, args=(40, 150), daemon=True).start()
    threading.Thread(target=engine.attack, args=(20, 100), daemon=True).start()

# --- BAŞLATMA ---
if __name__ == "__main__":
    # 1. Web sunucusunu başlat (UptimeRobot için)
    threading.Thread(target=run_web_server, daemon=True).start()
    print("Web Sunucusu ve Bot 7/24 Modunda Başlatıldı!")
    
    # 2. Botu çalıştır
    bot.polling(none_stop=True)
￼Enter
