import streamlit as st
import pandas as pd
import re
from models import SessionLocal, Ticket

st.set_page_config(page_title="Batch Ledger & Audit", layout="wide")

# Maintain the dark red and deep blue UI aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stSelectbox>div>div>select, .stTextInput>div>div>input { background-color: #1e293b; color: white; }
    .stButton>button { background-color: #1e3a8a; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #1e40af; color: white; }
    .dl-button>button { background-color: #7f1d1d; color: white; width: 100%; }
    .dl-button>button:hover { background-color: #991b1b; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Master Batch Ledger")
st.write("Audit all physical ticket batches, track vendor inventory, and recover lost CSV exports.")

db = SessionLocal()
try:
    # Query all physical tickets generated for vendors
    physical_tickets = db.query(Ticket).filter(Ticket.ticket_type == "Physical").all()
    
    if not physical_tickets:
        st.info("No physical vendor batches have been generated yet.")
        st.stop()
        
    # --- PARSE BATCH METADATA ---
    batch_data = []
    for t in physical_tickets:
        parts = str(t.buyer_phone).split(" | ")
        
        event_name = "Unknown Event"
        vendor_name = "Unknown Vendor"
        ticket_value = "Unknown Value"
        
        for p in parts:
            if "Event:" in p: event_name = p.replace("Event:", "").strip()
            if "Vendor:" in p: vendor_name = p.replace("Vendor:", "").split("[")[0].strip()
            if "Value:" in p: ticket_value = p.replace("Value:", "").strip()
            
        batch_data.append({
            "Ticket ID": t.ticket_id,
            "Event": event_name,
            "Vendor": vendor_name,
            "Value": ticket_value,
            "Status": t.status,
            "PIN": t.security_pin
        })
        
    df = pd.DataFrame(batch_data)
    
    # --- FILTER CONTROLS ---
    col1, col2 = st.columns(2)
    with col1:
        event_filter = st.selectbox("Filter by Event", ["All Events"] + list(df["Event"].unique()))
    with col2:
        vendor_filter = st.selectbox("Filter by Vendor", ["All Vendors"] + list(df["Vendor"].unique()))
        
    # Apply Filters
    if event_filter != "All Events":
        df = df[df["Event"] == event_filter]
    if vendor_filter != "All Vendors":
        df = df[df["Vendor"] == vendor_filter]

    st.markdown("---")
    
    # --- BATCH SUMMARY AGGREGATION ---
    st.subheader("Batch Inventory Summary")
    # Group the data to show total counts per Vendor/Event/Value pairing
    summary_df = df.groupby(["Event", "Vendor", "Value"]).agg(
        Total_Printed=('Ticket ID', 'count'),
        Unsold_With_Vendor=('Status', lambda x: (x == 'With_Vendor').sum()),
        Sold_To_Fans=('Status', lambda x: (x == 'Sold').sum()),
        Scanned_At_Gate=('Status', lambda x: (x == 'Used').sum())
    ).reset_index()
    
    st.dataframe(summary_df, use_container_width=True)
    
    st.markdown("---")
    
    # --- BATCH RECOVERY / DOWNLOAD ---
    st.subheader("Recover Batch CSVs")
    st.write("Select a specific vendor batch below to regenerate and download its ticket codes.")
    
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        dl_event = st.selectbox("Select Event", df["Event"].unique(), key="dl_e")
    with rc2:
        # Filter vendors based on selected event
        valid_vendors = df[df["Event"] == dl_event]["Vendor"].unique()
        dl_vendor = st.selectbox("Select Vendor", valid_vendors, key="dl_v")
    with rc3:
        # Filter values based on selected event and vendor
        valid_values = df[(df["Event"] == dl_event) & (df["Vendor"] == dl_vendor)]["Value"].unique()
        dl_value = st.selectbox("Select Tier", valid_values, key="dl_val")
        
    # Isolate the exact batch to download
    export_df = df[(df["Event"] == dl_event) & (df["Vendor"] == dl_vendor) & (df["Value"] == dl_value)]
    
    # Format for download (matching standard output)
    csv_export = export_df[["Ticket ID", "PIN", "Event", "Vendor", "Value", "Status"]].to_csv(index=False).encode('utf-8')
    
    st.write("")
    st.markdown('<div class="dl-button">', unsafe_allow_html=True)
    st.download_button(
        label=f"📥 Download {dl_vendor} - {dl_value} Batch ({len(export_df)} Tickets)",
        data=csv_export,
        file_name=f"Recovered_Batch_{dl_vendor}_{dl_event}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading batch ledger: {e}")
finally:
    db.close()
