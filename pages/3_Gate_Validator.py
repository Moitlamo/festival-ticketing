import streamlit as st
import datetime
from streamlit_qrcode_scanner import qrcode_scanner
from models import SessionLocal, Ticket, Event

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")

# --- 1. GATE LOGIN SYSTEM ---
# If the operator is not logged in, show ONLY the login screen
if 'active_event_id' not in st.session_state:
    st.title("🔐 Gate Scanner Login")
    st.caption("Enter the Gate Access PIN provided by the event promoter.")
    
    with st.form("gate_login"):
        entered_pin = st.text_input("Gate Access PIN", type="password")
        submit_login = st.form_submit_button("Access Scanner", type="primary")
        
        if submit_login:
            if not entered_pin:
                st.error("Please enter a PIN.")
            else:
                session = SessionLocal()
                # Find the exact event linked to this PIN
                event = session.query(Event).filter_by(gate_pin=entered_pin).first()
                session.close()
                
                if event:
                    st.session_state['active_event_id'] = event.id
                    st.session_state['active_event_name'] = event.name
                    st.success(f"✅ Logged into {event.name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid PIN. Please check with the promoter.")
    st.stop() # Stops the rest of the page from loading

# --- 2. THE SCANNER INTERFACE ---
active_event_id = st.session_state['active_event_id']
active_event_name = st.session_state['active_event_name']

st.title(f"🛡️ Live Gate: {active_event_name}")

# Logout Button
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Auto-scanner is active and locked to this event.")
with col2:
    if st.button("🚪 Logout"):
        del st.session_state['active_event_id']
        del st.session_state['active_event_name']
        st.rerun()

st.divider()

def process_ticket(scanned_uuid, current_event_id):
    clean_uuid = scanned_uuid.strip()
    local_session = SessionLocal()
    
    try:
        ticket = local_session.query(Ticket).filter_by(id=clean_uuid).first()
        
        if not ticket:
            st.error("❌ INVALID TICKET: Fake ticket detected!")
        else:
            current_status = str(ticket.status).strip().lower()
            
            if ticket.event_id != current_event_id:
                st.error("🚨 WRONG EVENT BLOCKED! This ticket cannot be used here.")
            elif ticket.scanned_at_gate:
                st.error("🛑 DUPLICATE SCAN: Already used!")
            elif current_status != "sold":
                st.warning("⚠️ UNPAID TICKET BLOCKED!")
            elif current_status == "sold":
                ticket.scanned_at_gate = True
                ticket.scan_timestamp = datetime.datetime.now()
                local_session.commit()
                st.success("✅ ACCESS GRANTED!")
                
    except Exception as e:
        local_session.rollback()
    finally:
        local_session.close()

tab1, tab2 = st.tabs(["📷 Auto-Scan Camera", "⌨️ Manual Entry"])

with tab1:
    qr_code = qrcode_scanner(key='qr_scanner')
    if qr_code:
        if 'last_scanned' not in st.session_state or st.session_state['last_scanned'] != qr_code:
            st.session_state['last_scanned'] = qr_code
            process_ticket(qr_code, active_event_id)
        if st.button("🔄 Scan Next Ticket", type="primary", use_container_width=True):
            st.session_state['last_scanned'] = None
            st.rerun()

with tab2:
    manual_uuid = st.text_input("Type UUID or use physical scanner gun:")
    if manual_uuid:
        process_ticket(manual_uuid, active_event_id)
