import streamlit as st
import qrcode
from io import BytesIO

st.markdown("<h2 style='color: #8B0000;'>M.Marumo Technologies - Desk Tag Generator</h2>", unsafe_allow_html=True)
st.write("Generate the static QR codes to be printed and taped to the gate desks for inventory tracking.")

def create_static_qr(tag_string: str) -> BytesIO:
    """Generates a static QR code for the desk scanners."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15, # Larger box size for high-quality printing
        border=4,
    )
    qr.add_data(tag_string)
    qr.make(fit=True)

    # Applying the deep blue visual theme for clear scanning
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# 1. Define the temporary tags needed for this specific event
available_tags = {
    "VIP": "VIP_TAG",
    "Standard": "STANDARD_TAG",
    "Kids": "KIDS_TAG",
    "Staff / Vendor": "STAFF_TAG"
}

# 2. UI for selection
selected_label = st.selectbox("Select Tag Category to Generate", list(available_tags.keys()))
exact_qr_string = available_tags[selected_label]

st.info(f"This will generate a QR code containing exactly: **{exact_qr_string}**")

# 3. Generate and Download
if st.button(f"Generate {selected_label} Desk QR Code"):
    qr_buffer = create_static_qr(exact_qr_string)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(qr_buffer, caption=f"Master Code: {selected_label}", use_column_width=True)
        
    with col2:
        st.success("QR Code Generated Successfully.")
        st.markdown(
            """
            **Instructions for the Gate:**
            1. Download this image.
            2. Print it on standard A4 paper.
            3. Tape it securely to the admissions desk.
            4. Bouncers will scan this exact code each time they hand out a physical tag.
            """
        )
        
        st.download_button(
            label=f"📥 Download Print-Ready {selected_label} QR",
            data=qr_buffer,
            file_name=f"Master_Desk_Code_{exact_qr_string}.png",
            mime="image/png",
            type="primary"
        )
