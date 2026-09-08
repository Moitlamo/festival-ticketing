import streamlit as st
import urllib.parse
from streamlit_qrcode_scanner import qrcode_scanner
from models import SessionLocal, Ticket
from sqlalchemy import or_

st.set_page_config(page_title="Vendor Sales Portal", page_icon="🎫")

# --- Mobile UI Fixes ---
st.markdown("""
    <style>
    /* Force the QR scanner iframe to maintain a proper height on mobile */
    iframe {
        min-height: 250px !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Authentication Mock ---
if 'logged_in_vendor' not in st.session_state:
    st.session_state.logged_in_vendor = "Bofelo Lefoko" 
vendor = st.session_state.logged_in_vendor

st.success(f"Logged in as: **{vendor}**")

# --- Live Inventory Section ---
st.header("Live Inventory")

# Calculate how many tickets this vendor is allowed to sell (Assigned + General)
session = SessionLocal()
try:
    available_count = session.query(Ticket).filter(
        Ticket.status == "With_Vendor",
        or_(Ticket.vendor_name == vendor, Ticket.vendor_name.in_([None, "", "General"]))
    ).count()
except Exception:
    available_count = 0
finally:
    session.close()

st.metric(label="Tickets Ready to Sell", value=available_count)

# --- Sales Section ---
st.header("Register a Sale")
tab1, tab2, tab3 = st.tabs(["⌨️ Enter Number", "📸 Scan QR", "📱 Digital & WhatsApp"])

# ----------------- TAB 1: MANUAL PHYSICAL ENTRY -----------------
with tab1:
    st.write("Sell a physical ticket by typing its 3-digit serial number.")
    
    with st.form("manual_sale_form", clear_on_submit=True):
        serial_input = st.text_input("Enter 3-Digit Serial Number (e.g., 045)", max_chars=3)
        buyer_phone_manual = st.text_input("Buyer Phone Number (+267)")
        submit_manual = st.form_submit_button("Submit Sale", type="primary", use_container_width=True)
    
    if submit_manual:
        if serial_input and buyer_phone_manual:
            formatted_serial = serial_input.strip().zfill(3)
            session = SessionLocal()
            try:
                ticket = session.query(Ticket).filter_by(printed_serial=formatted_serial).first()
                
                if not ticket:
                    st.error(f"🚨 INVALID TICKET: #{formatted_serial} does not exist.")
                elif ticket.status == "Sold":
                    st.warning(f"⚠️ ALREADY SOLD: #{formatted_serial} has already been purchased.")
                else:
                    is_general = ticket.vendor_name in [None, "", "General"]
                    is_owner = ticket.vendor_name == vendor
                    
                    if is_owner or is_general:
                        ticket.status = "Sold"
                        ticket.buyer_phone = buyer_phone_manual
                        # Track who actually sold the general ticket for commission/auditing
                        if is_general:
                            ticket.sold_by = vendor 
                            
                        session.commit()
                        st.success(f"✅ SUCCESS: Ticket #{formatted_serial} registered to {buyer_phone_manual} and marked as Sold.")
                    else:
                        st.error(f"⛔ ACCESS DENIED: This ticket is strictly assigned to {ticket.vendor_name}.")
            except Exception as e:
                session.rollback()
                st.error("🚨 Database Error. Please try again.")
            finally:
                session.close()
        else:
            st.warning("Please enter both the serial number and phone number.")

# ----------------- TAB 2: QR SCANNER (LIVE AUTO-SCAN) -----------------
with tab2:
    st.write("Hold the physical ticket's QR code up to the camera to scan.")
    
    scanned_uuid = qrcode_scanner(key="vendor_scanner_live")
    if scanned_uuid:
        st.success("✅ QR Code Scanned Successfully!")
        st.code(scanned_uuid)
        
    with st.form("scan_sale_form", clear_on_submit=True):
        buyer_phone_scan = st.text_input("Buyer Phone Number (+267)")
        submit_scan = st.form_submit_button("Process Scanned Ticket", type="primary", use_container_width=True)
        
    if submit_scan:
        if scanned_uuid and buyer_phone_scan:
            session = SessionLocal()
            try:
                ticket = session.query(Ticket).filter_by(id=scanned_uuid).first()
                
                if not ticket:
                    st.error("🚨 INVALID TICKET: This QR code does not exist in the system.")
                elif ticket.status == "Sold":
                    st.warning("⚠️ ALREADY SOLD: This ticket has already been purchased.")
                else:
                    is_general = ticket.vendor_name in [None, "", "General"]
                    is_owner = ticket.vendor_name == vendor
                    
                    if is_owner or is_general:
                        ticket.status = "Sold"
                        ticket.buyer_phone = buyer_phone_scan
                        if is_general:
                            ticket.sold_by = vendor
                            
                        session.commit()
                        st.success(f"✅ SUCCESS: Ticket registered to {buyer_phone_scan} and marked as Sold.")
                    else:
                        st.error(f"⛔ ACCESS DENIED: This ticket is strictly assigned to {ticket.vendor_name}.")
            except Exception as e:
                session.rollback()
                st.error("🚨 Database Error. Please try again.")
            finally:
                session.close()
        elif not scanned_uuid:
            st.warning("Please scan the QR code first.")
        elif not buyer_phone_scan:
            st.warning("Please enter the buyer's phone number.")

# ----------------- TAB 3: DIGITAL & WHATSAPP -----------------
with tab3:
    st.write("Auto-assign the next available digital ticket and send via WhatsApp.")
    
    with st.form("digital_sale_form", clear_on_submit=True):
        buyer_phone_digital = st.text_input("Buyer Phone Number (+267)")
        submit_digital = st.form_submit_button("Generate Digital Ticket", type="primary", use_container_width=True)
        
    if submit_digital:
        if available_count > 0 and buyer_phone_digital:
            session = SessionLocal()
            try:
                # Fetch the next ticket assigned to this vendor OR a general ticket
                ticket = session.query(Ticket).filter(
                    Ticket.status == "With_Vendor",
                    or_(Ticket.vendor_name == vendor, Ticket.vendor_name.in_([None, "", "General"]))
                ).first()
                
                if ticket:
                    ticket.status = "Sold"
                    ticket.buyer_phone = buyer_phone_digital
                    if ticket.vendor_name in [None, "", "General"]:
                        ticket.sold_by = vendor
                        
                    session.commit()
                    
                    # Formulate the WhatsApp message with the real ticket UUID
                    message = f"Hello! Here is your SmartTec Ticket.\n\nTicket ID: {ticket.id}\n\nPlease present this code at the gate."
                    encoded_message = urllib.parse.quote(message)
                    whatsapp_url = f"https://wa.me/267{buyer_phone_digital}?text={encoded_message}"
                    
                    st.success("✅ Digital ticket assigned successfully!")
                    st.markdown(f"[**💬 Click to Send Ticket via WhatsApp**]({whatsapp_url})", unsafe_allow_html=True)
                else:
                    st.error("🚨 Out of inventory.")
            except Exception as e:
                session.rollback()
                st.error("🚨 Database Error. Please try again.")
            finally:
                session.close()
        else:
            st.warning("Please ensure you have inventory and entered a phone number.")
