import streamlit as st
from models import SessionLocal, Vendor

st.set_page_config(page_title="Manage Vendors", page_icon="🧑‍💼")
st.title("🧑‍💼 Manage Vendors")
st.caption("Register authorized sellers for the festival.")

# Form to add a new vendor
with st.form("add_vendor_form", clear_on_submit=True):
    new_vendor_name = st.text_input("New Vendor Name & Code (e.g., Presto Restaurant [VEND-001])")
    submitted = st.form_submit_button("Register Vendor", type="primary")

if submitted:
    if not new_vendor_name.strip():
        st.warning("Please enter a vendor name.")
    else:
        session = SessionLocal()
        try:
            new_vendor = Vendor(name=new_vendor_name.strip())
            session.add(new_vendor)
            session.commit()
            st.success(f"✅ Vendor '{new_vendor_name}' successfully registered!")
        except Exception:
            session.rollback()
            st.error("🚨 This vendor name already exists in the system.")
        finally:
            session.close()

# Display the current list of authorized vendors
st.divider()
st.subheader("Currently Registered Vendors")

session = SessionLocal()
existing_vendors = session.query(Vendor).all()

if existing_vendors:
    for v in existing_vendors:
        st.write(f"🏷️ **{v.name}**")
else:
    st.info("No vendors registered yet.")
session.close()
