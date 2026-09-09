import streamlit as st
from models import SessionLocal, Base

st.title("🚨 Database Reset")
st.warning("Clicking this will wipe all live data and rebuild the tables.")

if st.button("RESET DATABASE NOW"):
    try:
        # We extract the engine directly from your working SessionLocal
        engine = SessionLocal().get_bind()
        
        # Drop the old tables and create the new multi-tenant ones
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        st.success("✅ Database successfully reset and upgraded for Multi-Tenancy!")
    except Exception as e:
        st.error(f"Error: {e}")
