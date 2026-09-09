import streamlit as st
import pandas as pd
from models import SessionLocal, Client, Event, Ticket

st.set_page_config(page_title="Promoter Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS CARDS ---
# This function generates the brightly colored metric blocks
def create_stat_card(title, value, color_hex, icon):
    html = f"""
    <div style="
        background-color: {color_hex}; 
        padding: 20px; 
        border-radius: 10px; 
        color: white; 
        text-align: center; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;">
        <h3 style="margin: 0; font-size: 1.2rem; color: rgba(255,255,255,0.9); font-weight: normal;">{icon} {title}</h3>
        <h1 style="margin: 10px 0 0 0; font-size: 3rem; color: white;">{value}</h1>
    </div>
    """
    return html

st.title("📈 Promoter Command Center")
st.caption("Live, real-time analytics and gate tracking for your events.")

session = SessionLocal()

# 1. Select the Promoter (Client)
clients = session.query(Client).all()
if not clients:
    st.warning("No promoters found. Please register a client in the Super Admin panel.")
else:
    client_dict = {c.name: c for c in clients}
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        selected_client_name = st.selectbox("1. Select Promoter Profile", list(client_dict.keys()))
        current_client = client_dict[selected_client_name]
    
    # 2. Select the Event belonging to that Promoter
    client_events = session.query(Event).filter_by(client_id=current_client.id).all()
    
    if not client_events:
        st.info(f"⚪ {selected_client_name} does not have any active events.")
    else:
        event_dict = {e.name: e for e in client_events}
        with col_b:
            selected_event_name = st.selectbox("2. Select Event Dashboard", list(event_dict.keys()))
            current_event = event_dict[selected_event_name]
        
        st.divider()
        
        # --- FETCH LIVE DATA ---
        all_event_tickets = session.query(Ticket).filter_by(event_id=current_event.id).all()
        
        # Calculate Metrics
        total_tickets = len(all_event_tickets)
        sold_tickets = sum(1 for t in all_event_tickets if t.status == "Sold")
        pending_tickets = total_tickets - sold_tickets # Anything not sold is pending
        live_gate_in = sum(1 for t in all_event_tickets if t.scanned_at_gate == True)
        expected_revenue = sum(t.price for t in all_event_tickets if t.status == "Sold" and t.price)
        
        # --- DISPLAY COLORED CARDS ---
        st.markdown(f"### Live Status: {selected_event_name}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # RED CARD: Pending / Unsold
            st.markdown(create_stat_card("Tickets Pending", pending_tickets, "#E53935", "⏳"), unsafe_allow_html=True)
            
        with col2:
            # BLUE CARD: Sold Tickets
            st.markdown(create_stat_card("Tickets Sold", sold_tickets, "#1E88E5", "🎫"), unsafe_allow_html=True)
            
        with col3:
            # GREEN CARD: Live Gate In
            st.markdown(create_stat_card("Live Gate In", live_gate_in, "#4CAF50", "✅"), unsafe_allow_html=True)
            
        # --- EXTRA DETAILS (Financials & Progress) ---
        st.markdown("### 💰 Financial Overview")
        st.metric("Total Expected Revenue", f"P {expected_revenue:,.2f}")
        
        # Progress Bar for Sales
        if total_tickets > 0:
            sales_percentage = (sold_tickets / total_tickets)
            st.caption(f"Sales Completion: {sales_percentage * 100:.1f}% of {total_tickets} generated tickets.")
            st.progress(sales_percentage)
        
        # Recent Sales Table (Optional view to see what's happening right now)
        with st.expander("View Recent Ticket Sales"):
            sold_list = [t for t in all_event_tickets if t.status == "Sold"]
            if not sold_list:
                st.write("No sales processed yet.")
            else:
                sales_data = []
                for t in sold_list:
                    sales_data.append({
                        "Ticket Type": t.ticket_type,
                        "Price": f"P {t.price}",
                        "Sold By Vendor": t.vendor_name,
                        "Scanned at Gate?": "Yes" if t.scanned_at_gate else "No"
                    })
                st.dataframe(pd.DataFrame(sales_data), use_container_width=True)

session.close()
