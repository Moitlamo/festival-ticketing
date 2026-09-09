import streamlit as st
import random
import qrcode
import zipfile
import io
import pandas as pd
from models import SessionLocal, Ticket, Vendor

st.set_page_config(page_title="Vendor Batches", page_icon="📦")
st.title("📦 Generate Vendor Batches")
st.caption("Assign digital ticket batches to registered festival vendors and export for print.")

# 1. Fetch the list of registered vendors from the database
session = SessionLocal()
vendors = session.query(Vendor).all()
vendor_names = [v.name for v in vendors]
session.close()

# 2. Check if there are any vendors available
if not vendor_names:
    st.warning("⚠️ No vendors found! Please register a vendor in the 'Manage Vendors' page first.")
else:
    # 3. Use a selectbox inside the form
    with st.form("batch_form"):
        selected_vendor = st.selectbox("Select an Authorized Vendor", vendor_names)
        quantity = st.number_input("Number of Tickets to Generate", min_value=1, max_value=500, value=50)
        ticket_value = st.text_input("Ticket Value (e.g., P 100.00, VIP P 500.00)", value="P 100.00")
        
        submitted = st.form_submit_button("Generate Ticket Batch", type="primary", use_container_width=True)

    # 4. Process the form submission
    if submitted:
        session = SessionLocal()
        try:
            with st.spinner(f"Generating {quantity} tickets and building print archive for {selected_vendor}..."):
                
                # We will collect the new ticket data here to build the ZIP
                batch_data = []
                
                for i in range(quantity):
                    pin = str(random.randint(1000, 9999))
                    ticket_type_val = f"Batch - {ticket_value}"
                    
                    new_ticket = Ticket(
                        ticket_type=ticket_type_val,
                        status="With_Vendor",
                        security_pin=pin,
                        vendor_name=selected_vendor, 
                        buyer_phone=None,       
                        printed_serial=None     
                    )
                    session.add(new_ticket)
                    # Flush pushes the object to the database to assign it an ID without committing yet
                    session.flush() 
                    
                    batch_data.append({
                        "UUID": str(new_ticket.id),
                        "Vendor": selected_vendor,
                        "Type": ticket_type_val,
                        "Batch_Index": i + 1
                    })
                
                # Commit all tickets to the database
                session.commit()
                
                # --- BUILD THE ZIP ARCHIVE ---
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    
                    # Add QR codes to the ZIP
                    for t in batch_data:
                        qr = qrcode.QRCode(version=1, box_size=10, border=2)
                        qr.add_data(t["UUID"]) 
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format="PNG")
                        
                        # Name files sequentially (e.g., ticket_1.png, ticket_2.png)
                        file_name = f"QR_Codes/ticket_{t['Batch_Index']}.png"
                        zip_file.writestr(file_name, img_bytes.getvalue())
                    
                    # Add the CSV Manifest to the ZIP
                    df = pd.DataFrame(batch_data)
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    zip_file.writestr("Ticket_Manifest.csv", csv_bytes)

                # Store the generated ZIP and metadata in session state
                st.session_state['ready_zip'] = zip_buffer.getvalue()
                st.session_state['zip_filename'] = f"{selected_vendor}_Batch_{quantity}.zip"
                
                st.success(f"✅ Successfully generated {quantity} tickets for {selected_vendor}!")
                st.balloons()
                
        except Exception as e:
            session.rollback()
            st.error("🚨 An error occurred while generating the batch.")
            st.code(str(e))
        finally:
            session.close()

    # 5. Display the Download Button (Outside the form, relies on session state)
    if 'ready_zip' in st.session_state:
        st.info("🖨️ Your print shop archive is ready. Click below to download.")
        st.download_button(
            label="📦 Download ZIP for Print Shop",
            data=st.session_state['ready_zip'],
            file_name=st.session_state['zip_filename'],
            mime="application/zip",
            type="primary"
        )
