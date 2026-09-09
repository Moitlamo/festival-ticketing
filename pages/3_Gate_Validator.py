import streamlit as st
import datetime
from streamlit_qrcode_scanner import qrcode_scanner
from models import SessionLocal, Ticket

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")
st.title("🛡️ Live Gate Auto-Scanner")
st.caption("Point your camera at a ticket. It will scan automatically.")

# --- TICKET VERIFICATION ENGINE ---
def process_ticket(scanned_uuid):
    clean_uuid = scanned_uuid.strip()
    session = SessionLocal()
    
    try:
        ticket = session.query(Ticket).filter_by(id=clean_uuid).first()
        
        if not ticket:
            st.error("❌ INVALID TICKET: This QR code is not in the database. Fake ticket detected!")
        else:
            current_status = str(ticket.status).strip().lower()
            
            # Check 1: Duplicate Scan
            if ticket.scanned_at_gate:
                scan_time = ticket.scan_timestamp.strftime("%H:%M:%S") if ticket.scan_timestamp else "Unknown Time"
                st.error(f"🛑 DUPLICATE SCAN: Already used at {scan_time}!")
                
            # Check 2: Financial Guardrail (Blocks unsold tickets)
            elif current_status != "sold":
                st.warning(f"⚠️ UNPAID TICKET BLOCKED! Vendor '{ticket.vendor_name}' has not processed this sale.")
                
            # Check 3: Grant Entry
            elif current_status == "sold":
                ticket.scanned_at_gate = True
                ticket.scan_timestamp = datetime.datetime.now()
                session.commit()
                
                event_name = ticket.event.name if ticket.event else "Event"
                st.success(f"✅ ACCESS GRANTED: Valid ticket for {event_name}.")
                st.info(f"Vendor: {ticket.vendor_name} | Price: P {ticket.price}")
                
    except Exception as e:
        session.rollback()
        st.error(f"Error during scan: {e}")
    finally:
        session.close()

# --- SCANNER INTERFACE ---
tab1, tab2 = st.tabs(["📷 Auto-Scan Camera", "⌨️ Manual Entry"])

with tab1:
    st.markdown("### Point Camera at QR Code")
    st.info("Ensure the QR code is well-lit and in focus.")
    
    # This renders the LIVE video feed and auto-scans
    qr_code = qrcode_scanner(key='qr_scanner')
    
    # When a code is detected, process it
    if qr_code:
        # We use session state so the scanner doesn't spam the same ticket 10 times a second
        if 'last_scanned' not in st.session_state or st.session_state['last_scanned'] != qr_code:
            st.session_state['last_scanned'] = qr_code
            process_ticket(qr_code)
            
        # Button to clear the screen for the next person in line
        if st.button("🔄 Scan Next Ticket", type="primary", use_container_width=True):
            st.session_state['last_scanned'] = None
            st.rerun()

with tab2:
    st.markdown("### Backup Scanner")
    st.info("Use this if a printed QR code is torn or unreadable.")
    manual_uuid = st.text_input("Type UUID or use physical scanner gun:", key="manual_input")
    
    if manual_uuid:
        process_ticket(manual_uuid)
