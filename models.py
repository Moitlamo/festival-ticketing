import uuid
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

# ==========================================
# 1. DATABASE CONNECTION SETUP
# ==========================================

# Fetch the database URL from your Streamlit Cloud Secrets
try:
    # This tries the most common secret names you might be using
    if "DATABASE_URL" in st.secrets:
        db_url = st.secrets["DATABASE_URL"]
    elif "postgres" in st.secrets:
        db_url = st.secrets["postgres"]["url"]
    elif "connections" in st.secrets:
        db_url = st.secrets["connections"]["postgresql"]["url"]
    else:
        # Fallback to a local SQLite file if no secrets are found
        db_url = "sqlite:///./smarttec_local.db"
except Exception:
    db_url = "sqlite:///./smarttec_local.db"

# Create the engine and the SessionLocal that your other pages are looking for
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 2. MULTI-TENANT DATABASE MODELS
# ==========================================

class Client(Base):
    """The Event Organizer or Promoter"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    contact_phone = Column(String)
    
    # A client can host multiple events
    events = relationship("Event", back_populates="client")


class Event(Base):
    """The Specific Function (e.g., Football Tournament, Awards Gala)"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_date = Column(DateTime)
    
    # Link to the Client who owns this event
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    # Relationships mapping back and forth
    client = relationship("Client", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")
   


class Vendor(Base):
    """The Authorized Sellers (Global)"""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    phone = Column(String)


class Ticket(Base):
    """The Digital/Physical Ticket Inventory"""
    __tablename__ = 'tickets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Lock the ticket to a specific event
    event_id = Column(Integer, ForeignKey('events.id'))
    
    ticket_type = Column(String)
    status = Column(String, default="Unassigned")
    security_pin = Column(String)
    vendor_name = Column(String) 
    buyer_phone = Column(String)
    printed_serial = Column(String)
    sold_by = Column(String)
    
    event = relationship("Event", back_populates="tickets")
