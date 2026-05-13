from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# SQLite veritabanı dosyası
SQLALCHEMY_DATABASE_URL = "sqlite:///./koopai.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. MÜŞTERİLER TABLOSU
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    phone = Column(String)
    city = Column(String) # Kargo gecikmelerini veya rotaları belirlemek için
    
    # Bir müşterinin birden fazla siparişi olabilir (One-to-Many)
    orders = relationship("Order", back_populates="customer")

# 2. ÜRÜNLER TABLOSU
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Zeytinyağı, Defne Sabunu vb.
    description = Column(String)
    price = Column(Float)
    stock_quantity = Column(Integer) # Mevcut Stok
    category = Column(String) # Gıda, El Sanatları vb.

# Bir ürüne ait birden fazla sipariş kaydı olabilir (One-to-Many)
    orders = relationship("Order", back_populates="product")


# 3. SİPARİŞLER TABLOSU (İlişki Merkezi)
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
# Foreign Key bağlantıları
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    quantity = Column(Integer)
    status = Column(String, default="Hazırlanıyor") # Hazırlanıyor, Kargolandı, Teslim Edildi
    tracking_code = Column(String, nullable=True) 
    order_date = Column(DateTime, default=datetime.utcnow)
    
    # İlişki (Relationship) Tanımlamaları
    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product", back_populates="orders")

# Veritabanı ve tabloları oluşturur
def create_db():
    Base.metadata.create_all(bind=engine)