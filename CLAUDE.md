# Trading Scanner — Proje Hafızası

## Proje Amacı
H4 timeframe'de teknik analiz yapan bir trader için sabah scanner sistemi.
Günlük rutini: sabah sistemi çalıştır, 5 enstrüman için S/R + formasyon + trend özeti al, trade kararlarını journal'a kaydet.

## Trader Profili
- **Timeframe:** H4 (ana), H1 (konfirmasyon)
- **Enstrümanlar:** US30, US500, DE40, EURUSD, GBPUSD
- **Platform:** Tradenation + MT4
- **Stil:** Teknik analiz — S/R cluster, trend, formasyon kombinasyonu

## S/R Kuralı (KRİTİK)
- Bir seviye geçerli sayılmak için **minimum 2-3 kez test edilmiş** olmalı
- Tolerans bandı: ±%0.3 (enstrümana göre ayarlanabilir)
- Test sayısına göre güç skoru: 2 test = orta (sarı), 3+ test = güçlü (kırmızı/yeşil)
- Yakınlık skoru: Fiyat S/R'a %1'den yakınsa ALERT

## Formasyon Listesi

### Mum Formasyonları (1-3 mum)
- Bullish/Bearish Engulfing
- Hammer / Shooting Star
- Doji (standard, long-legged, gravestone, dragonfly)
- Inside Bar
- Pin Bar (uzun fitil, küçük gövde — %70+ fitil kuralı)
- Morning Star / Evening Star
- Tweezer Top / Tweezer Bottom

### Mum Matematiği
- Gövde/toplam mum oranı (güçlü mum: gövde > %75)
- Fitil/gövde oranı (rejection tespiti)
- Kapanış pozisyonu (mumun üst/alt yarısında mı?)
- Hacim karşılaştırması (önceki 10 muma göre)

### Grafik Formasyonları (çok mumlu — son 50-100 H4 mum)
**Reversal (Dönüş):**
- Head & Shoulders (Omuz Baş Omuz)
- Inverse Head & Shoulders (Ters OBO)
- Double Top / Double Bottom
- Rising Wedge (bearish) / Falling Wedge (bullish)
- Cup & Handle

**Continuation (Devam):**
- Bull Flag / Bear Flag
- Ascending Triangle (bullish)
- Descending Triangle (bearish)
- Symmetrical Triangle (breakout bekle)
- Channel (Yükselen / Alçalan / Yatay)

## Proje Yapısı
```
trading_scanner/
├── CLAUDE.md                  # Bu dosya
├── requirements.txt
├── run.py                     # Ana başlatma scripti
├── config.py                  # Ayarlar (enstrümanlar, parametreler)
├── core/
│   ├── data_fetcher.py        # yfinance H4 data çekimi
│   ├── support_resistance.py  # S/R cluster algoritması
│   ├── trend_analyzer.py      # EMA + trendline
│   ├── candle_patterns.py     # Mum formasyonları + matematik
│   └── chart_patterns.py      # Grafik formasyonları
├── journal/
│   ├── journal_db.py          # SQLite trade journal
│   └── statistics.py          # Win rate, formasyon bazlı istatistik
└── ui/
    └── dashboard.py           # Streamlit arayüz
```

## Teknik Stack
- Python 3.10+
- yfinance (H4 OHLCV data)
- pandas, numpy (hesaplamalar)
- scipy (pivot/cluster tespiti)
- mplfinance (grafik render)
- streamlit (dashboard UI)
- plotly (interaktif grafikler)
- SQLite (journal)

## Ticker Mapping (yfinance)
```python
INSTRUMENTS = {
    "US30":   "^DJI",
    "US500":  "^GSPC",
    "DE40":   "^GDAXI",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X"
}
```

## Renk Kodları (Dashboard)
- 🔴 Güçlü direnç (3+ test)
- 🟡 Orta direnç (2 test)
- 🟢 Güçlü destek (3+ test)
- 🟡 Orta destek (2 test)
- ⚠️ Fiyat S/R'a %1'den yakın — ALERT
- 📊 Grafik formasyonu tespit edildi
- 🕯️ Mum formasyonu tespit edildi

## Geliştirme Kuralları
1. Her modül bağımsız test edilebilir olmalı
2. Config.py'den parametreler yönetilmeli (hardcode yok)
3. Hata durumunda sistem çökmemeli — enstrüman skip edilip devam etmeli
4. Her fonksiyon docstring içermeli
5. İlk çalıştırmada örnek data ile test edilebilmeli
