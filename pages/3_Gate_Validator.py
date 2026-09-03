import streamlit as st
import streamlit.components.v1 as components
from models import SessionLocal, Ticket
import time

st.set_page_config(page_title="Gate Validator", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; height: 50px; font-size: 18px; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .stTextInput>div>div>input { font-size: 20px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Universal Gate Scanner")

db = SessionLocal()

def validate_ticket(ticket_identifier):
    ticket = db.query(Ticket).filter(
        (Ticket.ticket_id == ticket_identifier) | 
        (Ticket.serial_number == ticket_identifier)
    ).first()
    
    if not ticket:
        st.error(f"❌ INVALID: '{ticket_identifier}' not found in database.")
    elif ticket.status == 'Scanned':
        st.error(f"⚠️ ALREADY SCANNED: This ticket was already redeemed.")
    elif ticket.status == 'Void':
        st.error("🚫 TICKET VOIDED: This ticket has been cancelled.")
    elif ticket.status in ['Available', 'Sold']:
        ticket.status = 'Scanned'
        db.commit()
        if ticket.ticket_type == 'Electronic':
            st.success("✅ VALID DIGITAL TICKET! Entry Authorized.")
        else:
            st.success(f"✅ VALID PAPER TICKET ({ticket.serial_number})! Entry Authorized.")

# 1. Check if a scan was just passed through the URL parameters
query_params = st.query_params
if "scanned_code" in query_params:
    scanned_val = query_params["scanned_code"]
    validate_ticket(scanned_val)
    
    # Clear the URL parameter so it doesn't re-validate on page refresh
    st.query_params.clear()
    time.sleep(2) # Give gate staff time to read the success/fail message
    st.rerun()

# 2. Manual Entry Fallback
with st.form("manual_validation_form", clear_on_submit=True):
    manual_serial = st.text_input("Manual Entry (Type serial if barcode is damaged)")
    submit_manual = st.form_submit_button("Validate Manually", use_container_width=True)
    if submit_manual and manual_serial:
        validate_ticket(manual_serial.strip())

st.divider()

# 3. Live Camera Scanner Integration
st.subheader("Live Camera Scanner")
st.write("Point your device camera at the digital QR code or physical barcode.")

# HTML5 QR/Barcode Scanner
scanner_html = """
<div id="reader" style="width: 100%; border-radius: 8px; overflow: hidden;"></div>
<script src="https://unpkg.com/html5-qrcode"></script>
<script>
    function onScanSuccess(decodedText, decodedResult) {
        // Stop the scanner to prevent double-scanning
        html5QrcodeScanner.clear();
        
        // Push the scanned code to the Streamlit URL parameters
        const url = new URL(window.parent.location.href);
        url.searchParams.set("scanned_code", decodedText);
        window.parent.location.href = url.toString();
    }
    
    // Configured to read standard 1D barcodes (paper) and 2D QR codes (digital)
    let html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", 
        { fps: 10, qrbox: {width: 250, height: 250} },
        /* verbose= */ false
    );
    html5QrcodeScanner.render(onScanSuccess);
</script>
"""
components.html(scanner_html, height=400)

db.close()
