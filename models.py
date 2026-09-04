import uuid
import streamlit as st
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Fetch the cloud database URL from Streamlit Secrets
# If testing locally without secrets, fallback to SQLite
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
except (FileNotFoundError, KeyError):
    DATABASE_URL = "sqlite:///ticketing.db"

# 2. Fix PostgreSQL URL scheme for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Initialize the database connection engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Define the Ticket Table Schema
class Ticket(Base):
    __tablename__ = "tickets"
    
    # Primary key: Unique random string (UUID) for the QR code
    ticket_id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    
    # Type of ticket (e.g., Physical, Digital, Gate_WalkIn, Wristband_Exchange)
    ticket_type = Column(String, default="Digital")
    
    # Gate control status (e.g., Sold, With_Vendor, Used)
    status = Column(String, default="Sold")
    
    # Metadata string holding Event Name, Ticket Value, Vendor Name, and Buyer Phone
    buyer_phone = Column(String, nullable=True)
    
    # 4-digit security PIN for SMS recovery and manual verification
    security_pin = Column(String, nullable=True)

# 5. Automatically build tables and catch EXACT connection errors
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    st.error("🚨 DATABASE CONNECTION FAILED. EXACT ERROR:")
    st.code(str(e))
    st.stop()
