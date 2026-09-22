import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Initialize Supabase Client
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Supabase connection failed. Check your secrets. Error: {e}")

st.markdown("<h2 style='color: #8B0000;'>M.Marumo Technologies - Promoter Dashboard</h2>", unsafe_allow_html=True)
st.write("Real-time tracking of digital ticket sales and physical gate inventory.")

# 2. Event Selection
try:
    if 'supabase' in locals():
        events_res = supabase.table("events").select("name").execute()
        event_options = [e["name"] for e in events_res.data] if events_res.data else []
    else:
        event_options = []
except Exception:
    event_options = []

if not event_options:
    event_options = ["Leririma Games", "Mahalapye East Finals", "Taupye Soccer Tournament"]

event_name = st.selectbox("Select Event to View", event_options)

st.divider()

if event_name:
    # -------------------------------------------------------------------------
    # SECTION A: DIGITAL TICKET SALES
    # -------------------------------------------------------------------------
    st.markdown("<h3 style='color: #1E3A8A;'>Digital Ticket Sales</h3>", unsafe_allow_html=True)
    
    try:
        tickets_res = supabase.table("tickets").select("*").eq("event_name", event_name).execute()
        digital_data = tickets_res.data
    except Exception as e:
        digital_data = []
        st.warning(f"Could not load digital tickets. Ensure 'tickets' table exists. ({e})")

    if digital_data:
        df_digital = pd.DataFrame(digital_data)
        
        total_digital_sold = len(df_digital)
        total_digital_revenue = df_digital["price"].sum() if "price" in df_digital.columns else 0.0
        
        col1, col2 = st.columns(2)
        col1.metric("Total Digital Tickets Sold", total_digital_sold)
        col2.metric("Digital Revenue (BWP)", f"P{total_digital_revenue:,.2f}")
        
        with st.expander("View Digital Ticket Details"):
            st.dataframe(df_digital, use_container_width=True, hide_index=True)
    else:
        st.info("No digital ticket sales recorded for this event yet.")

    st.divider()

    # -------------------------------------------------------------------------
    # SECTION B: PHYSICAL GATE TAGS (INVENTORY TRACKER)
    # -------------------------------------------------------------------------
    st.markdown("<h3 style='color: #1E3A8A;'>Physical Gate Tags (Inventory Tracker)</h3>", unsafe_allow_html=True)
    
    try:
        inventory_res = supabase.table("inventory").select("*").eq("event_name", event_name).execute()
        inventory_data = inventory_res.data
    except Exception as e:
        inventory_data = []
        st.error(f"Could not load physical inventory: {e}")

    if inventory_data:
        df_inv = pd.DataFrame(inventory_data)
        
        df_inv["Display Name"] = df_inv["tag_type"].apply(
            lambda x: x.split('_')[-2] + " " + x.split('_')[-1] if '_' in x else x
        )
        
        df_inv["Unsold Value (BWP)"] = df_inv["price"] * df_inv["stock_count"]
        
        total_remaining_tags = df_inv["stock_count"].sum()
        total_unsold_value = df_inv["Unsold Value (BWP)"].sum()

        col3, col4 = st.columns(2)
        col3.metric("Physical Tags Remaining at Gate", int(total_remaining_tags))
        col4.metric("Value of Remaining Stock (BWP)", f"P{total_unsold_value:,.2f}")

        st.dataframe(
            df_inv[["Display Name", "price", "stock_count", "Unsold Value (BWP)"]].rename(
                columns={
                    "price": "Unit Price (BWP)", 
                    "stock_count": "Tags Remaining at Gate"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No physical tags have been allocated for this event yet.")

    st.divider()

    # -------------------------------------------------------------------------
    # SECTION C: GRAND TOTALS
    # -------------------------------------------------------------------------
    if digital_data or inventory_data:
        st.markdown("<h3 style='color: #8B0000;'>Event Grand Totals</h3>", unsafe_allow_html=True)
        
        calc_digital_rev = df_digital["price"].sum() if digital_data and "price" in df_digital.columns else 0.0
        calc_unsold_phys = total_unsold_value if inventory_data else 0.0
        
        grand_total_potential = calc_digital_rev + calc_unsold_phys
        
        st.metric(
            label="Total Potential Revenue (Digital Sold + Physical Remaining)", 
            value=f"P{grand_total_potential:,.2f}"
        )
