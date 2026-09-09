import streamlit as st
import random
import qrcode
import zipfile
import io
import pandas as pd
from models import SessionLocal, Ticket, Vendor, Event

st.set_page_config(page_title="Vendor Batches", page_icon="📦")
st.title("📦 Generate Vendor Batches")
st.caption("Assign digital ticket batches to specific events and export for print.")

session = SessionLocal()

# 1. Fetch both Vendors and Events
vendors = session.query(Vendor).all()
events = session.query(Event).all()

vendor_dict = {v.name: v for v in vendors}
event_dict = {e.name: e.id for e in events}

if not vendor_dict or not event_dict:
    st.warning("⚠️ You need at least one registered Vendor and one active Event to generate batches.")
else:
    with st.form("batch_form"):
        selected_event_name = st.selectbox("Select the Event", list(event_dict.keys()))
        selected_vendor_name = st.selectbox("Select an Authorized Vendor", list(vendor_dict.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
        with col2:
            ticket_price = st.number_input("Ticket Price (Pula)", min_value=0.0, value=100.0, step=10.0)
            
        ticket_type_name = st.text_input("Ticket Tier/Type", value="Standard Ticket")
        
        submitted = st.form_submit_button("Generate Ticket Batch", type="primary", use_container_width=True)

    if submitted:
        selected_event_id = event_dict[selected_event_name]
        selected_vendor = vendor_dict[selected_vendor_name]
        
        try:
            with st.spinner(f"Generating {quantity} tickets for {selected_event_name}..."):
                batch_data = []
                
                for i in range(quantity):
                    pin = str(random.randint(1000, 9999))
                    
                    new_ticket = Ticket(
                        event_id=selected_event_id, 
                        vendor_id=selected_vendor.id, # Hard link to vendor for metrics
                        ticket_type=ticket_type_name,
                        price=ticket_price,           # Adds monetary value for financial dashboard
                        status="With_Vendor",
                        security_pin=pin,
                        vendor_name=selected_vendor.name 
                    )
                    session.add(new_ticket)
                    session.flush() 
                    
                    batch_data.append({
                        "UUID": str(new_ticket.id),
                        "Event": selected_event_name,
                        "Vendor": selected_vendor.name,
                        "Type": ticket_type_name,
                        "Price": ticket_price,
                        "Batch_Index": i + 1
                    })
                
                session.commit()
                
                # --- BUILD THE ZIP ARCHIVE ---
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    for t in batch_data:
                        qr = qrcode.QRCode(version=1, box_size=10, border=2)
                        qr.add_data(t["UUID"]) 
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format="PNG")
                        file_name = f"QR_Codes/ticket_{t['Batch_Index']}.png"
                        zip_file.writestr(file_name, img_bytes.getvalue())
                    
                    df = pd.DataFrame(batch_data)
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    zip_file.writestr("Ticket_Manifest.csv", csv_bytes)

                clean_event_name = selected_event_name.replace(" ", "_")
                st.session_state['ready_zip'] = zip_buffer.getvalue()
                st.session_state['zip_filename'] = f"{selected_vendor.name}_{clean_event_name}_Batch.zip"
                
                st.success(f"✅ Successfully generated {quantity} tickets priced at P {ticket_price}!")
                st.balloons()
                
        except Exception as e:
            session.rollback()
            st.error("🚨 An error occurred while generating the batch.")
            st.code(str(e))

    if 'ready_zip' in st.session_state:
        st.download_button(
            label="📦 Download ZIP for Print Shop",
            data=st.session_state['ready_zip'],
            file_name=st.session_state['zip_filename'],
            mime="application/zip",
            type="primary"
        )

session.close()
