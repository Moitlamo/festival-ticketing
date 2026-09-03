import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image
from models import SessionLocal, Ticket

# Configure the page
st.set_page_config(page_title="Issue Electronic Tickets", layout="centered")

# Apply the Dark Blue and Deep Red UI to reduce visual fatigue
st.markdown("""
    <style>
    .stApp {
        background-color: #0b1120; 
        color: #e2e8f0;
    }
    /* Style the generation buttons with the dark red aesthetic */
    .stButton>button {
        background-color: #7f1d1d;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #991b1b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📲 Issue Electronic Tickets")
st.write("Generate secure, UUID-backed QR codes for online buyers.")

# Button to trigger ticket generation
if st.button("Generate New Electronic Ticket", use_container_width=True):
    # 1. Open database connection
    db = SessionLocal()
    
    try:
        # 2. Create the ticket record in the database
        new_ticket = Ticket(
            ticket_type="Electronic",
            status="Sold"  # Marked as sold immediately upon generation
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket) # Retrieves the generated UUID
        
        # 3. Generate the QR Code containing the UUID
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(new_ticket.ticket_id)
        qr.make(fit=True)
        
        # Create the image (using the dark blue for the QR code itself)
        img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
        
        # 4. Save image to a temporary memory buffer so Streamlit can display/download it
        buf = BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        # 5. Display the success message and the ticket
        st.success("✅ Ticket successfully generated and saved to the database!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(byte_im, caption=f"Ticket ID: {new_ticket.ticket_id}")
            
            # Allow the admin to download the QR code to send to the buyer
            st.download_button(
                label="Download QR Code Ticket",
                data=byte_im,
                file_name=f"ticket_{new_ticket.ticket_id}.png",
                mime="image/png",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()
