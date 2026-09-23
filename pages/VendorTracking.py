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

st.title("📊 Vendor Sales & Tracking Portal")
st.markdown("Track seller inventory, tickets sold, and total cash due in real-time.")

# 1. Fetch all inventory data
def fetch_inventory():
    try:
        response = supabase.table('inventory').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching inventory: {e}")
        return []

inventory_data = fetch_inventory()

if not inventory_data:
    st.info("No vendor allocations found. Issue tickets to vendors first to see tracking data.")
else:
    # Convert database response to a Pandas DataFrame for easy math and filtering
    df = pd.DataFrame(inventory_data)
    
    # Calculate tracking metrics
    df['Sold Qty'] = df['initial_stock'] - df['stock_count']
    df['Cash Due (Pula)'] = df['Sold Qty'] * df['price']
    df['Total Stock Value (Pula)'] = df['initial_stock'] * df['price']
    
    # Rename columns for a clean, professional display
    display_df = df.rename(columns={
        'event_name': 'Event',
        'vendor_name': 'Seller Name',
        'tag_type': 'Ticket Type',
        'initial_stock': 'Issued Qty',
        'stock_count': 'Remaining Qty',
        'price': 'Price (Pula)'
    })
    
    # 2. Global Event Filter
    events_list = display_df['Event'].unique().tolist()
    events_list.insert(0, "All Events")
    
    selected_filter = st.selectbox("Filter by Event", events_list)
    
    if selected_filter != "All Events":
        filtered_df = display_df[display_df['Event'] == selected_filter]
    else:
        filtered_df = display_df

    # 3. Top Level Financial & Inventory Metrics
    st.markdown("### 📈 Overall Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    total_issued = int(filtered_df['Issued Qty'].sum())
    total_sold = int(filtered_df['Sold Qty'].sum())
    total_remaining = int(filtered_df['Remaining Qty'].sum())
    total_cash_due = float(filtered_df['Cash Due (Pula)'].sum())
    
    col1.metric("Total Tickets Issued", f"{total_issued}")
    col2.metric("Total Tickets Sold", f"{total_sold}")
    col3.metric("Tickets Remaining", f"{total_remaining}")
    col4.metric("Total Cash Due", f"P {total_cash_due:,.2f}")

    st.divider()

    # 4. Detailed Seller Breakdown
    st.markdown("### 🧑‍💼 Seller Breakdown")
    
    # Rearrange columns so the most important financial data is at the front
    final_table = filtered_df[[
        'Seller Name', 'Ticket Type', 'Event', 'Price (Pula)', 
        'Issued Qty', 'Sold Qty', 'Remaining Qty', 'Cash Due (Pula)'
    ]]
    
    # Sort by Cash Due so the sellers owing the most money are at the top
    final_table = final_table.sort_values(by=['Seller Name', 'Ticket Type'])
    
    # Display the interactive dataframe
    st.dataframe(
        final_table.style.format({
            "Price (Pula)": "{:.2f}",
            "Cash Due (Pula)": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # 5. Quick Summary by Vendor (Aggregated)
    st.markdown("### 💰 Consolidated Vendor Liabilities")
    # Group by Seller to see total cash owed regardless of ticket type
    vendor_summary = filtered_df.groupby('Seller Name').agg(
        Total_Tickets_Sold=('Sold Qty', 'sum'),
        Total_Cash_Due=('Cash Due (Pula)', 'sum')
    ).reset_index()
    
    vendor_summary = vendor_summary.sort_values(by='Total_Cash_Due', ascending=False)
    
    st.dataframe(
        vendor_summary.style.format({
            "Total_Cash_Due": "P {:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
