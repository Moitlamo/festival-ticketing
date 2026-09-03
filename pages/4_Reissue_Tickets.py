import streamlit as st
import qrcode
from io import BytesIO
from models import SessionLocal, Ticket
from twilio.rest import Client

st.set_page_config(page_title="Reissue Tickets", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .stTextInput>div>div>input { background-color: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🔄 Reissue Tickets")
st.write("Search the database by mobile number to recover, download, or resend lost tickets.")

with st.form("search_ticket_form"):
    search_phone = st.text_input("Enter Attendee Mobile Number (Include +country code)")
    search_button = st.form_submit_button("Search Database", use_container_width=True)

if search_button:
    if not search_phone.strip():
        st.warning("⚠️ Please enter a mobile number to search.")
    else:
        db = SessionLocal()
        try:
            # Query the database for any tickets matching the provided phone string
            tickets = db.query(Ticket).filter(Ticket.buyer_phone.like(f"%{search_phone.strip()}%")).all()
            
            if not tickets:
                st.error("❌ No tickets found associated with this number.")
            else:
                st.success(f"✅ Found {len(tickets)} ticket(s) linked to this account.")
                
                for t in tickets:
                    # Create a clean UI card for each ticket found
                    with st.expander(f"🎟️ Ticket ID: {t.ticket_id[:8]} | Status: {t.status}", expanded=True):
                        st.write(f"**Security PIN:** {t.security_pin}")
                        st.write(f"**Ticket Type:** {t.ticket_type}")
                        st.write(f"**Original Details:** {t.buyer_phone}")
                        
                        # Regenerate the QR Code from the stored ID
                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        qr.add_data(t.ticket_id)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
                        
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(byte_im, width=150)
                        with col2:
                            st.download_button(
                                label="📥 Download Recovered QR",
                                data=byte_im,
                                file_name=f"recovered_ticket_{t.ticket_id[:8]}.png",
                                mime="image/png",
                                key=f"dl_{t.ticket_id}",
                                use_container_width=True
                            )
                            
                            # Option to push a fresh SMS directly to their phone
                            if st.button("💬 Resend via SMS", key=f"sms_{t.ticket_id}", use_container_width=True):
                                try:
                                    client = Client(st.secrets["TWILIO_ACCOUNT_SID"], st.secrets["TWILIO_AUTH_TOKEN"])
                                    message_body = (
                                        f"RECOVERY: Your Festival Ticket ID is {t.ticket_id[:8]} "
                                        f"| PIN: {t.security_pin}"
                                    )
                                    client.messages.create(
                                        from_=st.secrets["TWILIO_PHONE_NUMBER"],
                                        body=message_body,
                                        to=search_phone.strip()
                                    )
                                    st.info("📨 Recovery SMS sent successfully!")
                                except Exception as sms_error:
                                    st.error(f"Failed to route SMS: {sms_error}")
                                    
        except Exception as e:
            st.error(f"System error during search: {e}")
        finally:
            db.close()
