import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

# --- 1. CLIENT MODEL (The Event Organizer) ---
class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    contact_phone = Column(String)
    
    # A client can host multiple events
    events = relationship("Event", back_populates="client")


# --- 2. EVENT MODEL (The Specific Function) ---
class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    event_date = Column(DateTime)
    
    # Link to the Client who owns this event
    client_id = Column(Integer, ForeignKey('clients.id'))
    
    # Relationships mapping back and forth
    client = relationship("Client", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")
    vendors = relationship("Vendor", back_populates="event")


# --- 3. VENDOR MODEL (The Sellers) ---
class Vendor(Base):
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    
    # Lock the vendor to a specific event
    event_id = Column(Integer, ForeignKey('events.id'))
    
    event = relationship("Event", back_populates="vendors")


# --- 4. TICKET MODEL (The Inventory) ---
class Ticket(Base):
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
