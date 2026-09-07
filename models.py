from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st
import datetime

# Database connection setup
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    
    # Existing columns
    id = Column(String, primary_key=True) 
    ticket_type = Column(String, nullable=False)
    status = Column(String, default="With_Vendor")
    security_pin = Column(String, nullable=True)
    
    # 🚨 NEW COLUMN ADDED HERE 🚨
    printed_serial = Column(String, nullable=True, unique=True)
    
    # Timestamp for when the ticket was generated/imported
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure tables are created (this skips existing tables)
Base.metadata.create_all(bind=engine)
