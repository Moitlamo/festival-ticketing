import uuid
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

# ==========================================
# 1. DATABASE CONNECTION SETUP
# ==========================================
try:
    if "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
    elif "postgres" in st.secrets:
        db_url = st.secrets["postgres"]["url"]
    elif "connections" in st.secrets:
        db_url = st.secrets["connections"]["postgresql"]["url"]
    else:
        db_url = "sqlite:///./smarttec_local.db"
except Exception:
    db_url = "sqlite:///./smarttec_local.db"

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. ENHANCED MULTI-TENANT MODELS
# ==========================================

class Event(Base):
    """The Specific Function"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_date = Column(DateTime)
    
    # --- THE NEW SECURITY COLUMN ---
    gate_pin = Column(String, nullable=False, default="1234") 
    
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    client = relationship("Client", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")


class Event(Base):
    """The Specific Function"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_date = Column(DateTime)
    
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    client = relationship("Client", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")


class Vendor(Base):
    """Global Authorized Sellers"""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    phone = Column(String)
    
    # Financial and Status Tracking
    status = Column(String, default="Active") 
    remitted_funds = Column(Float, default=0.0)
    
    tickets = relationship("Ticket", back_populates="vendor_profile")

    # Dynamic Dashboard Metrics
    @property
    def allocated_count(self):
        return len(self.tickets)
        
    @property
    def sold_count(self):
        return sum(1 for t in self.tickets if t.status == "Sold")
        
    @property
    def expected_revenue(self):
        return sum(t.price for t in self.tickets if t.status == "Sold" and t.price)


class Ticket(Base):
    """Digital/Physical Inventory"""
    __tablename__ = 'tickets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(Integer, ForeignKey('events.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=True) 
    
    # Original Ticket Data
    ticket_type = Column(String)
    price = Column(Float, default=0.0) 
    status = Column(String, default="Unassigned") 
    security_pin = Column(String)
    vendor_name = Column(String) 
    buyer_phone = Column(String)
    printed_serial = Column(String)
    sold_by = Column(String)
    
    # Gate Validation Metrics
    scanned_at_gate = Column(Boolean, default=False)
    scan_timestamp = Column(DateTime, nullable=True)
    
    event = relationship("Event", back_populates="tickets")
    vendor_profile = relationship("Vendor", back_populates="tickets")
