import streamlit as st
from models import SessionLocal, Ticket
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="Gate Scanner", page_icon="📱")
st.title("📱 Gate Validator")

# Create mobile-friendly tabs to switch between Digital and Physical
tab1, tab2 = st.tabs(["📷 Digital QR Scanner", "⌨️ Physical Ticket Entry"])

# ----------------- TAB 1: DIGITAL QR SCANNER -----------------
with tab1:
    st.caption("Hold the digital QR code up to the camera.")
    
    # Launch the camera scanner
    qr_code = qrcode_scanner(key='scanner')
    
    if qr_code:
        session = SessionLocal()
        try:
            # Look up the digital ticket by its UUID
            ticket = session.query(Ticket).filter_by(id=qr_code).first()
            
            if not ticket:
                st.error("❌ INVALID TICKET: QR Code not recognized in the database.")
            elif ticket.status == "Used":
                st.error("⚠️ ALREADY SCANNED: This ticket has already entered the venue!")
            else:
                ticket.status = "Used"
                session.commit()
                st.success("✅ VALID: Digital ticket accepted. Grant Entry!")
                st.balloons()
        except Exception as e:
            session.rollback()
            st.error("🚨 Connection Error. Please try again.")
        finally:
            session.close()


# ----------------- TAB 2: PHYSICAL TICKET PAD -----------------
with tab2:
    st.caption("Type the 3-digit serial number from the pre-printed ticket.")
    
    with st.form("validation_form", clear_on_submit=True):
        serial_input = st.text_input("Ticket Serial Number", max_chars=3, placeholder="e.g., 251")
        submitted = st.form_submit_button("VALIDATE PHYSICAL TICKET", type="primary", use_container_width=True)

    if submitted:
        if not serial_input.strip():
            st.warning("Please enter a ticket number.")
        else:
            formatted_serial = serial_input.strip().zfill(3)
            
            session = SessionLocal()
            try:
                ticket = session.query(Ticket).filter_by(printed_serial=formatted_serial).first()
                
                if not ticket:
                    st.error(f"❌ INVALID TICKET: #{formatted_serial} does not exist.")
                elif ticket.status == "Used":
                    st.error(f"⚠️ ALREADY SCANNED: #{formatted_serial} has already entered!")
                else:
                    ticket.status = "Used"
                    session.commit()
                    st.success(f"✅ VALID: #{formatted_serial} accepted. Grant Entry!")
                    st.balloons()
            except Exception as e:
                session.rollback()
                st.error("🚨 Connection Error. Please try again.")
            finally:
                session.close()
