import streamlit as st
import datetime
from models import SessionLocal, Ticket

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")
st.title("🛡️ Live Gate Scanner (Diagnostic Mode)")
st.caption("Verify QR codes and track live event entry.")

st.markdown("### Scan Ticket QR Code")
scanned_uuid = st.text_input("Click here and scan QR code (or type UUID):", key="scanner_input")

if scanned_uuid:
    # Clean the input in case the scanner adds hidden spaces
    clean_uuid = scanned_uuid.strip()
    session = SessionLocal()
    
    try:
        # 1. Look up the ticket
        ticket = session.query(Ticket).filter_by(id=clean_uuid).first()
        
        if not ticket:
            st.error("❌ INVALID TICKET: This QR code is not in the database.")
        else:
            # --- DIAGNOSTIC OUTPUT ---
            # This will show us exactly what is saved in the database
            st.info(f"🔍 DEBUG: The database says this ticket status is: '{ticket.status}'")
            
            # Normalize the status text to prevent capitalization or space errors
            current_status = str(ticket.status).strip().lower()
            
            # 2. Check if already scanned
            if ticket.scanned_at_gate:
                scan_time = ticket.scan_timestamp.strftime("%H:%M:%S") if ticket.scan_timestamp else "Unknown Time"
                st.error(f"🛑 DUPLICATE SCAN: Already used at {scan_time}!")
                
            # 3. STRICT FINANCIAL GUARDRAIL
            elif current_status != "sold":
                st.warning(f"⚠️ UNPAID TICKET BLOCKED! Status is '{ticket.status}'. Vendor {ticket.vendor_name} has not processed this sale.")
                
            # 4. Grant entry only if strictly sold
            elif current_status == "sold":
                ticket.scanned_at_gate = True
                ticket.scan_timestamp = datetime.datetime.now()
                session.commit()
                
                event_name = ticket.event.name if ticket.event else "Event"
                st.success(f"✅ ACCESS GRANTED: Valid ticket for {event_name}.")
                
    except Exception as e:
        session.rollback()
        st.error(f"Error during scan: {e}")
    finally:
        session.close()
