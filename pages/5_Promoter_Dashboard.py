import streamlit as st
import datetime
from models import SessionLocal, Ticket

st.set_page_config(page_title="Gate Validator", page_icon="🛡️")
st.title("🛡️ Live Gate Scanner")
st.caption("Verify QR codes and track live event entry.")

# --- SCANNER INTERFACE ---
st.markdown("### Scan Ticket QR Code")
# Depending on your scanner hardware, it usually acts like a keyboard pasting the UUID and hitting Enter
scanned_uuid = st.text_input("Click here and scan QR code (or type UUID):", key="scanner_input")

if scanned_uuid:
    session = SessionLocal()
    
    try:
        # 1. Look up the ticket in the database
        ticket = session.query(Ticket).filter_by(id=scanned_uuid).first()
        
        if not ticket:
            # FATAL: Ticket does not exist in the system at all
            st.error("❌ INVALID TICKET: This QR code is not in the SmartTec Ticket database. Fake ticket detected!")
            
        else:
            # 2. Check if it has already been used
            if ticket.scanned_at_gate:
                scan_time = ticket.scan_timestamp.strftime("%H:%M:%S") if ticket.scan_timestamp else "Unknown Time"
                st.error(f"🛑 DUPLICATE SCAN: This ticket was already used to enter at {scan_time}!")
                
            # 3. THE NEW FINANCIAL GUARDRAIL: Check if it was actually sold
            elif ticket.status != "Sold":
                st.warning(f"⚠️ UNPAID TICKET: This ticket belongs to {ticket.vendor_name} but was never marked as Sold in the portal. Entry Denied.")
                
            # 4. If it passes all checks, grant entry!
            else:
                ticket.scanned_at_gate = True
                ticket.scan_timestamp = datetime.datetime.now()
                session.commit()
                
                # Fetch event name safely through the relationship
                event_name = ticket.event.name if ticket.event else "Event"
                
                st.success(f"✅ ACCESS GRANTED: Valid {ticket.ticket_type} for {event_name}.")
                st.info(f"Vendor: {ticket.vendor_name} | Price: P {ticket.price}")
                
    except ValueError:
        st.error("Invalid QR Code format. Please scan a valid SmartTec ticket.")
    except Exception as e:
        session.rollback()
        st.error(f"Database error during scan: {e}")
    finally:
        session.close()
