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

# Match selected event name to its numeric ID
selected_event_id = None
if selected_event_name and selected_event_name != "No events found":
    for e in events_data:
        name = e.get('name') or e.get('event_name') or e.get('title')
        if name == selected_event_name:
            selected_event_id = e.get('id')
            break

# 3. Fetch ALL Ticket Types (using direct DB query for speed)
def fetch_all_ticket_types():
    unique_tickets = {}
    try:
        # Get a list of all unique ticket categories by scanning directly in Supabase
        response = supabase.table('tickets').select('ticket_type, price').execute()
        if response.data:
            for row in response.data:
                t_type = row.get('ticket_type')
                if t_type and t_type not in unique_tickets:
                    unique_tickets[t_type] = row.get('price', 0.0)
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
        if not selected_event_name or not selected_vendor or not selected_ticket:
            st.error("⚠️ Please select a valid Event, Vendor, and Ticket Type.")
        else:
            clean_tag = selected_ticket.strip()
            req_stock = int(initial_stock)
            
            try:
                available_tickets = []
                
                # --- DB-LEVEL VAULT SEARCH ---
                # 1. Search for tags where vendor_name is literally a Database NULL
                null_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).is_('vendor_name', 'null').limit(req_stock).execute()
                if null_response.data:
                    available_tickets.extend([t['id'] for t in null_response.data])
                
                # 2. If we need more, search for tags where vendor_name is just an empty string ""
                if len(available_tickets) < req_stock:
                    empty_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).eq('vendor_name', '').limit(req_stock - len(available_tickets)).execute()
                    if empty_response.data:
                        available_tickets.extend([t['id'] for t in empty_response.data])
                
                # 3. If we STILL need more, search for tags assigned to 'Main Gate'
                if len(available_tickets) < req_stock:
                    maingate_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).ilike('vendor_name', '%main gate%').limit(req_stock - len(available_tickets)).execute()
                    if maingate_response.data:
                        available_tickets.extend([t['id'] for t in maingate_response.data])

                # --- EVALUATE THE RESULTS ---
                if len(available_tickets) < req_stock:
                    st.error(f"⚠️ Vault Shortage: You requested {req_stock} tickets, but only {len(available_tickets)} unassigned '{clean_tag}' tags are available.")
                    st.info("💡 **Debug Tip:** Open your Supabase 'tickets' table and look at the 50 tags you just generated. Ensure their `vendor_name` column is empty, and their `ticket_type` is exactly 'Double'.")
                else:
                    # 1. Claim the physical tickets
                    tickets_to_assign = available_tickets[:req_stock]
                    
                    supabase.table('tickets') \
                        .update({'vendor_name': selected_vendor, 'status': 'With_Vendor'}) \
                        .in_('id', tickets_to_assign) \
                        .execute()
                    
                    # 2. Update the Inventory Summary
                    existing_response = supabase.table('inventory') \
                        .select('*') \
                        .eq('event_name', selected_event_name) \
                        .eq('vendor_name', selected_vendor) \
                        .eq('tag_type', clean_tag) \
                        .execute()
                        
                    if existing_response.data and len(existing_response.data) > 0:
                        existing_row = existing_response.data[0]
                        new_initial = existing_row.get('initial_stock', 0) + req_stock
                        new_stock = existing_row.get('stock_count', 0) + req_stock
                        
                        supabase.table('inventory').update({
                            'initial_stock': new_initial, 'stock_count': new_stock, 'price': price
                        }).eq('event_name', selected_event_name).eq('vendor_name', selected_vendor).eq('tag_type', clean_tag).execute()
                          
                        st.success(f"✅ VAULT TRANSFER SUCCESS: Moved {req_stock} physical '{clean_tag}' tags to {selected_vendor}. New Total: {new_initial}")
                    else:
                        supabase.table('inventory').insert({
                            'event_name': selected_event_name, 'vendor_name': selected_vendor, 'tag_type': clean_tag,
                            'initial_stock': req_stock, 'stock_count': req_stock, 'price': price
                        }).execute()
                        
                        st.success(f"✅ NEW VAULT TRANSFER: Moved {req_stock} physical '{clean_tag}' tags to {selected_vendor}.")
            except Exception as e:
                st.error(f"❌ Transaction Error: {str(e)}")
