import streamlit as st
from models import SessionLocal, Base

if st.button("UPGRADE DATABASE SCHEMA"):
    try:
        engine = SessionLocal().get_bind()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        st.success("✅ Database upgraded with financial and gate tracking!")
    except Exception as e:
        st.error(f"Error: {e}")
