import streamlit as st
import pandas as pd
from models import SessionLocal, Vendor

st.set_page_config(page_title="Manage Vendors", page_icon="👥")
st.title("👥 Manage Authorized Vendors")
st.caption("Register and manage your global ticket sellers.")

session = SessionLocal()

# --- REGISTER NEW VENDOR ---
with st.form("add_vendor_form"):
    st.subheader("Register New Vendor")
    vendor_name = st.text_input("Vendor Name", placeholder="e.g., John Doe, Kudu Supermarket")
    vendor_phone = st.text_input("Vendor Phone Number", placeholder="e.g., 71234567")
    
    submit_vendor = st.form_submit_button("Register Vendor", type="primary")
    
    if submit_vendor:
        if not vendor_name:
            st.error("Vendor name is required.")
        else:
            try:
                new_vendor = Vendor(name=vendor_name, phone=vendor_phone)
                session.add(new_vendor)
                session.commit()
                st.success(f"✅ Vendor '{vendor_name}' successfully registered!")
            except Exception as e:
                session.rollback()
                st.error("Error creating vendor. This name might already exist in the database.")

st.divider()

# --- VIEW CURRENT VENDORS ---
st.subheader("Current Registered Vendors")
vendors = session.query(Vendor).all()

if not vendors:
    st.info("No vendors registered in the system yet.")
else:
    # Display vendors in a clean table
    vendor_data = [{"ID": v.id, "Name": v.name, "Phone": v.phone} for v in vendors]
    df = pd.DataFrame(vendor_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

session.close()
