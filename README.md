# New Dev Assistant 🛠️

**New Dev Assistant**, yazılım projelerini analiz eden, potansiyel riskleri ortaya çıkaran ve geliştiriciye **proje sağlığı** hakkında net, ölçülebilir ve aksiyon alınabilir geri bildirimler sunan **Python tabanlı bir masaüstü geliştirici yardımcısıdır**.

Proje, erken sürümlerde edinilen deneyimlerin ardından **v2.0.0 itibarıyla temizlenmiş, stabilize edilmiş ve uzun vadeli bir temel (baseline)** üzerine oturtulmuştur.

> 🎯 Amaç: Kodun sadece çalışmasını değil, uzun vadede güvenli, sağlıklı ve sürdürülebilir kalmasını sağlamak.

---

## 🚀 v2.0.0 — Clean Stable Baseline

Bu sürüm ile birlikte:

- Risk değerlendirme sistemi netleştirildi
- Dashboard anlamlı ve ölçülebilir hale getirildi
- Repo ve release disiplini oturtuldu

Bu sürüm, projenin **uzun vadeli referans noktasıdır**.

---

## ✨ Temel Özellikler

### 🧠 Risk Scoring & Health Analysis

- CRITICAL / HIGH / MEDIUM risk seviyeleri
- Severity + Score tabanlı değerlendirme
- Proje sağlık puanı hesaplama

### 📊 Dashboard Risk Summary

- Risk dağılımı bar grafikleri
- En riskli dosyalar
- Son tarama istatistikleri

### 🔍 Gelişmiş Scanner

- Tehlikeli fonksiyon tespiti (eval, exec, system, vb.)
- TODO / FIXME / NOTE algılama
- Debug artefact kontrolleri
- Proje hijyen analizleri
- Dev / Prod modları

### 🧾 HTML Raporlama

- Koyu temalı modern HTML rapor
- Otomatik isimlendirme
- Net risk & öneri ayrımı

---

## 🧱 Mimari

```text
src/
├─ launcher.py
├─ app.py
├─ scanner.py
├─ report_html.py
├─ config.py
└─ ipc.py
```

---

## ⚙️ Kurulum

```bash
git clone https://github.com/zinkxx/new-dev-assistant.git
cd new-dev-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/launcher.py
```

---

## 🛣️ Yol Haritası

- Analiz seviyeleri
- CLI mod
- JSON / Markdown raporlar
- Plugin altyapısı
- AI destekli analiz

---

## 📄 Lisans

MIT License

---

## ✨ Geliştirici

**Zinkx**
