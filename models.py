from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean

class Vendor(Base):
    """Global Authorized Sellers"""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    phone = Column(String)
    
    # New Operational Tracking
    status = Column(String, default="Active") # Active, Suspended, Reconciled
    remitted_funds = Column(Float, default=0.0)
    
    # Establish a direct link to all tickets this vendor handles
    tickets = relationship("Ticket", back_populates="vendor_profile")

    # Dynamic Metrics (Calculated on the fly)
    @property
    def allocated_count(self):
        return len(self.tickets)
        
    @property
    def sold_count(self):
        return sum(1 for t in self.tickets if t.status == "Sold")
        
    @property
    def expected_revenue(self):
        return sum(t.price for t in self.tickets if t.status == "Sold" and t.price)

class Client(Base):
    """The Promoter / Event Organizer"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    contact_phone = Column(String)
    account_status = Column(String, default="Active") 
    
    events = relationship("Event", back_populates="client")

class Ticket(Base):
    """Digital/Physical Inventory"""
    __tablename__ = 'tickets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(Integer, ForeignKey('events.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id')) # Hard link to vendor
    
    ticket_type = Column(String)
    price = Column(Float, default=0.0) # Crucial for financial metrics
    status = Column(String, default="Unassigned") # Unassigned, With_Vendor, Sold
    
    # Gate Validation Metrics
    scanned_at_gate = Column(Boolean, default=False)
    scan_timestamp = Column(DateTime, nullable=True)
    
    event = relationship("Event", back_populates="tickets")
    vendor_profile = relationship("Vendor", back_populates="tickets")
