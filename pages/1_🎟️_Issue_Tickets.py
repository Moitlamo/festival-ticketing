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
st.write("Generate secure tickets and dispatch them via WhatsApp, SMS, or download for offline attendees.")

with st.form("issue_ticket_form"):
    buyer_phone = st.text_input("Attendee Mobile Number (Include country code, e.g., +267...)")
    security_pin = st.text_input("Create 4-Digit Security PIN", type="password", max_chars=4)
    
    # Choose how to deliver the ticket
    delivery_method = st.selectbox(
        "Delivery Method", 
        ["WhatsApp Message", "SMS Text Message", "Manual / Print Only (No Message Sent)"]
    )
    
    submit_ticket = st.form_submit_button("Generate & Process Ticket", use_container_width=True)

if submit_ticket:
    if not buyer_phone or len(security_pin) != 4:
        st.error("⚠️ Please provide a valid mobile number and a 4-digit PIN.")
    else:
        db = SessionLocal()
        try:
            # Save ticket to database
            new_ticket = Ticket(
                ticket_type="Electronic", 
                status="Sold",
                buyer_phone=buyer_phone.strip(),
                security_pin=security_pin
            )
            db.add(new_ticket)
            db.commit()
            db.refresh(new_ticket)
            
            # Generate QR Code image
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(new_ticket.ticket_id)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.success(f"✅ Ticket generated successfully!")
            
            # Display QR code and direct download option for everyone
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(byte_im, caption=f"Ticket ID: {new_ticket.ticket_id}")
                st.download_button(
                    label="📥 Download Ticket QR Code (For Print/Gallery)",
                    data=byte_im,
                    file_name=f"ticket_{new_ticket.ticket_id[:8]}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            # --- MESSAGE DISPATCH LOGIC ---
            TWILIO_ACCOUNT_SID = "your_account_sid_here"
            TWILIO_AUTH_TOKEN = "your_auth_token_here"
            TWILIO_PHONE_NUMBER = "your_twilio_sms_number_here" # e.g., +1234567890
            TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
            
            formatted_phone = buyer_phone.strip()
            if not formatted_phone.startswith("+"):
                formatted_phone = "+" + formatted_phone
                
            message_body = (
                f"🎟️ Festival Ticket Confirmed!\n"
                f"ID: {new_ticket.ticket_id}\n"
                f"PIN: {security_pin}\n"
                f"Present this at the gate."
            )
            
            if TWILIO_ACCOUNT_SID != "your_account_sid_here":
                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                
                if delivery_method == "WhatsApp Message":
                    message = client.messages.create(
                        from_=TWILIO_WHATSAPP_NUMBER,
                        body=message_body,
                        to=f"whatsapp:{formatted_phone}"
                    )
                    st.info(f"📱 WhatsApp sent to {formatted_phone}!")
                    
                elif delivery_method == "SMS Text Message":
                    message = client.messages.create(
                        from_=TWILIO_PHONE_NUMBER,
                        body=message_body,
                        to=formatted_phone
                    )
                    st.info(f"💬 SMS text message sent to {formatted_phone}!")
            else:
                if delivery_method != "Manual / Print Only (No Message Sent)":
                    st.warning("⚠️ Twilio credentials not configured. Ticket created locally, but no message was sent.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()
        finally:
            db.close()
