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
                    st.success(f"Logged into {event.name}")
                    st.rerun()
                else:
                    st.error("Wrong PIN. Ask the promoter for the correct code.")
    st.stop()

# --- 2. THE SCANNER INTERFACE ---
active_event_id = st.session_state['active_event_id']
active_event_name = st.session_state['active_event_name']

st.title(f"🛡️ Gate: {active_event_name}")

col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Scanner locked to this event.")
with col2:
    if st.button("🚪 Logout"):
        del st.session_state['active_event_id']
        del st.session_state['active_event_name']
        st.rerun()

st.divider()

scan_mode = st.radio(
    "Select Action:", 
    ["🟢 SCAN IN (Entering Venue)", "🔴 SCAN OUT (Leaving Venue)"], 
    horizontal=True
)

def process_ticket(scanned_uuid, current_event_id, mode):
    clean_uuid = scanned_uuid.strip()
    local_session = SessionLocal()
    
    try:
        ticket = local_session.query(Ticket).filter_by(id=clean_uuid).first()
        
        # 1. Does the ticket exist in the database?
        if not ticket:
            st.error("⛔ DO NOT ENTER: Ticket does not exist in the system.")
            return

        # 2. Is it for this event?
        if ticket.event_id != current_event_id:
            st.error("⛔ DO NOT ENTER: Ticket belongs to a different event.")
            return

        # 3. Has it been paid for?
        current_status = str(ticket.status).strip().lower()
        if current_status != "sold":
            st.error("⛔ DO NOT ENTER: Ticket has not been paid for.")
            return

        # --- ENTRY CHECKS ---
        if mode == "🟢 SCAN IN (Entering Venue)":
            if ticket.scanned_at_gate:
                st.error("⛔ DO NOT ENTER: User is already inside.")
            else:
                ticket.scanned_at_gate = True
                ticket.scan_timestamp = datetime.datetime.now()
                local_session.commit()
                st.success("✅ ALLOWED TO ENTER: Welcome inside.")
        
        # --- EXIT CHECKS ---
        elif mode == "🔴 SCAN OUT (Leaving Venue)":
            if not ticket.scanned_at_gate:
                st.warning("⚠️ USER IS NOT INSIDE: Cannot scan out someone who hasn't entered.")
            else:
                ticket.scanned_at_gate = False
                local_session.commit()
                st.info("👋 EXIT CONFIRMED: User has left and can re-enter later.")
                
    except Exception as e:
        local_session.rollback()
        st.error(f"System Error: {e}")
    finally:
        local_session.close()

tab1, tab2 = st.tabs(["📷 Auto-Scan Camera", "⌨️ Manual Code Entry"])

with tab1:
    if scan_mode == "🟢 SCAN IN (Entering Venue)":
        st.info("Mode: Checking people IN.")
    else:
        st.warning("Mode: Checking people OUT.")
        
    qr_code = qrcode_scanner(key='qr_scanner')
    if qr_code:
        if 'last_scanned' not in st.session_state or st.session_state['last_scanned'] != qr_code:
            st.session_state['last_scanned'] = qr_code
            process_ticket(qr_code, active_event_id, scan_mode)
            
        if st.button("🔄 Next Scan", type="primary", use_container_width=True):
            st.session_state['last_scanned'] = None
            st.rerun()

with tab2:
    manual_uuid = st.text_input("Enter ticket code manually:")
    if manual_uuid:
        process_ticket(manual_uuid, active_event_id, scan_mode)
