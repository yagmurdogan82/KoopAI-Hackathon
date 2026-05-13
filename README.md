# 🌿 KoopAI - Otonom Kadın Kooperatifi Yönetim Sistemi

**KoopAI**, 6 Şubat depremlerinin ardından Hatay'da kurulan kadın kooperatiflerinin operasyonel yükünü sıfıra indirmek ve müşteri iletişimini otomatize etmek amacıyla geliştirilmiş uçtan uca (end-to-end) bir yapay zeka ve yönetim paneli projesidir. 

Bu proje, basit bir web arayüzünden ziyade, çapraz modül senkronizasyonu (cross-module sync) ve ajan tabanlı (agentic) iş akışları barındıran tam teşekküllü bir SaaS simülasyonudur.

## 🚀 Öne Çıkan Özellikler ve Mühendislik Yaklaşımı

* 🤖 **Ajan Tabanlı (Agentic) Müşteri Asistanı:** LangGraph ve Google Gemini 3.1 altyapısıyla çalışan, RAG mimarisiyle kooperatif verilerini okuyan otonom asistan. *Domain Restriction (Guardrails)* uygulanarak botun sadece kooperatif ürünleri hakkında Hatay şivesiyle samimi cevaplar vermesi sağlanmıştır.
* 🔄 **Çapraz Modül Veri Senkronizasyonu (State Management):** Sipariş Yönetimi sayfasında onaylanan bir sipariş; 
    * Özet ekranındaki anlık verileri günceller, 
    * Kargo listesine yeni bir teslimat satırı açar,
    * Stok ve Envanter sayfasındaki ilgili ürünün stoğunu dinamik olarak eksiltir.
* 📄 **Otonom E-Fatura ve PDF Raporlama:** İstemci tarafında (Client-side) `jsPDF` kullanılarak dinamik faturalar ve aylık satış raporları üretilir. Özel *Karakter Dönüştürücü (Sanitizer)* algoritmamız sayesinde Türkçe karakter sorunları sıfıra indirilmiştir.
* ⚠️ **Dinamik Stok Uyarı Sistemi:** Siparişler onaylandıkça düşen stoklar kritik seviyeye (10 ve altı) ulaştığında sistem DOM manipülasyonu ile arayüzü kırmızı alarma geçirir ve üreticiye tedarik uyarısı verir.

## 🧠 Kullanılan Teknolojiler ve Mimari

* **Backend & API:** Python, FastAPI
* **Yapay Zeka (LLM & Vector DB):** Google Gemini, LangChain, LangGraph, ChromaDB
* **Frontend:** HTML5, JavaScript (Vanilla ES6), Bootstrap 5
* **Kütüphaneler:** jsPDF (Raporlama), SweetAlert2 (Asenkron UI bildirimleri), FontAwesome (İkonografi)

## ⚙️ Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz. 

**1. Repoyu Klonlayın:**
```bash
git clone [https://github.com/yagmurdogan82/koopai.git](https://github.com/yagmurdogan82/koopai.git)
cd koopai