import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# API Key
load_dotenv()

# 1. Örnek Kooperatif Verileri (İleride bunu veritabanından veya PDF'lerden çekeceğiz)
documents = [
    "Kooperatifimizde satılan zeytinyağları Hatay Altınözü bölgesindeki kadın çiftçilerimiz tarafından soğuk sıkım olarak üretilmektedir.",
    "Siparişler onaylandıktan sonra 2 iş günü içerisinde kargoya teslim edilir. Anlaşmalı kargo firmamız Yurtiçi Kargo'dur.",
    "Biber salçalarımız Samandağ biberlerinden güneşte kurutularak elde edilir, tamamen katkısızdır ve 1 kg'lık cam kavanozlarda satılır.",
    "Defne sabunlarımız geleneksel Hatay yöntemleriyle el yapımı olarak üretilmektedir. Güncel stok durumu: 150 adet.",
    "Kadın kooperatifimizin elde ettiği gelirin %15'i depremzede çocukların eğitim fonuna aktarılmaktadır."
]

# 2. Embedding ve Vektör Veritabanı (ChromaDB)
# Gemini'nin embedding modelini kullanarak metinleri vektörlere çevirir
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_texts(documents, embeddings, collection_name="koop_data")

# En alakalı 2 dokümanı getirecek şekilde ayarlar
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 3. Prompt Tasarımı (Sistem Kimliği)
template = """Sen 6 Şubat depremlerinden sonra Hatay'da kurulan bir kadın kooperatifinin yapay zeka asistanı olan KoopAI'sın.
Amacın müşterilere sıcak, samimi, umut verici ve yardımcı bir dille yanıt vermek.
Soruları yanıtlarken SADECE aşağıdaki bağlamı (context) kullan. Eğer cevabı bağlamda bulamıyorsan, kesinlikle uydurma yapma ve yetkili kooperatif üyelerinin geri dönüş yapacağını söyle.

Bağlam: {context}

Müşteri Sorusu: {question}

Yanıt:"""
prompt = ChatPromptTemplate.from_template(template)

# 4. LLM Tanımlaması (Gemini Modelini kullanıldı)
# temperature=0.3 ile biraz yaratıcılık ama yüksek doğruluk hedeflendi
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# 5. LCEL (LangChain Expression Language) ile Zinciri Kurma
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- SİSTEMİ TEST EDELİM ---
if __name__ == "__main__":
    soru = "Merhaba, zeytinyağlarınız nasıl üretiliyor ve kargom ne zaman yola çıkar?"
    print(f"Soru: {soru}\n")
    
    # Zinciri çalıştırıp (invoke) sonucu alınır
    yanit = rag_chain.invoke(soru)
    print(f"KoopAI Yanıtı:\n{yanit}")