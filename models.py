import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Ticket(Base):
    __tablename__ = 'tickets'
    
    # Unique ID for electronic tickets (This becomes the QR code)
    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 'Electronic' or 'Manual'
    ticket_type = Column(String, nullable=False) 
    
    # For paper tickets, e.g., 'FEST-001'
    serial_number = Column(String, unique=True, nullable=True) 
    
    # 'Available', 'Sold', 'Scanned', 'Void'
    status = Column(String, default='Available') 
    
    # Name of the promoter/vendor holding the manual ticket
    vendor_name = Column(String, nullable=True) 
    
    # When the ticket was generated or registered
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize SQLite database (Streamlit handles this automatically)
engine = create_engine('sqlite:///festival_tickets.db', echo=False)
Base.metadata.create_all(engine)

# Create a session factory we will use in our pages to talk to the database
SessionLocal = sessionmaker(bind=engine)
