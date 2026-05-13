from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# SQLite veritabanı dosyası
SQLALCHEMY_DATABASE_URL = "sqlite:///./koopai.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tema 4: Stok ve Envanter Yönetimi için Ürün Modeli
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Zeytinyağı, Defne Sabunu vb.
    description = Column(String)
    price = Column(Float)
    stock_quantity = Column(Integer) # Mevcut Stok
    category = Column(String) # Gıda, El Sanatları vb.

# Tema 2 & 3: Sipariş ve Kargo Takibi için Sipariş Modeli
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    product_id = Column(ForeignKey("products.id"))
    quantity = Column(Integer)
    status = Column(String, default="Hazırlanıyor") # Hazırlanıyor, Kargolandı, Teslim Edildi
    tracking_code = Column(String, nullable=True) # Kargo Takip Kodu
    order_date = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")

# Tabloları oluşturma fonksiyonu
def create_db():
    Base.metadata.create_all(bind=engine)