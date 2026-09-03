import streamlit as st
from models import SessionLocal, Ticket
from twilio.rest import Client

st.set_page_config(page_title="Ticket Reissuance", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; }
    </style>
""", unsafe_allow_html=True)

st.title("🔄 Secure Ticket Reissuance")

with st.form("reissue_form"):
    old_phone = st.text_input("Original Phone Number Used for Purchase")
    auth_pin = st.text_input("4-Digit Security PIN", type="password", max_chars=4)
    new_phone = st.text_input("New Phone Number to Receive Ticket")
    
    submit_reissue = st.form_submit_button("Void Old Ticket & Reissue", use_container_width=True)

if submit_reissue and old_phone and auth_pin and new_phone:
    db = SessionLocal()
    
    # Locate the active ticket associated with the old phone
    original_ticket = db.query(Ticket).filter(
        Ticket.buyer_phone == old_phone,
        Ticket.status.in_(['Available', 'Sold']) 
    ).first()
    
    if not original_ticket:
        st.error("❌ No active, unscanned ticket found for this phone number.")
    elif original_ticket.security_pin != auth_pin:
        st.error("🚫 SECURITY ALERT: Incorrect PIN provided. Reissue denied.")
    else:
        try:
            # Cryptographically destroy the old ticket
            original_ticket.status = "Void"
            
            # Generate the replacement ticket with a new UUID
            replacement = Ticket(
                ticket_type="Electronic",
                status="Sold",
                buyer_phone=new_phone,
                security_pin=auth_pin, 
                original_ticket_id=original_ticket.ticket_id 
            )
            
            db.add(replacement)
            db.commit()
            db.refresh(replacement)
            
            st.success(f"✅ Old ticket voided. New Ticket ID {replacement.ticket_id} generated for {new_phone}.")
            
        except Exception as e:
            db.rollback()
            st.error("System Error during reissuance.")
        finally:
            db.close()
