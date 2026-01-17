# New Dev Assistant 🛠️

**New Dev Assistant**, yazılım projelerini analiz eden, potansiyel riskleri ortaya çıkaran ve geliştiriciye proje sağlığı konusunda rehberlik eden **Python tabanlı bir masaüstü geliştirici yardımcısıdır**.

Bu proje, önceki denemelerden edinilen tecrübelerle **daha temiz mimari**, **daha sürdürülebilir yapı** ve **genişletilebilirlik** hedefiyle yeniden ele alınmıştır.

> 🎯 Amaç: _Kodun sadece çalışmasını değil, uzun vadede sağlıklı kalmasını sağlamak._

---

## 🚀 Temel Özellikler

### 🔍 Proje Analizi (Scanner)

- Dosya ve klasör yapısının taranması
- Riskli kod alışkanlıklarının ve pattern’lerin tespiti
- TODO / FIXME / NOTE gibi geliştirici notlarının bulunması
- Proje köküne göre bağlamsal değerlendirme

### 📊 Raporlama

- Analiz sonuçlarını **HTML rapor** olarak üretir
- Koyu temalı, modern ve okunabilir arayüz
- Riskler, uyarılar ve yapılacaklar net şekilde ayrılır
- Proje adına ve zamana göre otomatik rapor isimlendirme

### 🖥️ Masaüstü Arayüz

- **PySide6 (Qt)** tabanlı native masaüstü uygulaması
- Dark / Light tema desteği
- Sade, geliştirici odaklı kullanıcı deneyimi
- CLI karmaşası olmadan görsel kontrol

### 🛠️ Modüler ve Genişletilebilir Yapı

- Analiz motoru UI’dan ayrıdır
- Yeni tarama kuralları kolayca eklenebilir
- Yardımcı script’ler için ayrı `tools/` dizini

---

## 🧠 Mimari Genel Bakış

```text
src/
├─ launcher.py        # Uygulama giriş noktası
├─ app.py             # Ana pencere ve UI yönetimi
├─ scanner.py         # Proje analiz motoru
├─ report.py          # HTML rapor üretimi
├─ config.py          # Yapılandırma ve ayarlar
└─ ipc.py             # UI ↔ işlem iletişimi
```

### Çalışma Akışı

```text
Kullanıcı → Proje Seçimi
        → Scanner (analiz)
        → Finding listesi
        → Report Generator
        → HTML Rapor
```

Bu yapı sayesinde:

- İş mantığı ve arayüz net biçimde ayrılır
- Test edilebilirlik artar
- İleride CLI, plugin veya AI destekli modüller eklenebilir

---

## ⚙️ Kurulum

### 1️⃣ Depoyu Klonla

```bash
git clone https://github.com/zinkxx/new-dev-assistant.git
cd new-dev-assistant
```

### 2️⃣ Sanal Ortam Oluştur

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 4️⃣ Uygulamayı Çalıştır

```bash
python src/launcher.py
```

---

## 🖥️ Sistem Gereksinimleri

- **Python:** 3.10+
- **İşletim Sistemi:** macOS / Linux / Windows
- **Önerilen ortam:** macOS + Python 3.12+

---

## 📂 Proje Yapısı

```text
.
├─ src/               # Ana uygulama kodları
├─ assets/            # Stil, ikon ve statik dosyalar
├─ tools/             # Yardımcı geliştirici script’leri
├─ requirements.txt   # Python bağımlılıkları
├─ README.md
└─ LICENSE
```

---

## 🧩 Genişletilebilirlik

New Dev Assistant aşağıdaki geliştirmelere açık olacak şekilde tasarlanmıştır:

- 🔌 Plugin tabanlı analiz kuralları
- 📈 Proje sağlık puanı (scoring system)
- 🌐 CI/CD entegrasyonu (rapor export)
- 🧠 AI destekli kod ve yapı önerileri _(planlanan)_

---

## 🛣️ Yol Haritası (Roadmap)

- [ ] Scanner kural setinin genişletilmesi
- [ ] Analiz seviyeleri (basic / strict / deep)
- [ ] JSON & Markdown rapor çıktıları
- [ ] Otomatik periyodik tarama
- [ ] CLI mod desteği

---

## 🤝 Katkı

Katkılar memnuniyetle karşılanır 🚀

1. Fork oluştur
2. Feature branch aç (`feature/new-idea`)
3. Commit at
4. Pull Request gönder

---

## 📄 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır.
Detaylar için `LICENSE` dosyasına bakabilirsiniz.

---

## ✨ Geliştirici

**Zinkx**
💻 Developer • 🛠️ Tool Builder • 🚀 Product-Oriented

> New Dev Assistant, gerçek geliştirme süreçlerinde yaşanan sorunlardan yola çıkılarak geliştirilmiştir.
