import streamlit as st
import pandas as pd
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

# 2. Fetch Vendors AND Map their Numeric IDs
def fetch_vendors():
    try:
        response = supabase.table('vendors').select('*').execute()
        vendor_map = {}
        if response.data:
            for v in response.data:
                name = v.get('name') or v.get('vendor_name') or v.get('full_name')
                if name:
                    vendor_map[name] = v.get('id')
        return vendor_map
    except Exception as e:
        st.error(f"Vendors fetch error: {e}")
        return {}

events_data = fetch_events()
event_names = [e.get('name') or e.get('event_name') or e.get('title') for e in events_data if e]

vendor_mapping = fetch_vendors()
vendor_list = list(vendor_mapping.keys())

selected_event_name = st.selectbox("Target Event", options=event_names if event_names else ["No events found"])
selected_vendor = st.selectbox("Select Vendor", options=vendor_list if vendor_list else ["No vendors found"])

# Match selected event name and vendor to their numeric IDs
selected_event_id = None
if selected_event_name and selected_event_name != "No events found":
    for e in events_data:
        name = e.get('name') or e.get('event_name') or e.get('title')
        if name == selected_event_name:
            selected_event_id = e.get('id')
            break
            
selected_vendor_id = vendor_mapping.get(selected_vendor)

# Dynamically find the numeric ID for Main Gate
maingate_id = None
for key, val in vendor_mapping.items():
    if "main gate" in str(key).lower():
        maingate_id = val
        break

# 3. Fetch ALL Ticket Types
def fetch_all_ticket_types():
    unique_tickets = {}
    try:
        limit = 1000
        offset = 0
        while True:
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
        if not selected_event_name or not selected_vendor or not selected_ticket:
            st.error("⚠️ Please select a valid Event, Vendor, and Ticket Type.")
        else:
            clean_tag = selected_ticket.strip()
            req_stock = int(initial_stock)
            
            try:
                available_tickets = []
                
                # --- WIDE NET VAULT SEARCH ---
                # 1. Search for NULL vendor_id
                null_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).is_('vendor_id', 'null').limit(req_stock).execute()
                if null_response.data:
                    available_tickets.extend([t['id'] for t in null_response.data])
                
                # 2. Search for Main Gate's specific numeric ID
                if maingate_id and len(available_tickets) < req_stock:
                    mg_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).eq('vendor_id', maingate_id).limit(req_stock - len(available_tickets)).execute()
                    if mg_response.data:
                        available_tickets.extend([t['id'] for t in mg_response.data])
                        
                # 3. Search for vendor_id = 0 (sometimes used as default unassigned)
                if len(available_tickets) < req_stock:
                    zero_response = supabase.table('tickets').select('id').eq('ticket_type', clean_tag).eq('vendor_id', 0).limit(req_stock - len(available_tickets)).execute()
                    if zero_response.data:
                        available_tickets.extend([t['id'] for t in zero_response.data])

                # --- EVALUATE THE RESULTS ---
                if len(available_tickets) < req_stock:
                    st.error(f"⚠️ Vault Shortage: You requested {req_stock} tickets, but only {len(available_tickets)} unassigned '{clean_tag}' tags are available.")
                    
                    # --- AUTO-DEBUGGER ---
                    st.warning("🔍 **SYSTEM DIAGNOSTIC TRIGGERED**")
                    debug_res = supabase.table('tickets').select('id, vendor_id, status, event_id').eq('ticket_type', clean_tag).limit(10).execute()
                    
                    if debug_res.data:
                        st.write(f"The database found these '{clean_tag}' tags, but they are blocked from allocation. Here is their hidden data:")
                        st.dataframe(pd.DataFrame(debug_res.data))
                        st.info("👉 **Look at the `vendor_id` column above.** If it has a number (like 4 or 8), those tags are already owned by another vendor. If you want to issue them, you must update the generator to leave that ID blank, or add that specific ID to the vault rules.")
                    else:
                        st.error(f"❌ CRITICAL: The database contains absolutely 0 tags named '{clean_tag}'. Check if the generator actually created them, or if it used a different spelling.")
                else:
                    # 1. Claim the physical tickets by assigning the numeric vendor_id
                    tickets_to_assign = available_tickets[:req_stock]
                    
                    supabase.table('tickets') \
                        .update({'vendor_id': selected_vendor_id, 'status': 'With_Vendor'}) \
                        .in_('id', tickets_to_assign) \
                        .execute()
                    
                    # 2. Update the Inventory Summary Table
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
