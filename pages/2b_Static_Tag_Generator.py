import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client

# Initialize Supabase client
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Supabase connection failed. Check your secrets. Error: {e}")

st.markdown("<h2 style='color: #8B0000;'>M.Marumo Technologies - Desk Tag Generator</h2>", unsafe_allow_html=True)
st.write("Generate static desk codes, set ticket prices, and allocate inventory for specific events.")

def create_static_qr(tag_string: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=15, border=4)
    qr.add_data(tag_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

st.subheader("1. Event & Financial Details")
col_event, col_price = st.columns(2)

with col_event:
    try:
        if 'supabase' in locals():
            events_res = supabase.table("events").select("name").execute()
            event_options = [e["name"] for e in events_res.data] if events_res.data else []
        else:
            event_options = []
    except Exception as e:
        event_options = []
        
    if not event_options:
        event_options = ["Leririma Games", "Mahalapye East Finals", "Taupye Soccer Tournament"]

    event_name = st.selectbox("Event Name", event_options)

with col_price:
    ticket_price = st.number_input("Ticket Value (BWP)", min_value=0.0, value=50.0, step=10.0)

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

if event_name:
    safe_event_prefix = event_name.replace(" ", "").upper()
    exact_qr_string = f"{safe_event_prefix}_DEPLETION_{available_tags[selected_label]}"
    total_value = stock_count * ticket_price
    
    st.info(f"Master Desk Code: **{exact_qr_string}** | Unit Price: **P{ticket_price:,.2f}** | Total Potential Revenue: **P{total_value:,.2f}**")

    if st.button(f"Generate & Allocate {selected_label} Inventory"):
        
        # Update Supabase Inventory Pool
        if 'supabase' in locals():
            try:
                supabase.table("inventory").upsert({
                    "tag_type": exact_qr_string,
                    "event_name": event_name,
                    "price": ticket_price,
                    "stock_count": stock_count
                }).execute()
                st.success(f"Successfully allocated {stock_count} {selected_label} tags for '{event_name}' at P{ticket_price:,.2f} each.")
            except Exception as e:
                st.warning(f"Database warning: Could not save inventory. Error: {e}")

        # Generate and store in session state to prevent TypeError and vanishing buttons
        qr_buffer = create_static_qr(exact_qr_string)
        st.session_state['qr_data'] = qr_buffer.getvalue()  # Extracts raw bytes safely
        st.session_state['qr_filename'] = f"{safe_event_prefix}_Desk_Code_{available_tags[selected_label]}.png"
        st.session_state['qr_label'] = selected_label
        st.session_state['qr_event'] = event_name

    # Display UI safely from session state OUTSIDE the button
    if 'qr_data' in st.session_state:
        st.divider()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(st.session_state['qr_data'], caption=f"{st.session_state['qr_event']} - {st.session_state['qr_label']}", use_container_width=True)
            
        with col2:
            st.markdown(
                """
                **Instructions for the Gate:**
                1. Download this image using the button below.
                2. Print copies on standard A4 paper for your gate staff.
                3. Bouncers will scan this exact code to deduct from the allocated stock.
                """
            )
            
            st.download_button(
                label="📥 Download Print-Ready QR Code",
                data=st.session_state['qr_data'],
                file_name=st.session_state['qr_filename'],
                mime="image/png",
                type="primary"
            )
else:
    st.warning("Please enter an Event Name to generate tags.")
