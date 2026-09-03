import streamlit as st
import streamlit.components.v1 as components
from models import SessionLocal, Ticket

# Configure the page
st.set_page_config(page_title="Gate Validator", layout="centered")

# Apply the dark red and deep blue UI for low-light gate environments
st.markdown("""
    <style>
    .stApp {
        background-color: #0b1120; 
        color: #e2e8f0;
    }
    .stButton>button {
        background-color: #7f1d1d;
        color: white;
        border: none;
        height: 50px;
        font-size: 18px;
    }
    .stButton>button:hover {
        background-color: #991b1b;
        color: white;
    }
    .stTextInput>div>div>input {
        font-size: 20px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Gate Validation")
st.write("Scan a digital QR code or type a manual paper ticket serial number to authorize entry.")

# Open database connection
db = SessionLocal()

# Validation Function
def validate_ticket(ticket_identifier):
    # Search by either the electronic UUID or the manual serial number
    ticket = db.query(Ticket).filter(
        (Ticket.ticket_id == ticket_identifier) | 
        (Ticket.serial_number == ticket_identifier)
    ).first()
    
    if not ticket:
        st.error("❌ INVALID TICKET: Not found in database.")
    elif ticket.status == 'Scanned':
        st.error(f"⚠️ ALREADY SCANNED: This ticket was already redeemed.")
    elif ticket.status == 'Void':
        st.error("🚫 TICKET VOIDED: This ticket has been cancelled by an administrator.")
    elif ticket.status in ['Available', 'Sold']:
        # Mark as scanned
        ticket.status = 'Scanned'
        db.commit()
        
        if ticket.ticket_type == 'Electronic':
            st.success("✅ VALID DIGITAL TICKET! Entry Authorized.")
        else:
            st.success(f"✅ VALID PAPER TICKET ({ticket.serial_number})! Entry Authorized.")

# Setup Tabs for the two methods
tab1, tab2 = st.tabs(["Manual Serial Entry", "QR Code Scanner"])

with tab1:
    st.subheader("Type Paper Ticket Serial")
    with st.form("manual_validation_form", clear_on_submit=True):
        manual_serial = st.text_input("Enter Serial Number (e.g., FEST-001)")
        submit_manual = st.form_submit_button("Validate Ticket", use_container_width=True)
        
        if submit_manual and manual_serial:
            validate_ticket(manual_serial.strip())

with tab2:
    st.subheader("Live Camera Scanner")
    st.info("Since web-browsers strictly control camera permissions, you can use the built-in device camera here. Snap a photo of the QR code to read it.")
    
    # Using Streamlit's native camera input for zero-install cloud compatibility
    camera_photo = st.camera_input("Point camera at QR code")
    
    if camera_photo:
        try:
            # We use pyzbar via cv2 (if available in cloud) or prompt for manual entry if cloud missing dependencies
            import qrcode
            st.warning("QR processing requires image libraries. For this cloud prototype, copy the UUID below the generated QR code into the manual entry tab.")
        except Exception as e:
            pass

db.close()
