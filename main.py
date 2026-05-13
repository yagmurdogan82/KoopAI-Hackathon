import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import or_

# LangChain ve Google GenAI kütüphaneleri
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool, create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Veritabanı modüllerimiz
from database import create_db, SessionLocal, Product, Order

os.environ["GOOGLE_API_KEY"] = "AIzaSyCE5_PAMFj9yEI_FDzVoLiOa8xS_RCw-7k"

app = FastAPI(title="KoopAI - Hatay Kadın Kooperatifi", version="1.0")

# Templates klasörünü tanımlıyoruz
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

# RAG Retriever'ı bir Agent Aracına (Tool) dönüştürüyoruz
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
Amacın müşterilere sıcak, samimi ve umut verici bir dille yanıt vermek.
Sana verilen araçları (tools) kullanarak doğru bilgileri çek. Asla kendi kendine stok veya fiyat uydurma."""

# LangGraph ile çok daha hızlı ve akıllı bir ajan oluşturuyoruz
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

# --- 5. FASTAPI UÇ NOKTASI (ENDPOINT) ---
class ChatRequest(BaseModel):
    mesaj: str

@app.post("/api/chat")
async def chat_with_koopai(request: ChatRequest):
    # LangGraph ajanı mesaj listesi (messages) ile çalışır
    sonuc = agent_executor.invoke({"messages": [HumanMessage(content=request.mesaj)]})
    
    # Dönen mesaj listesinden en sonuncusunu (KoopAI'nin yanıtını) alıyoruz
    yanit_metni = sonuc["messages"][-1].content
    
    return {"yanit": yanit_metni}

# Sitenin ana sayfasına (Kök dizine) girildiğinde index.html'i göster
@app.get("/")
async def ana_sayfa(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")