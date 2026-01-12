// Express kütüphanesini dahil ediyoruz
const express = require('express');
const app = express();

// Render, uygulamana hangi portu kullanacağını "process.env.PORT" ile söyler.
// Eğer yerelde çalıştırıyorsan 3000 portunu kullanır.
const PORT = process.env.PORT || 3000;

// Ana sayfa rotası
app.get('/', (req, res) => {
  res.send('<h1>Render Üzerinde İlk Uygulamam!</h1><p>Bu site bir subdomain üzerinden çalışıyor.</p>');
});

// Sunucuyu başlatıyoruz
app.listen(PORT, () => {
  console.log(`Sunucu ${PORT} portunda aktif.`);
});
