import streamlit as st
import qrcode
from io import BytesIO
from models import SessionLocal, Ticket
from twilio.rest import Client

st.set_page_config(page_title="Issue Electronic Tickets", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📲 Issue Electronic Tickets")
st.write("Generate secure tickets and dispatch them directly via WhatsApp.")

with st.form("issue_ticket_form"):
    # Require country code for WhatsApp API routing
    buyer_phone = st.text_input("Buyer WhatsApp Number (Include +267)")
    
    # Capture the 4-digit PIN required for future reissuance
    security_pin = st.text_input("Create 4-Digit Security PIN", type="password", max_chars=4)
    
    submit_ticket = st.form_submit_button("Generate & Send via WhatsApp", use_container_width=True)

if submit_ticket:
    if not buyer_phone or len(security_pin) != 4:
        st.error("⚠️ Please provide a valid WhatsApp number and a 4-digit PIN.")
    else:
        db = SessionLocal()
        try:
            # Save ticket with the phone number and PIN
            new_ticket = Ticket(
                ticket_type="Electronic", 
                status="Sold",
                buyer_phone=buyer_phone.strip(),
                security_pin=security_pin
            )
            db.add(new_ticket)
            db.commit()
            db.refresh(new_ticket)
            
            # Generate the QR Code
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(new_ticket.ticket_id)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.success(f"✅ Ticket {new_ticket.ticket_id} generated!")
            st.image(byte_im)
            
            # WhatsApp Dispatch Logic
            TWILIO_ACCOUNT_SID = "your_account_sid_here"
            TWILIO_AUTH_TOKEN = "your_auth_token_here"
            TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886" 
            
            if TWILIO_ACCOUNT_SID != "your_account_sid_here":
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                message_body = (
                    f"🎟️ *Your Event Ticket is Confirmed!*\n\n"
                    f"Ticket ID: {new_ticket.ticket_id}\n"
                    f"Security PIN: Keep your 4-digit PIN safe in case you lose this message.\n\n"
                    f"Please present this ID or your QR code at the gate."
                )
                
                # Format phone number for Twilio WhatsApp API
                formatted_phone = buyer_phone.strip()
                if not formatted_phone.startswith("+"):
                    formatted_phone = "+" + formatted_phone
                    
                message = client.messages.create(
                    from_=TWILIO_WHATSAPP_NUMBER,
                    body=message_body,
                    to=f"whatsapp:{formatted_phone}"
                )
                st.info(f"📱 WhatsApp sent successfully to {formatted_phone}!")
            else:
                st.warning("⚠️ Ticket generated, but WhatsApp was not sent. Twilio API credentials are required.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()
        finally:
            db.close()
