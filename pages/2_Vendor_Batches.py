import streamlit as st
import random
from models import SessionLocal, Ticket

st.set_page_config(page_title="Vendor Batches", page_icon="📦")

st.title("📦 Generate Vendor Batches")
st.caption("Create and assign digital ticket batches to registered festival vendors.")

with st.form("batch_form"):
    vendor_name = st.text_input("Vendor Name & Code (e.g., Presto Restaurant [VEND-001])")
    quantity = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
    ticket_value = st.text_input("Ticket Value (e.g., P 100.00, VIP P 500.00)", value="P 100.00")
    
    submitted = st.form_submit_button("Generate Ticket Batch", type="primary", use_container_width=True)

if submitted:
    if not vendor_name.strip():
        st.warning("Please enter a vendor name and code.")
    else:
        session = SessionLocal()
        try:
            st.info(f"Generating {quantity} tickets for {vendor_name}...")
            
            for _ in range(quantity):
                # Generate a random 4-digit security PIN for each ticket
                pin = str(random.randint(1000, 9999))
                
                new_ticket = Ticket(
                    ticket_type=f"Batch - {ticket_value}",
                    status="With_Vendor",
                    security_pin=pin,
                    vendor_name=vendor_name,
                    buyer_phone=None,       # Will be filled when the vendor sells it
                    printed_serial=None     # Left blank for digital batches
                )
                session.add(new_ticket)
                
            session.commit()
            st.success(f"Successfully generated {quantity} tickets for {vendor_name}!")
            st.balloons()
            
        except Exception as e:
            session.rollback()
            st.error("🚨 An error occurred while generating the batch.")
            st.code(str(e))
        finally:
            session.close()
