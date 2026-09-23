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

# 1. Fetch Events (Fetching both 'id' and 'name' to link with the tickets table)
@st.cache_data(ttl=10)
def fetch_events():
    try:
        response = supabase.table('events').select('id, name').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Events fetch error: {e}")
        return []

# 2. Fetch Vendors
@st.cache_data(ttl=10)
def fetch_vendors():
    try:
        response = supabase.table('vendors').select('name').execute()
        return [vendor['name'] for vendor in response.data] if response.data else []
    except Exception as e:
        st.error(f"Vendors fetch error: {e}")
        return []

events_data = fetch_events()
event_names = [e['name'] for e in events_data if 'name' in e]
vendor_list = fetch_vendors()

selected_event_name = st.selectbox("Target Event", options=event_names)
selected_vendor = st.selectbox("Select Vendor", options=vendor_list)

# Match selected event name to its numeric ID
selected_event_id = None
for e in events_data:
    if e.get('name') == selected_event_name:
        selected_event_id = e.get('id')
        break

# 3. Fetch Ticket Types dynamically using the exact column names from your database
@st.cache_data(ttl=10)
def fetch_tickets(event_id):
    if not event_id:
        return {}
    try:
        # Querying the tickets table using 'ticket_type', 'price', and 'event_id'
        response = supabase.table('tickets').select('ticket_type, price').eq('event_id', event_id).execute()
        
        # The tickets table contains individual tickets, so we deduplicate them to get unique categories
        unique_tickets = {}
        if response.data:
            for row in response.data:
                t_type = row.get('ticket_type')
                if t_type and t_type not in unique_tickets:
                    unique_tickets[t_type] = row.get('price', 0.0)
        return unique_tickets
    except Exception as e:
        st.error(f"Database Error: {e}")
        return {}

tickets_dict = fetch_tickets(selected_event_id)
ticket_options = list(tickets_dict.keys())

# Dropdown for Ticket Type
selected_ticket = st.selectbox("Select Ticket Type / Tag String", options=ticket_options)

# 4. Auto-populate Price logic
auto_price = float(tickets_dict.get(selected_ticket, 0.00)) if selected_ticket else 0.00

# 5. Form Submission
with st.form("allocation_form"):
    col1, col2 = st.columns(2)
    with col1:
        initial_stock = st.number_input("Quantity Given", min_value=1, step=1)
    with col2:
        # The value is now dynamically driven by the auto_price variable
        price = st.number_input("Price (Pula)", value=auto_price, min_value=0.00, step=10.00, format="%.2f")
        
    submitted = st.form_submit_button("Issue to Vendor", type="primary")

    if submitted:
        if not selected_event_name or not selected_vendor or not selected_ticket:
            st.error("⚠️ Please select Event, Vendor, and Ticket Type.")
        else:
            clean_tag = selected_ticket.strip()
            
            # Check for existing allocation in inventory table
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
