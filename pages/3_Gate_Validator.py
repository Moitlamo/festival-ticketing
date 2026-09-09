import streamlit as st
import datetime
import cv2
import numpy as np
from models import SessionLocal, Ticket

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")
st.title("🛡️ Live Gate Scanner")
st.caption("Verify QR codes and track live event entry.")

# --- TICKET VERIFICATION ENGINE ---
def process_ticket(scanned_uuid):
    clean_uuid = scanned_uuid.strip()
    session = SessionLocal()
    
    try:
        # 1. Look up the ticket
        ticket = session.query(Ticket).filter_by(id=clean_uuid).first()
        
        if not ticket:
            st.error("❌ INVALID TICKET: This QR code is not in the database.")
        else:
            current_status = str(ticket.status).strip().lower()
            
            # 2. Check for duplicate scans
            if ticket.scanned_at_gate:
                scan_time = ticket.scan_timestamp.strftime("%H:%M:%S") if ticket.scan_timestamp else "Unknown Time"
                st.error(f"🛑 DUPLICATE SCAN: Already used at {scan_time}!")
                
            # 3. Financial Guardrail (Blocks unsold tickets)
            elif current_status != "sold":
                st.warning(f"⚠️ UNPAID TICKET BLOCKED! Vendor '{ticket.vendor_name}' has not processed this sale.")
                
            # 4. Grant entry
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
tab1, tab2 = st.tabs(["📷 Mobile Camera", "⌨️ Manual Entry"])

with tab1:
    st.markdown("### Scan with Phone Camera")
    # This triggers the mobile camera
    camera_photo = st.camera_input("Take a clear picture of the QR Code", key="camera")
    
    if camera_photo is not None:
        with st.spinner("Decoding QR..."):
            # Convert the camera image into a format OpenCV can read
            file_bytes = np.asarray(bytearray(camera_photo.read()), dtype=np.uint8)
            opencv_image = cv2.imdecode(file_bytes, 1)
            
            # Decode the QR code
            detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = detector.detectAndDecode(opencv_image)
            
            if data:
                process_ticket(data)
            else:
                st.error("Could not read QR code. Please ensure the code is in focus and well-lit.")

with tab2:
    st.markdown("### Backup Scanner")
    st.info("Use this if the QR code is damaged.")
    manual_uuid = st.text_input("Type UUID or use physical scanner gun:", key="manual_input")
    
    if manual_uuid:
        process_ticket(manual_uuid)
