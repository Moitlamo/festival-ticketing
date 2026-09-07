import streamlit as st
import re
from models import SessionLocal, Ticket

st.set_page_config(page_title="Festival Command Center", page_icon="🎟️", layout="wide")

st.title("🎟️ Festival Command Center")

session = SessionLocal()
try:
    all_tickets = session.query(Ticket).all()
    
    # 1. Filter tickets by their live status
    sold_tickets = [t for t in all_tickets if t.status in ["Sold", "Used"]]
    scanned_tickets = [t for t in all_tickets if t.status == "Used"]
    
    # 2. Calculate Revenue Streams
    electronic_revenue = 0
    vendor_cash_owed = 0
    
    for t in sold_tickets:
        # Extract the numeric price from the ticket_type string (e.g., "Batch - P 100.00")
        match = re.search(r'\d+', t.ticket_type)
        if match:
            price = int(match.group())
            # If a vendor sold it, they owe you the cash. Otherwise, it's direct electronic revenue.
            if t.vendor_name:
                vendor_cash_owed += price
            else:
                electronic_revenue += price
                
    # 3. Build the Dashboard UI
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tickets Sold", len(sold_tickets))
    with col2:
        st.metric("Total Scanned (In Venue)", len(scanned_tickets))
    with col3:
        st.metric("Electronic Revenue", f"P {electronic_revenue}")
    with col4:
        st.metric("Vendor Cash Owed", f"P {vendor_cash_owed}")
        
    st.divider()
    st.success("✅ Database connected successfully! Your dashboard is now reading live data.")
    
except Exception as e:
    st.error("🚨 Error loading database statistics.")
    st.code(str(e))
finally:
    session.close()
