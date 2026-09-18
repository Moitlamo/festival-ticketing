import streamlit as st
import datetime
from streamlit_qrcode_scanner import qrcode_scanner
from models import SessionLocal, Ticket, Event

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")

# --- 1. GATE LOGIN SYSTEM ---
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
                event = session.query(Event).filter_by(gate_pin=entered_pin).first()
                session.close()
                
                if event:
                    st.session_state['active_event_id'] = event.id
                    st.session_state['active_event_name'] = event.name
                    st.success(f"✅ Logged into {event.name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid PIN. Please check with the promoter.")
    st.stop()

# --- 2. THE SCANNER INTERFACE ---
active_event_id = st.session_state['active_event_id']
active_event_name = st.session_state['active_event_name']

st.title(f"🛡️ Live Gate: {active_event_name}")

col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Auto-scanner is active and locked to this event.")
with col2:
    if st.button("🚪 Logout"):
        del st.session_state['active_event_id']
        del st.session_state['active_event_name']
        st.rerun()

st.divider()

# --- THE NEW IN/OUT TOGGLE ---
scan_mode = st.radio(
    "Select Scanner Mode:", 
    ["🟢 SCAN IN (Grant Entry)", "🔴 SCAN OUT (Grant Exit)"], 
    horizontal=True
)

def process_ticket(scanned_uuid, current_event_id, mode):
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
            elif current_status != "sold":
                st.warning("⚠️ UNPAID TICKET BLOCKED!")
            else:
                # --- ENTRY LOGIC ---
                if mode == "🟢 SCAN IN (Grant Entry)":
                    if ticket.scanned_at_gate:
                        st.error("🛑 DUPLICATE SCAN: Customer is already marked as INSIDE the venue!")
                    else:
                        ticket.scanned_at_gate = True
                        ticket.scan_timestamp = datetime.datetime.now()
                        local_session.commit()
                        st.success("✅ ACCESS GRANTED! (Customer checked IN)")
                
                # --- EXIT LOGIC ---
                elif mode == "🔴 SCAN OUT (Grant Exit)":
                    if not ticket.scanned_at_gate:
                        st.error("🛑 ERROR: Customer is not currently marked as inside the venue!")
                    else:
                        ticket.scanned_at_gate = False
                        local_session.commit()
                        st.success("👋 GOODBYE! (Customer checked OUT and can return later)")
                
    except Exception as e:
        local_session.rollback()
        st.error(f"Processing error: {e}")
    finally:
        local_session.close()

tab1, tab2 = st.tabs(["📷 Auto-Scan Camera", "⌨️ Manual Entry"])

with tab1:
    # FIX: Changed 'mode' to 'scan_mode' here
    if scan_mode == "🟢 SCAN IN (Grant Entry)":
        st.info("Currently Scanning **IN**. Customers will be marked as inside the venue.")
    else:
        st.warning("Currently Scanning **OUT**. Customers will be permitted to exit and re-enter.")
        
    qr_code = qrcode_scanner(key='qr_scanner')
    if qr_code:
        if 'last_scanned' not in st.session_state or st.session_state['last_scanned'] != qr_code:
            st.session_state['last_scanned'] = qr_code
            process_ticket(qr_code, active_event_id, scan_mode)
            
        if st.button("🔄 Scan Next Ticket", type="primary", use_container_width=True):
            st.session_state['last_scanned'] = None
            st.rerun()

with tab2:
    manual_uuid = st.text_input("Type UUID or use physical scanner gun:")
    if manual_uuid:
        process_ticket(manual_uuid, active_event_id, scan_mode)
