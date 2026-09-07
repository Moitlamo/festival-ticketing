import streamlit as st
import re
from models import SessionLocal, Ticket, Vendor

st.set_page_config(page_title="Promoter Dashboard", page_icon="📊", layout="wide")
st.title("📊 Promoter Dashboard")

session = SessionLocal()
try:
    all_tickets = session.query(Ticket).all()
    
    # 1. Categorize Tickets by Status
    issued_tickets = [t for t in all_tickets if t.status == "With_Vendor"]
    sold_tickets = [t for t in all_tickets if t.status in ["Sold", "Used"]]
    used_tickets = [t for t in all_tickets if t.status == "Used"]
    
    # 2. Calculate Actual Revenue (Only from Sold/Used tickets)
    actual_revenue = 0
    for t in sold_tickets:
        # Extract the price number from strings like "Batch - P 100.00" or "Physical_P50"
        match = re.search(r'\d+', t.ticket_type)
        if match:
            actual_revenue += int(match.group())

    # 3. Calculate Potential Revenue (Inventory currently with vendors)
    potential_revenue = 0
    for t in issued_tickets:
        match = re.search(r'\d+', t.ticket_type)
        if match:
            potential_revenue += int(match.group())

    # --- Dashboard UI ---
    st.subheader("Financial Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Actual Gross Revenue", value=f"P {actual_revenue}.00", help="Revenue from finalized sales.")
    with col2:
        st.metric(label="Pending Vendor Inventory", value=f"P {potential_revenue}.00", help="Value of unsold tickets held by vendors.")
    with col3:
        total = actual_revenue + potential_revenue
        st.metric(label="Total System Value", value=f"P {total}.00")

    st.divider()
    
    st.subheader("Gate & Distribution Stats")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(label="Total Tickets Sold", value=len(sold_tickets))
    with col5:
        st.metric(label="Tickets Pending Sale", value=len(issued_tickets))
    with col6:
        check_in_rate = (len(used_tickets) / len(sold_tickets) * 100) if sold_tickets else 0
        st.metric(label="Live Gate Check-Ins", value=f"{len(used_tickets)} ({check_in_rate:.1f}%)")

except Exception as e:
    st.error("Error loading dashboard data.")
    st.code(str(e))
finally:
    session.close()
