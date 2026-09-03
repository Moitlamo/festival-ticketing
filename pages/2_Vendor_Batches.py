import streamlit as st
import qrcode
import zipfile
import pandas as pd
from io import BytesIO
import random
from models import SessionLocal, Ticket

st.set_page_config(page_title="Vendor Batches", layout="centered")

# Custom UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; } /* Deep blue background */
    .stButton>button { background-color: #8b0000; color: white; border: none; } /* Dark red primary buttons */
    .stButton>button:hover { background-color: #a52a2a; color: white; }
    .stTextInput>div>div>input { background-color: #1e3a8a; color: white; } /* Deep blue input fields */
    div[data-baseweb="input"] { background-color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Generate Vendor Batches")
st.write("Create bulk physical ticket batches for promoters or offline sales.")

with st.form("vendor_batch_form"):
    vendor_name = st.text_input("Vendor / Promoter Name")
    batch_size = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
    
    submit_batch = st.form_submit_button("Generate Ticket Batch", use_container_width=True)

if submit_batch:
    if not vendor_name:
        st.error("⚠️ Please enter a Vendor Name.")
    else:
        db = SessionLocal()
        try:
            zip_buffer = BytesIO()
            ticket_data = []
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                st.write(f"Generating {batch_size} tickets for {vendor_name}...")
                progress_bar = st.progress(0)
                
                for i in range(int(batch_size)):
                    # Auto-generate a random 4-digit PIN for each physical ticket
                    security_pin = str(random.randint(1000, 9999))
                    
                    # Log the vendor name in the phone column or note field
                    new_ticket = Ticket(
                        ticket_type="Physical",
                        status="With_Vendor",
                        buyer_phone=f"Vendor: {vendor_name}", 
                        security_pin=security_pin
                    )
                    db.add(new_ticket)
                    db.commit()
                    db.refresh(new_ticket)
                    
                    # Generate QR Code 
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(new_ticket.ticket_id)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
                    
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG")
                    
                    # Add image to ZIP file
                    file_name = f"Ticket_{i+1}_{new_ticket.ticket_id[:8]}.png"
                    zip_file.writestr(file_name, img_buffer.getvalue())
                    
                    # Add details to our CSV log
                    ticket_data.append({
                        "Ticket Number": i + 1,
                        "Ticket ID": new_ticket.ticket_id,
                        "PIN": security_pin,
                        "Status": "With_Vendor"
                    })
                    
                    progress_bar.progress((i + 1) / int(batch_size))
            
            # Create a pandas dataframe and convert to CSV for the vendor log
            df = pd.DataFrame(ticket_data)
            csv_buffer = df.to_csv(index=False).encode('utf-8')
            
            st.success(f"✅ Successfully generated {batch_size} tickets!")
            
            # Provide download buttons side-by-side
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📦 Download QR Codes (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"Vendor_{vendor_name.replace(' ', '_')}_Batch.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📊 Download Ticket Log (CSV)",
                    data=csv_buffer,
                    file_name=f"Vendor_{vendor_name.replace(' ', '_')}_Log.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()
        finally:
            db.close()
