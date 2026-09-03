import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Ticket(Base):
    __tablename__ = 'tickets'
    
    # Primary Identifier (Becomes the QR Code for Electronic Tickets)
    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 'Electronic' or 'Manual'
    ticket_type = Column(String, nullable=False) 
    
    # --- MANUAL TICKET TRACKING ---
    # For paper tickets, e.g., 'FEST-001'
    serial_number = Column(String, unique=True, nullable=True) 
    # Name of the promoter/vendor holding the manual ticket
    vendor_name = Column(String, nullable=True) 
    
    # --- ELECTRONIC SECURITY & REISSUANCE ---
    # Primary ID for WhatsApp delivery and recovery
    buyer_phone = Column(String, nullable=True) 
    # 4-digit PIN set at purchase to authorize ticket transfers
    security_pin = Column(String, nullable=True) 
    # If a ticket is reissued, this tracks the ID of the voided original
    original_ticket_id = Column(String, nullable=True) 
    
    # --- STATE MANAGEMENT ---
    # Allowed states: 'Available', 'Sold', 'Scanned', 'Void'
    status = Column(String, default='Available') 
    
    # Timestamp of generation
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize SQLite database (Streamlit automatically builds this in the cloud)
engine = create_engine('sqlite:///festival_tickets.db', echo=False)
Base.metadata.create_all(engine)

# Create a session factory we will use in our app pages to query the database
SessionLocal = sessionmaker(bind=engine)
