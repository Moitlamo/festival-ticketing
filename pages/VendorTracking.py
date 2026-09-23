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
    # Convert database response to a Pandas DataFrame
    df = pd.DataFrame(inventory_data)
    
    # Calculate tracking metrics
    df['Sold Qty'] = df['initial_stock'] - df['stock_count']
    df['Cash Due (Pula)'] = df['Sold Qty'] * df['price']
    df['Total Stock Value (Pula)'] = df['initial_stock'] * df['price']
    
    # Rename columns for display
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

    # --- SPLIT THE DATA: MASTER VAULT vs GROUND SELLERS ---
    master_df = filtered_df[filtered_df['Seller Name'].str.strip().str.lower() == 'main gate']
    sellers_df = filtered_df[filtered_df['Seller Name'].str.strip().str.lower() != 'main gate']

    # 3. Master Vault (Main Gate) Section
    st.divider()
    st.markdown("## 🏦 Master Vault (Main Gate Inventory)")
    
    if not master_df.empty:
        col1, col2 = st.columns(2)
        total_vault_stock = int(master_df['Remaining Qty'].sum())
        total_vault_value = float(master_df['Remaining Qty'].sum() * master_df['Price (Pula)'].mean()) # Approximated value
        
        col1.metric("Bulk Tickets Remaining in Vault", f"{total_vault_stock}")
        
        master_display = master_df[['Ticket Type', 'Event', 'Price (Pula)', 'Remaining Qty']]
        st.dataframe(
            master_display.style.format({"Price (Pula)": "{:.2f}"}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No 'Main Gate' inventory found for this event.")

    st.divider()

    # 4. Ground Sellers Section
    st.markdown("## 🧑‍💼 Active Ground Sellers")
    
    if not sellers_df.empty:
        # Top Level Financial & Inventory Metrics for SELLERS ONLY
        st.markdown("### 📈 Ground Seller Performance")
        col1, col2, col3, col4 = st.columns(4)
        
        total_issued = int(sellers_df['Issued Qty'].sum())
        total_sold = int(sellers_df['Sold Qty'].sum())
        total_remaining = int(sellers_df['Remaining Qty'].sum())
        total_cash_due = float(sellers_df['Cash Due (Pula)'].sum())
        
        col1.metric("Total Tickets Issued", f"{total_issued}")
        col2.metric("Total Tickets Sold", f"{total_sold}")
        col3.metric("Tickets Held by Sellers", f"{total_remaining}")
        col4.metric("Total Cash Due", f"P {total_cash_due:,.2f}")

        # Detailed Seller Breakdown
        st.markdown("### 📋 Seller Breakdown")
        final_table = sellers_df[[
            'Seller Name', 'Ticket Type', 'Event', 'Price (Pula)', 
            'Issued Qty', 'Sold Qty', 'Remaining Qty', 'Cash Due (Pula)'
        ]].sort_values(by=['Seller Name', 'Ticket Type'])
        
        st.dataframe(
            final_table.style.format({
                "Price (Pula)": "{:.2f}",
                "Cash Due (Pula)": "{:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Consolidated Vendor Liabilities
        st.markdown("### 💰 Consolidated Cash Owed (By Seller)")
        vendor_summary = sellers_df.groupby('Seller Name').agg(
            Total_Tickets_Sold=('Sold Qty', 'sum'),
            Total_Cash_Due=('Cash Due (Pula)', 'sum')
        ).reset_index().sort_values(by='Total_Cash_Due', ascending=False)
        
        st.dataframe(
            vendor_summary.style.format({
                "Total_Cash_Due": "P {:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No ground sellers have been issued tickets yet.")
