import streamlit as st
import urllib.parse
from streamlit_qrcode_scanner import qrcode_scanner

# TODO: Import your actual database session and models here
# from database import SessionLocal, Ticket 

st.set_page_config(page_title="Vendor Sales Portal", page_icon="🎫")

# --- Authentication Mock ---
if 'logged_in_vendor' not in st.session_state:
    st.session_state.logged_in_vendor = "Bofelo Lefoko" 

vendor = st.session_state.logged_in_vendor

st.success(f"Logged in as: **{vendor}**")

# --- Live Inventory Section ---
st.header("Live Inventory")

# Uncomment below when connecting to your live PostgreSQL database
# db_session = SessionLocal()
# available_count = db_session.query(Ticket).filter_by(vendor_name=vendor, status="With_Vendor").count()
available_count = 19 # Placeholder matching your screenshot

st.metric(label="Tickets Ready to Sell", value=available_count)

# --- Sales Section ---
st.header("Register a Sale")
tab1, tab2, tab3 = st.tabs(["⌨️ Enter Number", "📸 Scan QR", "📱 Digital & WhatsApp"])

# TAB 1: Manual Physical Entry
with tab1:
    st.write("Sell a physical ticket by typing its 3-digit serial number.")
    serial_input = st.text_input("Enter 3-Digit Serial Number (e.g., 045)", max_chars=3)
    buyer_phone_manual = st.text_input("Buyer Phone Number (+267)", key="phone_manual")
    
    if st.button("Submit Sale", key="btn_manual"):
        if serial_input and buyer_phone_manual:
            st.success(f"✅ Ticket {serial_input} successfully registered to {buyer_phone_manual} and marked as Sold.")
            # TODO: Add database query to update status to "Sold" where serial == serial_input
        else:
            st.warning("Please enter both the serial number and phone number.")

# TAB 2: QR Scanner (Live Auto-Scanner)
with tab2:
    st.write("Hold the physical ticket's QR code up to the camera to scan.")
    
    # Using the exact same live scanner as the Gate Validator, but with a unique key
    scanned_uuid = qrcode_scanner(key="vendor_scanner_live")
    
    # Display the scanned UUID if successful
    if scanned_uuid:
        st.success("✅ QR Code Scanned Successfully!")
        st.code(scanned_uuid)
    
    buyer_phone_scan = st.text_input("Buyer Phone Number (+267)", key="phone_scan")
    
    if st.button("Process Scanned Ticket", key="btn_scan"):
        if scanned_uuid and buyer_phone_scan:
             st.success(f"✅ Ticket {scanned_uuid} successfully registered to {buyer_phone_scan} and marked as Sold.")
             # TODO: Add database query to update status to "Sold" where id == scanned_uuid
        elif not scanned_uuid:
             st.warning("Please scan the QR code first.")
        elif not buyer_phone_scan:
             st.warning("Please enter the buyer's phone number.")

# TAB 3: Digital & WhatsApp
with tab3:
    st.write("Auto-assign the next digital ticket and send via WhatsApp.")
    buyer_phone_digital = st.text_input("Buyer Phone Number (+267)", key="phone_digital")
    
    if st.button("Generate Digital Ticket", key="btn_digital"):
        if available_count > 0 and buyer_phone_digital:
            # TODO: Fetch the actual ticket via SQLAlchemy
            # ticket = db_session.query(Ticket).filter_by(vendor_name=vendor, status="With_Vendor").first()
            mock_ticket_id = "550e8400-e29b-41d4-a716-446655440000" 
            
            # Formulate the WhatsApp message
            message = f"Hello! Here is your SmartTec Ticket.\n\nTicket ID: {mock_ticket_id}\n\nPlease present this code at the gate."
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://wa.me/267{buyer_phone_digital}?text={encoded_message}"
            
            st.success("✅ Digital ticket assigned successfully!")
            st.markdown(f"[**💬 Send Ticket via WhatsApp**]({whatsapp_url})", unsafe_allow_html=True)
            
            # TODO: Update DB status to 'Sold' and commit
        else:
            st.error("🚨 Out of inventory or missing phone number.")
