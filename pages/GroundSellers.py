import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("Issue Vendor Allocation")

# 1. Fetch Events
def fetch_events():
    try:
        response = supabase.table('events').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Events fetch error: {e}")
        return []

# 2. Fetch Vendors
def fetch_vendors():
    try:
        response = supabase.table('vendors').select('*').execute()
        vendor_names = []
        if response.data:
            for v in response.data:
                name = v.get('name') or v.get('vendor_name') or v.get('full_name')
                if name:
                    vendor_names.append(name)
        return vendor_names
    except Exception as e:
        st.error(f"Vendors fetch error: {e}")
        return []

events_data = fetch_events()
event_names = [e.get('name') or e.get('event_name') or e.get('title') for e in events_data if e]
vendor_list = fetch_vendors()

selected_event_name = st.selectbox("Target Event", options=event_names if event_names else ["No events found"])
selected_vendor = st.selectbox("Select Vendor", options=vendor_list if vendor_list else ["No vendors found"])

# 3. Fetch ALL Ticket Types using Pagination (Only requesting columns that exist)
def fetch_all_ticket_types():
    unique_tickets = {}
    try:
        limit = 1000
        offset = 0
        # Loop through the entire table in chunks to find every single ticket category
        while True:
            # FIXED: Removed 'name' and 'tag_type' to prevent database rejection
            response = supabase.table('tickets').select('ticket_type, price').range(offset, offset + limit - 1).execute()
            data = response.data
            
            if not data:
                break
                
            for row in data:
                t_type = row.get('ticket_type')
                if t_type and t_type not in unique_tickets:
                    unique_tickets[t_type] = row.get('price', 0.0)
                    
            if len(data) < limit:
                break
            offset += limit
            
        return unique_tickets
    except Exception as e:
        st.error(f"Database Error: {e}")
        return {}

tickets_dict = fetch_all_ticket_types()
ticket_options = list(tickets_dict.keys())

# Dropdown for Ticket Type
selected_ticket = st.selectbox("Select Ticket Type / Tag String", options=ticket_options if ticket_options else ["No tickets found"])

# 4. Auto-populate Price logic
auto_price = float(tickets_dict.get(selected_ticket, 0.00)) if selected_ticket and selected_ticket != "No tickets found" else 0.00

# 5. Form Submission
with st.form("allocation_form"):
    col1, col2 = st.columns(2)
    with col1:
        initial_stock = st.number_input("Quantity Given", min_value=1, step=1)
    with col2:
        price = st.number_input("Price (Pula)", value=auto_price, min_value=0.00, step=10.00, format="%.2f")
        
    submitted = st.form_submit_button("Issue to Vendor", type="primary")

    if submitted:
        if not selected_event_name or selected_event_name == "No events found" or \
           not selected_vendor or selected_vendor == "No vendors found" or \
           not selected_ticket or selected_ticket == "No tickets found":
            st.error("⚠️ Please select a valid Event, Vendor, and Ticket Type.")
        else:
            clean_tag = selected_ticket.strip()
            
            # Check for existing allocation
            existing_response = supabase.table('inventory') \
                .select('*') \
                .eq('event_name', selected_event_name) \
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
                    }).eq('event_name', selected_event_name) \
                      .eq('vendor_name', selected_vendor) \
                      .eq('tag_type', clean_tag).execute()
                      
                    st.success(f"✅ REFILL SUCCESS: Added {initial_stock} to {selected_vendor}'s {clean_tag} batch. New Total: {new_initial}")
                except Exception as e:
                    st.error(f"❌ Update Error: {str(e)}")
                    
            else:
                # NEW ASSIGNMENT LOGIC
                try:
                    supabase.table('inventory').insert({
                        'event_name': selected_event_name,
                        'vendor_name': selected_vendor,
                        'tag_type': clean_tag,
                        'initial_stock': initial_stock,
                        'stock_count': initial_stock,
                        'price': price
                    }).execute()
                    
                    st.success(f"✅ NEW ASSIGNMENT: Issued {initial_stock} {clean_tag} tags to {selected_vendor}.")
                except Exception as e:
                    st.error(f"❌ Insert Error: {str(e)}")
