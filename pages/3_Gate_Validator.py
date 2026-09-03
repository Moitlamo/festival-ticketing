import streamlit as st
from models import SessionLocal, Ticket
try:
    from streamlit_qrcode_scanner import qrcode_scanner
except ImportError:
    st.error("⚠️ Library missing. Please run: pip install streamlit-qrcode-scanner")
    st.stop()

st.set_page_config(page_title="Gate Validator", layout="centered")

# Deep blue and dark red styling 
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stTextInput>div>div>input { background-color: #1e293b; color: white; font-size: 20px; font-weight: bold; text-align: center; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; height: 60px; font-size: 20px; font-weight: bold; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .next-btn>button { background-color: #1e3a8a; height: 80px; font-size: 24px; border: 2px solid #60a5fa; }
    .valid-ticket { background-color: #065f46; padding: 30px; border-radius: 10px; text-align: center; border: 3px solid #34d399; margin-bottom: 20px; }
    .fake-ticket { background-color: #7f1d1d; padding: 30px; border-radius: 10px; text-align: center; border: 3px solid #f87171; margin-bottom: 20px; }
    .used-ticket { background-color: #b45309; padding: 30px; border-radius: 10px; text-align: center; border: 3px solid #fbbf24; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Gate Validator")
st.write("Live Camera Scanner activated. Ensure your browser has camera permissions.")

# Initialize session state for continuous scanning flow
if "scanned_id" not in st.session_state:
    st.session_state.scanned_id = None

# --- STATE 1: CAMERA ACTIVE ---
if not st.session_state.scanned_id:
    # 1. Live Camera Feed
    camera_scan = qrcode_scanner(key='live_scanner')
    
    # 2. Manual Fallback (If camera is dark or broken)
    with st.form("manual_scanner_form"):
        manual_id = st.text_input("Or enter Ticket ID manually (if QR is damaged)")
        submit_manual = st.form_submit_button("Verify Manually", use_container_width=True)
    
    if camera_scan:
        st.session_state.scanned_id = camera_scan
        st.rerun()
    elif submit_manual and manual_id.strip():
        st.session_state.scanned_id = manual_id.strip()
        st.rerun()

# --- STATE 2: VALIDATION RESULT SCREEN ---
else:
    clean_id = st.session_state.scanned_id
    db = SessionLocal()
    
    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == clean_id).first()
        
        # 1. Catch Fakes
        if not ticket:
            st.markdown(
                f"""<div class="fake-ticket">
                <h1 style="color: white; margin: 0; font-size: 40px;">❌ FAKE TICKET</h1>
                <p style="color: white; font-size: 20px;">ID: {clean_id}<br>Not recognized by the system.</p>
                </div>""", 
                unsafe_allow_html=True
            )
        
        # 2. Catch Duplicates
        elif ticket.status == "Used":
            st.markdown(
                f"""<div class="used-ticket">
                <h1 style="color: white; margin: 0; font-size: 40px;">⚠️ ALREADY USED</h1>
                <p style="color: white; font-size: 20px;">This ticket was already scanned at the gate.</p>
                </div>""", 
                unsafe_allow_html=True
            )
            
        # 3. Valid Entry
        elif ticket.status in ["Sold", "With_Vendor"]:
            ticket.status = "Used"
            db.commit()
            
            st.markdown(
                f"""<div class="valid-ticket">
                <h1 style="color: white; margin: 0; font-size: 45px;">✅ ACCESS GRANTED</h1>
                <p style="color: white; font-size: 22px;">Type: {ticket.ticket_type}<br>Database locked successfully.</p>
                </div>""", 
                unsafe_allow_html=True
            )
            
    except Exception as e:
        st.error(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

    # Giant reset button for the next person in line
    st.markdown('<div class="next-btn">', unsafe_allow_html=True)
    if st.button("📷 SCAN NEXT TICKET", use_container_width=True):
        st.session_state.scanned_id = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
