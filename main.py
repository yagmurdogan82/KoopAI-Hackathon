import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import or_
from dotenv import load_dotenv

# LangChain ve Google GenAI kütüphaneleri
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Veritabanı modülleri
from database import create_db, SessionLocal, Product, Order

# API Key
load_dotenv()

app = FastAPI(title="KoopAI - Hatay Kadın Kooperatifi", version="1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates klasörü tanımı
templates = Jinja2Templates(directory="templates")

# --- 1. VERİTABANI BAŞLATMA VE ÖRNEK VERİ EKLEME ---
create_db()

@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    if db.query(Product).count() == 0:
        p1 = Product(name="Soğuk Sıkım Zeytinyağı", description="Altınözü zeytinlerinden", price=450.0, stock_quantity=50, category="Gıda")
        p2 = Product(name="Geleneksel Defne Sabunu", description="El yapımı defne sabunu", price=120.0, stock_quantity=150, category="Kozmetik")
        p3 = Product(name="Acı Biber Salçası", description="Samandağ biberinden", price=200.0, stock_quantity=80, category="Gıda")
        db.add_all([p1, p2, p3])
        db.commit()
    db.close()

# --- 2. RAG SİSTEMİ (Sabit Bilgiler İçin) ---
documents = [
    "Kooperatifimizde satılan zeytinyağları Hatay Altınözü bölgesindeki kadın çiftçilerimiz tarafından soğuk sıkım olarak üretilmektedir.",
    "Siparişler onaylandıktan sonra 2 iş günü içerisinde kargoya teslim edilir. Anlaşmalı kargo firmamız Yurtiçi Kargo'dur.",
    "Kadın kooperatifimizin elde ettiği gelirin %15'i depremzede çocukların eğitim fonuna aktarılmaktadır."
]
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_texts(documents, embeddings, collection_name="koop_data")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# RAG Retriever'ı bir Agent Aracına (Tool) dönüştürür
rag_tool = create_retriever_tool(
    retriever,
    "kooperatif_bilgileri_getir",
    "Kooperatifin genel işleyişi, sosyal sorumluluk projeleri, kargo süreçleri ve üretim yöntemleri hakkında bilgi aramak için bu aracı kullan."
)

# --- 3. SQL VERİTABANI ARACI (Canlı Stok ve Fiyat İçin) ---
@tool
def stok_ve_fiyat_sorgula(urun_adi: str) -> str:
    """Müşteri bir ürünün stoğunu, fiyatını veya var olup olmadığını sorduğunda bu aracı kullanarak veritabanına bak."""
    db = SessionLocal()
    # Gelen kelimeyi içeren ürünü bul (Örn: "sabun" kelimesi "Geleneksel Defne Sabunu"nu bulur)
    urun = db.query(Product).filter(Product.name.ilike(f"%{urun_adi}%")).first()
    db.close()
    
    if urun:
        return f"Bulunan Ürün: {urun.name}. Güncel Stok: {urun.stock_quantity} adet. Fiyatı: {urun.price} TL."
    return f"Maalesef '{urun_adi}' isimli bir ürünümüz şu anda kayıtlarımızda bulunmuyor."

# --- 4. LANGGRAPH AGENT KURULUMU (Yeni Nesil Mimari) ---
tools = [rag_tool, stok_ve_fiyat_sorgula]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

system_prompt = """Sen 6 Şubat depremlerinden sonra Hatay'da kurulan bir kadın kooperatifinin yapay zeka asistanı olan KoopAI'sın.
Amacın kooperatif yöneticilerine ve müşterilere sıcak, samimi ve Hatay şivesi esintileri taşıyan bir dille yanıt vermek.
Eğer senden mail veya mesaj taslağı hazırlaman istenirse, son derece profesyonel ama abartmadan yöresel samimiyeti koruyan bir metin yaz."""

# LangGraph ile çok daha hızlı ve akıllı bir ajan oluşturur
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

# --- 5. FASTAPI UÇ NOKTASI (ENDPOINT) ---
class ChatRequest(BaseModel):
    mesaj: str

@app.post("/api/chat")
async def chat_with_koopai(request: ChatRequest):
    # LangGraph ajanı mesaj listesi (messages) ile çalışır
    sonuc = agent_executor.invoke({"messages": [HumanMessage(content=request.mesaj)]})
    
    # Dönen mesaj listesinden en sonuncusunu (KoopAI'nin yanıtını) alır
    yanit_metni = sonuc["messages"][-1].content

    # Eğer Gemini saf metin yerine obje/liste döndürdüyse, içinden sadece metni söküp alır
    if isinstance(yanit_metni, list):
        temiz_metin = []
        for parca in yanit_metni:
            if isinstance(parca, str):
                temiz_metin.append(parca)
            elif isinstance(parca, dict) and "text" in parca:
                temiz_metin.append(parca["text"])
        yanit_metni = "\n".join(temiz_metin)
    elif not isinstance(yanit_metni, str):
        yanit_metni = str(yanit_metni)
    
    return {"yanit": yanit_metni}

@app.post("/api/otomatik-sms")
async def otomatik_sms_gonder():
    # Gerçek bir senaryoda burada veritabanından 'Kargolandı' durumundaki müşteriler çekilir
    # Ajanın yeteneğini göstermek için dinamik bir SMS taslağı ürettim
    
    prompt = """Sistemdeki aktif kargolar için otomatik SMS tetiklendi. 
    Müşterilere kargolarının yola çıktığını haber veren, profesyonel ama samimi, çok kısa (maksimum 2 cümle) bir toplu SMS metni yazar mısın? 
    KESİNLİKLE abartılı bir şive veya yerel ağız kullanma. Sadece Hatay'ın o meşhur misafirperverliğini ve tatlı dilini hissettiren, profesyonel, zarif ve anlaşılır bir Türkçe kullan. 
    Mesajın sonuna KoopAI imzasını ekle."""
    
    sonuc = agent_executor.invoke({"messages": [HumanMessage(content=prompt)]})
    sms_metni = sonuc["messages"][-1].content
    
    # EĞER GEMINI METİN YERİNE OBJE DÖNDÜRÜRSE DÜZELT:
    if isinstance(sms_metni, list):
        temiz_metin = [p["text"] for p in sms_metni if isinstance(p, dict) and "text" in p]
        sms_metni = "\n".join(temiz_metin) if temiz_metin else str(sms_metni)
    elif not isinstance(sms_metni, str):
        sms_metni = str(sms_metni)

    # Arka planda sunucu loglarına yazdırıyor
    print("--- SİSTEM LOGU: SMS SİSTEMİ TETİKLENDİ ---")
    print(f"Gönderilecek Metin: {sms_metni}")
    print("Durum: Başarıyla Telekomünikasyon API'sine (Simülasyon) iletildi.")
    print("-------------------------------------------")

    return {"durum": "basarili", "uretilen_sms": sms_metni}

# Sitenin ana sayfasına (Kök dizine) girildiğinde index.html'i göster
@app.get("/")
async def ana_sayfa(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
