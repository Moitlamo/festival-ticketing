import streamlit as st
from models import SessionLocal, Ticket

# Configure the page settings
st.set_page_config(page_title="Festival Ticketing Command Center", layout="wide")

# Apply the custom Dark Blue and Deep Red UI
st.markdown("""
    <style>
    .stApp {
        background-color: #0b1120; 
        color: #e2e8f0;
    }
    div[data-testid="metric-container"] {
        background-color: #7f1d1d;
        border-radius: 8px;
        padding: 15px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎟️ Festival Command Center")

# Open a connection to the database
db = SessionLocal()

# Calculate live metrics
total_sold = db.query(Ticket).filter(Ticket.status.in_(['Sold', 'Scanned'])).count()
total_scanned = db.query(Ticket).filter(Ticket.status == 'Scanned').count()

# Assuming an electronic ticket costs P150 for this prototype
electronic_sold = db.query(Ticket).filter(Ticket.ticket_type == 'Electronic', Ticket.status.in_(['Sold', 'Scanned'])).count()
electronic_revenue = electronic_sold * 150

db.close()

# Display live metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Tickets Sold", value=f"{total_sold}")
with col2:
    st.metric(label="Total Scanned (In Venue)", value=f"{total_scanned}")
with col3:
    st.metric(label="Electronic Revenue", value=f"P {electronic_revenue:,}")
with col4:
    st.metric(label="Vendor Cash Owed", value="P 0")

st.divider()
st.success("✅ Database connected successfully! Your dashboard is now reading live data.")
