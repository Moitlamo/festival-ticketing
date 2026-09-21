import streamlit as st
import qrcode
from io import BytesIO

st.markdown("<h2 style='color: #8B0000;'>M.Marumo Technologies - Desk Tag Generator</h2>", unsafe_allow_html=True)
st.write("Generate static desk codes, set ticket prices, and allocate inventory for specific events.")

def create_static_qr(tag_string: str) -> BytesIO:
    """Generates a high-res static QR code for the desk scanners."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15, 
        border=4,
    )
    qr.add_data(tag_string)
    qr.make(fit=True)

    # Deep blue visual theme
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# 1. Event Selection & Financials
st.subheader("1. Event & Financial Details")
col_event, col_price = st.columns(2)

with col_event:
    event_name = st.text_input("Event Name", placeholder="e.g., Leririma Games")

with col_price:
    ticket_price = st.number_input("Ticket Value (BWP)", min_value=0.0, value=50.0, step=10.0)

# 2. Expanded Tag Categories
st.subheader("2. Tag Allocation")
available_tags = {
    "VIP": "VIP_TAG",
    "Standard": "STANDARD_TAG",
    "Kids": "KIDS_TAG",
    "Staff / Vendor": "STAFF_TAG",
    "Double": "DOUBLE_TAG",
    "CoolerBox": "COOLERBOX_TAG"
}

selected_label = st.selectbox("Select Tag Category", list(available_tags.keys()))
stock_count = st.number_input(f"Number of {selected_label} tags to allocate (Starting Stock)", min_value=1, value=50, step=1)

# 3. Generation Logic
if event_name:
    # Create a unique QR string tied strictly to this event to prevent cross-event scanning errors
    safe_event_prefix = event_name.replace(" ", "").upper()
    exact_qr_string = f"{safe_event_prefix}_{available_tags[selected_label]}"
    total_value = stock_count * ticket_price
    
    st.info(f"Master Desk Code: **{exact_qr_string}** | Unit Price: **P{ticket_price:,.2f}** | Total Potential Revenue: **P{total_value:,.2f}**")

    if st.button(f"Generate & Allocate {selected_label} Inventory"):
        
        # Update Supabase Inventory Pool
        try:
            supabase.table("inventory").upsert({
                "tag_type": exact_qr_string,
                "event_name": event_name,
                "price": ticket_price,
                "stock_count": stock_count
            }).execute()
            
            st.success(f"Successfully allocated {stock_count} {selected_label} tags for '{event_name}' at P{ticket_price:,.2f} each.")
        except Exception as e:
            st.warning(f"Database warning: Please ensure 'event_name' and 'price' columns exist in your Supabase 'inventory' table. Error: {e}")

        # Generate the Printable QR Code
        qr_buffer = create_static_qr(exact_qr_string)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(qr_buffer, caption=f"{event_name} - {selected_label}", use_column_width=True)
            
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
                file_name=f"{safe_event_prefix}_Desk_Code_{available_tags[selected_label]}.png",
                mime="image/png",
                type="primary"
            )
else:
    st.warning("Please enter an Event Name to generate tags.")
