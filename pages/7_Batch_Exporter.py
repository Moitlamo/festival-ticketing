import streamlit as st
import qrcode
import zipfile
import io
import pandas as pd
# from models import SessionLocal, Ticket

st.header("🖨️ Print Shop QR Exporter")

# --- MOCK DATA (Replace with your actual SQLAlchemy query) ---
# session = SessionLocal()
# tickets = session.query(Ticket).filter_by(status="Unassigned").limit(100).all()
# mock_tickets = [{"id": t.id, "serial": t.printed_serial} for t in tickets]

mock_tickets = [
    {"id": "uuid-1111", "serial": "001"},
    {"id": "uuid-2222", "serial": "002"},
    {"id": "uuid-3333", "serial": "003"}
]

st.write(f"Found {len(mock_tickets)} tickets ready for print export.")

if st.button("Generate QR Code Archive"):
    with st.spinner("Generating high-res QR codes and spreadsheet..."):
        
        # Create an in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            
            # 1. Generate and add QR codes to the ZIP
            for t in mock_tickets:
                qr = qrcode.QRCode(version=1, box_size=10, border=2)
                qr.add_data(t["id"]) 
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                
                file_name = f"ticket_serial_{t['serial']}.png"
                zip_file.writestr(file_name, img_bytes.getvalue())
            
            # 2. Generate the CSV mapping file and add it to the ZIP
            df = pd.DataFrame(mock_tickets)
            df.rename(columns={"id": "UUID", "serial": "Printed Serial"}, inplace=True)
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            zip_file.writestr("Ticket_Manifest.csv", csv_bytes)
        
        # Provide the download button
        st.success("✅ Archive generated successfully!")
        st.download_button(
            label="📦 Download ZIP for Print Shop",
            data=zip_buffer.getvalue(),
            file_name="SmartTec_Print_Batch.zip",
            mime="application/zip",
            type="primary"
        )
