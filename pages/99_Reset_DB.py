import streamlit as st
from models import engine, Base

st.title("🚨 Database Reset")
st.warning("Clicking this will wipe all live data and rebuild the tables.")

if st.button("RESET DATABASE NOW"):
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        st.success("✅ Database successfully reset and upgraded for Multi-Tenancy!")
    except Exception as e:
        st.error(f"Error: {e}")
