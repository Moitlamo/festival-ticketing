from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st
import datetime
import uuid

# Database connection setup
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    
    # Core Identity with automatic UUID string generation
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    ticket_type = Column(String, nullable=False)
    status = Column(String, default="With_Vendor")
    
    # Security & Physical Tracking
    security_pin = Column(String, nullable=True)
    printed_serial = Column(String, nullable=True, unique=True)
    
    # Vendor & Buyer Tracking
    vendor_name = Column(String, nullable=True)
    buyer_phone = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure tables are created (this skips existing tables)
Base.metadata.create_all(bind=engine)
