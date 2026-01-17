# Contributing to New Dev Assistant 🛠️

Öncelikle **New Dev Assistant** projesine ilgi gösterdiğin için teşekkürler 🙌
Bu doküman, projeye katkı sağlamak isteyen geliştiriciler için temel kuralları ve beklentileri açıklar.

---

## 📌 Genel İlkeler

- Katkılar **küçük veya büyük fark etmeksizin** memnuniyetle karşılanır
- Kod kalitesi, okunabilirlik ve sürdürülebilirlik önceliklidir
- Var olan mimari yapıya uyum önemlidir
- “Çalışıyor” yeterli değildir; **anlaşılır ve temiz** olmalıdır

---

## 🧩 Katkı Türleri

Aşağıdaki katkı türleri özellikle teşvik edilir:

- 🐞 Bug fix
- ✨ Yeni analiz / scanner kuralı
- 🎨 UI / UX iyileştirmeleri
- 🧪 Test eklemeleri
- 📝 Dokümantasyon geliştirmeleri

---

## 🔀 Geliştirme Akışı

### 1️⃣ Depoyu Fork’la

GitHub üzerinden projeyi fork’la.

### 2️⃣ Feature Branch Oluştur

```bash
git checkout -b feature/short-description
```

Örnek:

- `feature/add-todo-detector`
- `fix/report-layout-bug`

---

### 3️⃣ Kod Standartları

- Python 3.10+ uyumlu kod yazılmalıdır
- Anlamlı değişken ve fonksiyon isimleri kullanılmalıdır
- Gerekli yerlerde **kısa ve açıklayıcı yorumlar** eklenmelidir
- UI ve analiz mantığı **ayrı tutulmalıdır**

---

### 4️⃣ Commit Mesajları

Commit mesajları **açık ve anlamlı** olmalıdır:

```text
Add TODO and FIXME detection to scanner
Fix report layout overflow on small screens
Refactor scanner for better extensibility
```

---

### 5️⃣ Pull Request Gönder

- PR açıklamasında **ne yaptığını net anlat**
- Gerekliyse ekran görüntüsü veya örnek çıktı ekle
- Büyük değişiklikler için önce issue açılması önerilir

---

## 🧪 Test & Doğrulama

Pull Request göndermeden önce:

- Uygulamanın çalıştığından emin ol
- Scanner çıktılarının beklenen şekilde üretildiğini kontrol et
- Raporun hatasız oluşturulduğunu doğrula

---

## 🗣️ İletişim

Sorular, öneriler veya büyük fikirler için:

- GitHub Issues bölümünü kullan
- Açıklayıcı başlıklar tercih et

---

Tekrar teşekkürler 🚀
Katkıların New Dev Assistant’ı daha güçlü hale getirecek.
