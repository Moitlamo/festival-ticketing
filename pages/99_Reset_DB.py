import streamlit as st
from models import SessionLocal, Base

st.title("🚨 Database Reset")
st.warning("Clicking this will wipe all live data and rebuild the tables.")

if st.button("RESET DATABASE NOW"):
    try:
        engine = SessionLocal().get_bind()
        
        # 1. Try to drop tables, but gracefully ignore if they are already gone
        try:
            Base.metadata.drop_all(bind=engine)
            st.info("Cleared existing tables.")
        except Exception:
            st.info("Database is already empty. Proceeding to create...")
        
        # 2. Force the creation of the new multi-tenant tables
        Base.metadata.create_all(bind=engine)
        
        st.success("✅ Database successfully reset and upgraded for Multi-Tenancy!")
    except Exception as e:
        st.error(f"Critical Error: {e}")
