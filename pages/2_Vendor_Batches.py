import streamlit as st
import qrcode
import zipfile
import pandas as pd
import json
import os
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from models import SessionLocal, Ticket

st.set_page_config(page_title="Vendor Batches", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select { background-color: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- USERNAME EVENT LOCKING ---
USER_EVENT_MAP = {
    "moitlamoleririma": "Leririma Games",
    "moitlamotfm": "Total Football Mania",
    "moitlamoeea": "Education Excellence Awards"
}

# --- VENDOR REGISTRY LOGIC ---
VENDOR_FILE = "vendors.json"

def load_vendors():
    if os.path.exists(VENDOR_FILE):
        with open(VENDOR_FILE, "r") as f:
            return json.load(f)
    return {}

def save_vendor(v_id, v_name, v_contact, v_address):
    vendors = load_vendors()
    vendors[v_id] = {
        "name": v_name,
        "contact": v_contact,
        "address": v_address
    }
    with open(VENDOR_FILE, "w") as f:
        json.dump(vendors, f)

vendors_db = load_vendors()

st.title("📦 Generate Vendor Batches")
st.write("Manage promoters and generate bulk physical ticket blocks.")

# --- 1. SYSTEM AUTHENTICATION ---
st.subheader("1. System Authentication")
admin_username = st.text_input("Enter System Username", type="password")

selected_event = None
if admin_username:
    auth_key = admin_username.strip().lower()
    selected_event = USER_EVENT_MAP.get(auth_key)
    
    if selected_event:
        st.success(f"✅ Authenticated. System locked to: **{selected_event}**")
    else:
        st.error("⚠️ Invalid username. No event associated with this account.")
        st.stop()
else:
    st.info("Please enter your username to unlock batch generation.")
    st.stop()

# --- 2. EVENT TRACKING ---
db = SessionLocal()
try:
    total_event_tickets = db.query(Ticket).filter(
        Ticket.buyer_phone.like(f"%Event: {selected_event}%")
    ).count()
    st.info(f"📊 **Total Tickets Generated for {selected_event}:** {total_event_tickets}")
except Exception:
    st.info(f"📊 **Total Tickets Generated for {selected_event}:** 0")

# --- 3. VENDOR SELECTION ---
st.subheader("2. Assign Vendor")

vendor_options = ["+ Add New Vendor"] + [f"{v['name']} (ID: {k})" for k, v in vendors_db.items()]
selected_vendor_option = st.selectbox("Select Existing Vendor or Add New", vendor_options)

vendor_id, vendor_name, vendor_contact, vendor_address = "", "", "", ""

if selected_vendor_option == "+ Add New Vendor":
    with st.expander("📝 Register New Vendor", expanded=True):
        vendor_id = st.text_input("Vendor ID (e.g., VEND-001)")
        vendor_name = st.text_input("Vendor Name (Person or Business)")
        vendor_contact = st.text_input("Contact Number")
        vendor_address = st.text_input("Address")
        
        if st.button("Save Vendor to Registry"):
            if vendor_id and vendor_name:
                save_vendor(vendor_id, vendor_name, vendor_contact, vendor_address)
                st.success(f"Vendor {vendor_name} saved successfully!")
                st.rerun() 
            else:
                st.error("⚠️ Vendor ID and Name are required.")
else:
    vendor_id = selected_vendor_option.split("(ID: ")[1].replace(")", "")
    vendor_data = vendors_db.get(vendor_id, {})
    vendor_name = vendor_data.get("name", "")
    vendor_contact = vendor_data.get("contact", "")
    vendor_address = vendor_data.get("address", "")
    
    st.write(f"**Contact:** {vendor_contact} | **Address:** {vendor_address}")

# --- 4. BATCH GENERATION ---
st.subheader("3. Generate Batch")
with st.form("vendor_batch_form"):
    batch_size = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
    # New Ticket Value Field
    ticket_value = st.text_input("Ticket Value (e.g., P 150.00, VIP P 500.00)", value="P 100.00")
    
    submit_batch = st.form_submit_button("Generate Ticket Batch", use_container_width=True)

if submit_batch:
    if not vendor_name or not ticket_value:
        st.error("⚠️ Please ensure a Vendor is selected and a Ticket Value is provided.")
    else:
        try:
            zip_buffer = BytesIO()
            ticket_data = []
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                st.write(f"Generating {batch_size} tickets for {vendor_name}...")
                progress_bar = st.progress(0)
                
                for i in range(int(batch_size)):
                    security_pin = str(random.randint(1000, 9999))
                    # Appending ticket value to our database tracking string
                    tracking_data = f"Vendor: {vendor_name} [{vendor_id}] | Event: {selected_event} | Value: {ticket_value}"
                    
                    new_ticket = Ticket(
                        ticket_type="Physical",
                        status="With_Vendor",
                        buyer_phone=tracking_data, 
                        security_pin=security_pin
                    )
                    db.add(new_ticket)
                    db.commit()
                    db.refresh(new_ticket)
                    
                    # 1. Generate base QR Code
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(new_ticket.ticket_id)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
                    
                    # 2. Expand image canvas to fit text at the bottom
                    qr_w, qr_h = qr_img.size
                    extra_height = 80
                    final_img = Image.new('RGB', (qr_w, qr_h + extra_height), color='white')
                    final_img.paste(qr_img, (0, 0))
                    
                    # 3. Draw text onto the image
                    draw = ImageDraw.Draw(final_img)
                    try:
                        # Attempt to load a default TrueType font if available on Streamlit Cloud
                        font = ImageFont.truetype("DejaVuSans.ttf", 18)
                    except IOError:
                        # Fallback to standard generic font
                        font = ImageFont.load_default()
                        
                    event_text = f"Event: {selected_event}"
                    val_text = f"Value: {ticket_value}"
                    pin_text = f"PIN: {security_pin}"
                    
                    draw.text((25, qr_h), event_text, fill="#0b1120", font=font)
                    draw.text((25, qr_h + 25), val_text, fill="#7f1d1d", font=font)
                    draw.text((25, qr_h + 50), pin_text, fill="#0b1120", font=font)
                    
                    # Save the customized composite image
                    img_buffer = BytesIO()
                    final_img.save(img_buffer, format="PNG")
                    
                    file_name = f"Ticket_{i+1}_{new_ticket.ticket_id[:8]}.png"
                    zip_file.writestr(file_name, img_buffer.getvalue())
                    
                    ticket_data.append({
                        "Event": selected_event,
                        "Vendor Name": vendor_name,
                        "Vendor ID": vendor_id,
                        "Ticket Value": ticket_value,
                        "Ticket Number": i + 1,
                        "Ticket ID": new_ticket.ticket_id,
                        "PIN": security_pin,
                        "Status": "With_Vendor"
                    })
                    
                    progress_bar.progress((i + 1) / int(batch_size))
            
            df = pd.DataFrame(ticket_data)
            csv_buffer = df.to_csv(index=False).encode('utf-8')
            
            st.success(f"✅ Successfully generated {batch_size} tickets!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📦 Download Printed QR Codes (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{selected_event.replace(' ', '_')}_{vendor_name.replace(' ', '_')}_Batch.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📊 Download Ticket Log (CSV)",
                    data=csv_buffer,
                    file_name=f"{selected_event.replace(' ', '_')}_{vendor_name.replace(' ', '_')}_Log.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()
        finally:
            db.close()
