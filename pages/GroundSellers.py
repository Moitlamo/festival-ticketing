import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client (update with your actual credentials/secrets mapping)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("M.Marumo Technologies")
st.subheader("Issue Vendor Allocation")

# 1. Fetch Initial Data for Dropdowns
@st.cache_data(ttl=60)
def fetch_events():
    response = supabase.table('events').select('name').execute()
    return [event['name'] for event in response.data] if response.data else []

@st.cache_data(ttl=60)
def fetch_vendors():
    response = supabase.table('vendors').select('name').execute()
    return [vendor['name'] for vendor in response.data] if response.data else []

event_list = fetch_events()
vendor_list = fetch_vendors()

# 2. Allocation Form
with st.form("allocation_form"):
    selected_event = st.selectbox("Target Event", options=event_list)
    selected_vendor = st.selectbox("Select Vendor", options=vendor_list)
    tag_type = st.text_input("QR Tag String (Must match static QR)", placeholder="e.g. SUMMER_COOLERBOX")
    
    col1, col2 = st.columns(2)
    with col1:
        initial_stock = st.number_input("Quantity Given", min_value=1, step=1)
    with col2:
        price = st.number_input("Price (Pula)", min_value=0.00, step=10.00, format="%.2f")
        
    submitted = st.form_submit_button("Issue to Vendor", type="primary")

    if submitted:
        if not selected_event or not selected_vendor or not tag_type:
            st.error("⚠️ Please fill in all fields.")
        else:
            clean_tag = tag_type.strip()
            
            # Check for existing allocation
            existing_response = supabase.table('inventory') \
                .select('*') \
                .eq('event_name', selected_event) \
                .eq('vendor_name', selected_vendor) \
                .eq('tag_type', clean_tag) \
                .execute()
                
            if existing_response.data and len(existing_response.data) > 0:
                # REFILL LOGIC
                existing_row = existing_response.data[0]
                new_initial = existing_row.get('initial_stock', 0) + initial_stock
                new_stock = existing_row.get('stock_count', 0) + initial_stock
                
                try:
                    supabase.table('inventory').update({
                        'initial_stock': new_initial,
                        'stock_count': new_stock,
                        'price': price
                    }).eq('event_name', selected_event) \
                      .eq('vendor_name', selected_vendor) \
                      .eq('tag_type', clean_tag).execute()
                      
                    st.success(f"✅ REFILL SUCCESS: Added {initial_stock} to {selected_vendor}'s {clean_tag} batch. New Total: {new_initial}")
                except Exception as e:
                    st.error(f"❌ Update Error: {str(e)}")
                    
            else:
                # NEW ASSIGNMENT LOGIC
                try:
                    supabase.table('inventory').insert({
                        'event_name': selected_event,
                        'vendor_name': selected_vendor,
                        'tag_type': clean_tag,
                        'initial_stock': initial_stock,
                        'stock_count': initial_stock,
                        'price': price
                    }).execute()
                    
                    st.success(f"✅ NEW ASSIGNMENT: Issued {initial_stock} {clean_tag} tags to {selected_vendor}.")
                except Exception as e:
                    st.error(f"❌ Insert Error: {str(e)}")
