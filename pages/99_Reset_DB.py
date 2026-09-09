import streamlit as st
from models import SessionLocal, Base
from sqlalchemy import MetaData

st.title("🚨 Database Schema Upgrade")
st.warning("This will force-clear all old constraints and build the new multi-tenant tables.")

if st.button("UPGRADE DATABASE SCHEMA", type="primary"):
    try:
        engine = SessionLocal().get_bind()
        
        # 1. Reflect the LIVE database to find all old, stubborn constraints
        meta = MetaData()
        meta.reflect(bind=engine)
        
        # 2. Drop everything it found in the correct order
        meta.drop_all(bind=engine)
        st.info("Cleared old tables and stubborn foreign keys.")
        
        # 3. Build the brand new schema from your models.py
        Base.metadata.create_all(bind=engine)
        
        st.success("✅ Database forcibly cleared and upgraded with financial and gate tracking!")
    except Exception as e:
        st.error(f"Critical Error: {e}")
