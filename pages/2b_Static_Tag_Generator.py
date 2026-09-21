import streamlit as st
import qrcode
from io import BytesIO

st.markdown("<h2 style='color: #8B0000;'>M.Marumo Technologies - Desk Tag Generator</h2>", unsafe_allow_html=True)
st.write("Generate static desk codes and allocate the initial gate inventory for depletion.")

def create_static_qr(tag_string: str) -> BytesIO:
    """Generates a static QR code for the desk scanners."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15, 
        border=4,
    )
    qr.add_data(tag_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# 1. Expanded Tag Categories
available_tags = {
    "VIP": "VIP_TAG",
    "Standard": "STANDARD_TAG",
    "Kids": "KIDS_TAG",
    "Staff / Vendor": "STAFF_TAG",
    "Double": "DOUBLE_TAG",
    "CoolerBox": "COOLERBOX_TAG"
}

selected_label = st.selectbox("Select Tag Category to Generate", list(available_tags.keys()))
exact_qr_string = available_tags[selected_label]

# 2. Inventory Allocation Input
# This sets the database stock so the gate scanner has a pool to deplete from
stock_count = st.number_input(f"Number of {selected_label} tags to allocate (Starting Stock)", min_value=1, value=50, step=1)

st.info(f"This will set the database starting stock to **{stock_count}** and generate the master desk code: **{exact_qr_string}**")

if st.button(f"Generate & Allocate {selected_label} Inventory"):
    
    # 3. Update Supabase Inventory Pool
    # Make sure 'supabase' is imported and initialized at the top of your file
    try:
        # Upsert requires 'tag_type' to be a unique column or primary key in your inventory table
        supabase.table("inventory").upsert({
            "tag_type": exact_qr_string,
            "stock_count": stock_count
        }).execute()
        st.success(f"Successfully allocated {stock_count} {selected_label} tags to the database.")
    except Exception as e:
        st.warning(f"Database update skipped. Ensure the 'inventory' table exists and supabase is connected. Error: {e}")

    # 4. Generate the Printable QR Code
    qr_buffer = create_static_qr(exact_qr_string)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(qr_buffer, caption=f"Master Code: {selected_label}", use_column_width=True)
        
    with col2:
        st.markdown(
            """
            **Instructions for the Gate:**
            1. Download this image.
            2. Print copies for your gate staff.
            3. Bouncers will scan this exact code to deduct from the allocated stock.
            """
        )
        
        st.download_button(
            label=f"📥 Download Print-Ready {selected_label} QR",
            data=qr_buffer,
            file_name=f"Master_Desk_Code_{exact_qr_string}.png",
            mime="image/png",
            type="primary"
        )
