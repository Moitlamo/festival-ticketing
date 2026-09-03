import streamlit as st

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
st.write("Welcome to the centralized ticketing system. The database is initializing...")

# Placeholder metrics for the dashboard
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Tickets Sold", value="0")
with col2:
    st.metric(label="Total Scanned", value="0")
with col3:
    st.metric(label="Electronic Revenue", value="P 0")
with col4:
    st.metric(label="Vendor Cash Owed", value="P 0")
