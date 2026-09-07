import streamlit as st
from models import SessionLocal, Ticket

st.set_page_config(page_title="Gate Scanner", page_icon="📱")

st.title("📱 Gate Validator")
st.caption("Type the 3-digit serial number from the pre-printed physical ticket.")

# A simple, focused form for mobile entry
with st.form("validation_form", clear_on_submit=True):
    serial_input = st.text_input("Ticket Serial Number", max_chars=3, placeholder="e.g., 251")
    
    # Massive button for easy tapping on a phone screen
    submitted = st.form_submit_button("VALIDATE TICKET", type="primary", use_container_width=True)

if submitted:
    if not serial_input.strip():
        st.warning("Please enter a ticket number.")
    else:
        # Automatically fix single digits (turns "5" into "005")
        formatted_serial = serial_input.strip().zfill(3)
        
        session = SessionLocal()
        try:
            # Search the database for this specific physical ticket
            ticket = session.query(Ticket).filter_by(printed_serial=formatted_serial).first()
            
            if not ticket:
                st.error(f"❌ INVALID TICKET: #{formatted_serial} does not exist in the system.")
            
            elif ticket.status == "Used":
                st.error(f"⚠️ ALREADY SCANNED: #{formatted_serial} has already entered the venue!")
                
            else:
                # Valid ticket found - Update status to Used
                ticket.status = "Used"
                session.commit()
                
                st.success(f"✅ VALID: #{formatted_serial} accepted. Grant Entry!")
                st.balloons() # Visual confirmation for noisy environments
                
        except Exception as e:
            session.rollback()
            st.error("🚨 Connection Error. Please try again.")
            st.code(str(e))
        finally:
            session.close()
