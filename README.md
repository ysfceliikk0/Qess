# 📥 Universal File Drop Catcher

**Universal File Drop Catcher**, bilgisayarınıza **Quick Share**, **Phone Link (Windows Bağlantısı)** veya **Tarayıcılar (Chrome, Edge, Brave, Firefox)** üzerinden yeni bir dosya düştüğünde ekran kenarından pürüzsüz bir yaylanma (`OutBack`) animasyonuyla beliren, dosyaları doğrudan sürükleyip (Drag & Drop) istediğiniz uygulamaya bırakmanızı sağlayan modern bir **PyQt6** masaüstü aracıdır.

---

## ✨ Öne Çıkan Özellikler

- **⚡ Otomatik Kaynak Tespiti:** Gelen dosyanın **Quick Share** (`⚡`), **Phone Link** (`📱`) veya **Tarayıcı / İndirilenler** (`🌐`) kaynaklı olduğunu alt klasörleriyle birlikte (`recursive=True`) tespit eder; `.crdownload` ve `.part` gibi geçici indirme dosyalarını yoksayar.
- **🗄️ İki Aşamalı Morf Dosya Rafı (Edge Dropzone):**
  - **Stage 0 (Görünmez Algılama):** Seçilen ekran kenarının tam ortasında (`Üst` seçildiğinde `y=0` sıfır boşluklu) görünmez bir yakınlık alanı bekler.
  - **Stage 1 & 2 (Morfing):** Fare kenara yaklaştığında zarif bir çubuk belirir; üzerine gelindiğinde veya dosya sürüklendiğinde çubuk morf animasyonuyla genişleyerek **Dosya Rafı**na dönüşür.
- **🔗 Akıllı UI Entegrasyonu:** Tepsi yönü ile Popup yönü aynı seçildiğinde (Varsayılan: **Üst Kenar**), yeni gelen dosyalar ayrı bir pencere açmak yerine doğrudan kenar tepsisini morf ederek içinde gösterilir.
- **✨ Dinamik Genişleyen (Morphing) Aksiyon Butonları:** **Kapat (`✕`)**, **Tepsiye Ekle (`📥`)**, **Kopyala (`📋`)** ve **Paylaş (`🔗`)** butonlarının üzerine gelindiğinde buton ve ana pencere `OutBack` eğrisiyle yatayda genişler.
- **📤 Yerel Paylaşım Menüsü (Native Share UI):**
  - **Windows 10/11:** `winsdk` / WinRT `IDataTransferManagerInterop` üzerinden yerel Windows **Paylaş** penceresini açar.
  - **Linux (Fedora / GNOME / KDE):** `xdg-desktop-portal` DBus arayüzünü ve yerel paylaşım araçlarını tetikler.
- **🎨 5 Dinamik Tema (Gradient & Solid):** *Okyanus*, *Gün Batımı*, *Gece Yarısı*, *Koyu Mod* ve *Sade Beyaz* temalarıyla tüm arayüzü anında günceller.
- **🚀 Sistem Başlangıcında Çalıştırma (Auto-Start):** Windows Kayıt Defteri (`winreg`) ve Linux `~/.config/autostart/filecatcher.desktop` desteği.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/kullaniciadi/universal-file-drop-catcher.git
cd universal-file-drop-catcher
```

### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Uygulamayı Başlatın
```bash
python main.py
```

---

## 📂 Proje Yapısı

```text
universal-file-drop-catcher/
├── main.py            # Ana uygulama, Watchdog dinleyici ve PyQt6 Morf UI bileşenleri
├── config.json        # Kullanıcı ayarları (Yönler, süre, tema, başlangıç durumu)
├── requirements.txt   # Python bağımlılıkları (PyQt6, watchdog, winsdk)
├── .gitignore         # Git tarafından yoksayılacak dosyalar
└── README.md          # Proje dokümantasyonu
```
