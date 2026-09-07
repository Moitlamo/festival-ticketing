from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import streamlit as st
import datetime
import uuid

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    ticket_type = Column(String, nullable=False)
    status = Column(String, default="With_Vendor")
    security_pin = Column(String, nullable=True)
    printed_serial = Column(String, nullable=True, unique=True)
    vendor_name = Column(String, nullable=True)
    buyer_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 🚨 NEW VENDOR TABLE 🚨
class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)
