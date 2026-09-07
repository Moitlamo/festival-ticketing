import streamlit as st
import random
from models import SessionLocal, Ticket, Vendor

st.set_page_config(page_title="Vendor Batches", page_icon="📦")
st.title("📦 Generate Vendor Batches")
st.caption("Assign digital ticket batches to registered festival vendors.")

# 1. Fetch the list of registered vendors from the database
session = SessionLocal()
vendors = session.query(Vendor).all()
vendor_names = [v.name for v in vendors]
session.close()

# 2. Check if there are any vendors available
if not vendor_names:
    st.warning("⚠️ No vendors found! Please register a vendor in the 'Manage Vendors' page first.")
else:
    # 3. Use a selectbox instead of a text input
    with st.form("batch_form"):
        selected_vendor = st.selectbox("Select an Authorized Vendor", vendor_names)
        quantity = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
        ticket_value = st.text_input("Ticket Value (e.g., P 100.00, VIP P 500.00)", value="P 100.00")
        
        submitted = st.form_submit_button("Generate Ticket Batch", type="primary", use_container_width=True)

    if submitted:
        session = SessionLocal()
        try:
            st.info(f"Generating {quantity} tickets for {selected_vendor}...")
            
            for _ in range(quantity):
                pin = str(random.randint(1000, 9999))
                new_ticket = Ticket(
                    ticket_type=f"Batch - {ticket_value}",
                    status="With_Vendor",
                    security_pin=pin,
                    vendor_name=selected_vendor, 
                    buyer_phone=None,       
                    printed_serial=None     
                )
                session.add(new_ticket)
                
            session.commit()
            st.success(f"✅ Successfully generated {quantity} tickets for {selected_vendor}!")
            st.balloons()
            
        except Exception as e:
            session.rollback()
            st.error("🚨 An error occurred while generating the batch.")
            st.code(str(e))
        finally:
            session.close()
