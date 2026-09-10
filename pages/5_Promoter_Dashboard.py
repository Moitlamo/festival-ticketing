import streamlit as st
import pandas as pd
from models import SessionLocal, Client, Event, Ticket

st.set_page_config(page_title="Promoter Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS CARDS ---
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

clients = session.query(Client).all()
if not clients:
    st.warning("No promoters found. Please register a client in the Super Admin panel.")
else:
    client_dict = {c.name: c for c in clients}
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        selected_client_name = st.selectbox("1. Select Promoter Profile", list(client_dict.keys()))
        current_client = client_dict[selected_client_name]
    
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
        
        total_tickets = len(all_event_tickets)
        sold_tickets = sum(1 for t in all_event_tickets if t.status == "Sold")
        pending_tickets = total_tickets - sold_tickets
        live_gate_in = sum(1 for t in all_event_tickets if t.scanned_at_gate == True)
        
        # --- DISPLAY COLORED CARDS ---
        st.markdown(f"### Live Status: {selected_event_name}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(create_stat_card("Tickets Pending", pending_tickets, "#E53935", "⏳"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_stat_card("Tickets Sold", sold_tickets, "#1E88E5", "🎫"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_stat_card("Live Gate In", live_gate_in, "#4CAF50", "✅"), unsafe_allow_html=True)
            
        # --- FINANCIAL OVERVIEW ---
        st.markdown("### 💰 Financial Overview")
        realized_revenue = sum(t.price for t in all_event_tickets if t.status == "Sold" and t.price)
        potential_revenue = sum(t.price for t in all_event_tickets if t.price)
        
        fin_col1, fin_col2 = st.columns(2)
        with fin_col1:
            st.metric(label="Money Collected (Sold Tickets)", value=f"P {realized_revenue:,.2f}")
        with fin_col2:
            st.metric(label="Max Potential Revenue (If Sold Out)", value=f"P {potential_revenue:,.2f}")
        
        if total_tickets > 0:
            sales_percentage = (sold_tickets / total_tickets)
            st.caption(f"Overall Sales Completion: {sales_percentage * 100:.1f}% of {total_tickets} generated tickets.")
            st.progress(sales_percentage)
            
        st.divider()

        # --- NEW FEATURE: VENDOR PERFORMANCE TRACKER ---
        st.markdown("### 🏅 Vendor Performance breakdown")
        st.caption("Click on a vendor below to view their detailed sales statistics.")
        
        # Find all unique vendors who were assigned tickets for this specific event
        vendor_names = set(t.vendor_name for t in all_event_tickets if t.vendor_name)
        
        if not vendor_names:
            st.info("No vendors have been issued tickets for this event yet.")
        else:
            for v_name in sorted(vendor_names):
                # Filter tickets for this specific vendor
                v_tickets = [t for t in all_event_tickets if t.vendor_name == v_name]
                v_total = len(v_tickets)
                v_sold = sum(1 for t in v_tickets if t.status == "Sold")
                v_pending = v_total - v_sold
                v_gate_in = sum(1 for t in v_tickets if t.scanned_at_gate == True)
                v_revenue = sum(t.price for t in v_tickets if t.status == "Sold" and t.price)
                
                # The clickable expander bar
                with st.expander(f"👤 {v_name} — Sold: {v_sold} / {v_total} tickets"):
                    
                    # Detailed Stats inside the drop-down
                    v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                    v_col1.metric("Allocated to Vendor", v_total)
                    v_col2.metric("Tickets Sold", v_sold)
                    v_col3.metric("Tickets Pending", v_pending)
                    v_col4.metric("Money Collected", f"P {v_revenue:,.2f}")
                    
                    # Mini progress bar just for this vendor
                    if v_total > 0:
                        v_progress = v_sold / v_total
                        st.caption(f"{v_name}'s Sales Progress: {v_progress * 100:.1f}%")
                        st.progress(v_progress)
                        
                    st.info(f"**Gate Activity:** {v_gate_in} people who bought tickets from {v_name} have entered the event.")

        st.divider()
        
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
                        "Sold By": t.vendor_name,
                        "Scanned?": "Yes" if t.scanned_at_gate else "No"
                    })
                st.dataframe(pd.DataFrame(sales_data), use_container_width=True)

session.close()
