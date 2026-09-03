import streamlit as st
import qrcode
import zipfile
import pandas as pd
import json
import os
import random
from io import BytesIO
from models import SessionLocal, Ticket

st.set_page_config(page_title="Vendor Batches", layout="centered")

# Deep blue and dark red styling to reduce visual fatigue
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select { background-color: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

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
st.write("Manage promoters and generate bulk ticket blocks tracked by event.")

# --- EVENT TRACKING ---
st.subheader("1. Select Event")
event_list = [
    "Leririma Games", 
    "Total Football Mania", 
    "Education Excellence Awards", 
    "Other (Custom)"
]
selected_event = st.selectbox("Event Name", event_list)

if selected_event == "Other (Custom)":
    selected_event = st.text_input("Enter Custom Event Name")

db = SessionLocal()

# Calculate total tickets generated for this event dynamically
if selected_event:
    try:
        total_event_tickets = db.query(Ticket).filter(
            Ticket.buyer_phone.like(f"%Event: {selected_event}%")
        ).count()
        st.info(f"📊 **Total Tickets Generated for {selected_event}:** {total_event_tickets}")
    except Exception:
        st.info("📊 **Total Tickets Generated for this event:** 0")

# --- VENDOR SELECTION ---
st.subheader("2. Assign Vendor")

vendor_options = ["+ Add New Vendor"] + [f"{v['name']} (ID: {k})" for k, v in vendors_db.items()]
selected_vendor_option = st.selectbox("Select Existing Vendor or Add New", vendor_options)

vendor_id = ""
vendor_name = ""
vendor_contact = ""
vendor_address = ""

if selected_vendor_option == "+ Add New Vendor":
    with st.expander("📝 Register New Vendor", expanded=True):
        vendor_id = st.text_input("Vendor ID (e.g., VEND-001)")
        vendor_name = st.text_input("Vendor Name (Person or Business)")
        vendor_contact = st.text_input("Contact Number")
        vendor_address = st.text_input("Address (e.g., Xhosa 1 Ward, Mahalapye)")
        
        if st.button("Save Vendor to Registry"):
            if vendor_id and vendor_name:
                save_vendor(vendor_id, vendor_name, vendor_contact, vendor_address)
                st.success(f"Vendor {vendor_name} saved successfully!")
                st.rerun() # Instantly refreshes the dropdown with the new vendor
            else:
                st.error("⚠️ Vendor ID and Name are required.")
else:
    # Extract vendor ID from the dropdown selection string
    vendor_id = selected_vendor_option.split("(ID: ")[1].replace(")", "")
    vendor_data = vendors_db.get(vendor_id, {})
    vendor_name = vendor_data.get("name", "")
    vendor_contact = vendor_data.get("contact", "")
    vendor_address = vendor_data.get("address", "")
    
    st.write(f"**Contact:** {vendor_contact} | **Address:** {vendor_address}")

# --- BATCH GENERATION ---
st.subheader("3. Generate Batch")
with st.form("vendor_batch_form"):
    batch_size = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
    submit_batch = st.form_submit_button("Generate Ticket Batch", use_container_width=True)

if submit_batch:
    if not vendor_name or not selected_event:
        st.error("⚠️ Please ensure an Event and Vendor are fully selected or registered.")
    else:
        try:
            zip_buffer = BytesIO()
            ticket_data = []
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                st.write(f"Generating {batch_size} tickets for {vendor_name} ({selected_event})...")
                progress_bar = st.progress(0)
                
                for i in range(int(batch_size)):
                    security_pin = str(random.randint(1000, 9999))
                    
                    # Pack tracking data into the existing DB column architecture
                    tracking_data = f"Vendor: {vendor_name} [{vendor_id}] | Event: {selected_event}"
                    
                    new_ticket = Ticket(
                        ticket_type="Physical",
                        status="With_Vendor",
                        buyer_phone=tracking_data, 
                        security_pin=security_pin
                    )
                    db.add(new_ticket)
                    db.commit()
                    db.refresh(new_ticket)
                    
                    # Generate the physical QR badge
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(new_ticket.ticket_id)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="#0b1120", back_color="white").convert('RGB')
                    
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG")
                    
                    file_name = f"Ticket_{i+1}_{new_ticket.ticket_id[:8]}.png"
                    zip_file.writestr(file_name, img_buffer.getvalue())
                    
                    # Add to the Master Log for the vendor
                    ticket_data.append({
                        "Event": selected_event,
                        "Vendor Name": vendor_name,
                        "Vendor ID": vendor_id,
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
                    label="📦 Download QR Codes (ZIP)",
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
