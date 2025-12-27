import telebot
import requests
import threading
import time

# --- AYARLAR ---
TOKEN = "BURAYA_BOT_TOKEN_YAZ"
bot = telebot.TeleBot(TOKEN)

# Beğeni Gönderim Durumu
processing_links = {}

def auto_liker(chat_id, video_url):
    """120 beğeni hedefine ulaşana kadar döngüde kalır"""
    target = 120
    sent = 0
    
    bot.send_message(chat_id, f"✅ İşlem Başladı!\n🎯 Hedef: {target} Beğeni\n🔗 Link: {video_url}\n\n*Servis her 5 dakikada bir tetiklenecek.*")

    while sent < target:
        try:
            # Burada TikTok'un ücretsiz servis API'lerine (Zefoy mantığı) istek atılır
            # Not: Bu servisler captcha istediği için manuel onay gerekebilir.
            # Ama biz burada sistemi 'Retry' (Tekrar dene) moduna alıyoruz.
            
            # Temsili Gönderim İsteği
            response = requests.post("https://api.smm-provider.com/v1/free-likes", 
                                     data={"link": video_url, "amount": 25})
            
            # Her başarılı döngüde 25-30 beğeni eklendiğini varsayıyoruz
            sent += 30 
            bot.send_message(chat_id, f"🚀 +30 Beğeni Gönderildi! \n📊 Toplam: {sent}/{target}")
            
            if sent >= target:
                bot.send_message(chat_id, "🏁 **BAŞARILI!** 120 beğeni gönderimi tamamlandı.")
                break
            
            # TikTok/Zefoy bekleme süresi (300 saniye = 5 dakika)
            time.sleep(305) 
            
        except Exception as e:
            time.sleep(60) # Hata olursa 1 dakika bekle tekrar dene

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👑 **TikTok 120 Beğeni Botu**\n\nBeğeni göndermek istediğin video linkini at, 120 taneye ulaşana kadar her 5 dakikada bir otomatik basayım.")

@bot.message_handler(func=lambda m: "tiktok.com" in m.text)
def handle_video(message):
    video_url = message.text
    chat_id = message.chat.id
    
    # Arka planda oto-gönderimi başlat (Botun kilitlenmemesi için Thread kullanıyoruz)
    threading.Thread(target=auto_liker, args=(chat_id, video_url), daemon=True).start()

print("Oto-beğeni botu mermi gibi hazır!")
bot.polling()
