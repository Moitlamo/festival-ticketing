import streamlit as st
import pandas as pd
from models import SessionLocal, Ticket

# Configure the page
st.set_page_config(page_title="Vendor Allocations", layout="wide")

# Apply the custom dark red and deep blue UI to reduce visual fatigue
st.markdown("""
    <style>
    .stApp {
        background-color: #0b1120; 
        color: #e2e8f0;
    }
    .stButton>button {
        background-color: #7f1d1d;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #991b1b;
        color: white;
    }
    div[data-testid="stForm"] {
        background-color: #1e293b;
        border: 1px solid #7f1d1d;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Vendor Ticket Allocation")
st.write("Assign batches of pre-printed paper tickets to street promoters and track cash owed.")

# Open database connection
db = SessionLocal()

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("Assign New Batch")
    with st.form("allocation_form"):
        vendor_name = st.text_input("Promoter / Vendor Name")
        prefix = st.text_input("Serial Prefix (e.g., FEST-)", value="FEST-")
        
        c1, c2 = st.columns(2)
        with c1:
            start_num = st.number_input("Starting Number", min_value=1, step=1)
        with c2:
            end_num = st.number_input("Ending Number", min_value=1, step=1)
            
        submit = st.form_submit_button("Allocate Tickets to Vendor")
        
        if submit and vendor_name:
            if start_num <= end_num:
                new_tickets = []
                # Loop through the range and generate the serial numbers
                for i in range(int(start_num), int(end_num) + 1):
                    # Format as FEST-001, FEST-002, etc.
                    serial = f"{prefix}{i:03d}"
                    
                    # Check if ticket already exists to prevent duplicates
                    existing = db.query(Ticket).filter(Ticket.serial_number == serial).first()
                    if not existing:
                        ticket = Ticket(
                            ticket_type="Manual",
                            serial_number=serial,
                            status="Available",
                            vendor_name=vendor_name
                        )
                        new_tickets.append(ticket)
                
                if new_tickets:
                    db.add_all(new_tickets)
                    db.commit()
                    st.success(f"✅ Successfully allocated {len(new_tickets)} tickets to {vendor_name}.")
                else:
                    st.warning("All tickets in this range are already allocated in the database.")
            else:
                st.error("Ending number must be greater than or equal to starting number.")

with col2:
    st.subheader("Current Vendor Tracking")
    # Query database to group tickets by vendor and calculate statuses
    vendors = db.query(Ticket.vendor_name).filter(Ticket.ticket_type == 'Manual').distinct().all()
    
    if vendors and vendors[0][0] is not None:
        tracking_data = []
        for v in vendors:
            v_name = v[0]
            if not v_name: continue
            
            total = db.query(Ticket).filter(Ticket.vendor_name == v_name).count()
            sold = db.query(Ticket).filter(Ticket.vendor_name == v_name, Ticket.status.in_(['Sold', 'Scanned'])).count()
            available = total - sold
            
            # Assuming a manual ticket costs P100 for this prototype
            cash_owed = sold * 100 
            
            tracking_data.append({
                "Vendor": v_name,
                "Allocated": total,
                "Unsold (Available)": available,
                "Sold/Scanned": sold,
                "Cash Owed": f"P {cash_owed:,}"
            })
            
        df = pd.DataFrame(tracking_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No manual tickets have been allocated to vendors yet.")

db.close()
