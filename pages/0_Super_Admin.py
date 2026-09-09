import streamlit as st
import datetime
import pandas as pd
from models import SessionLocal, Client, Event, Vendor, Ticket

st.set_page_config(page_title="Super Admin Dashboard", page_icon="👑", layout="wide")
st.title("👑 M.Marumo Technologies Admin")
st.caption("Global master control and stakeholder overview for SmartTec Ticket.")

tab1, tab2, tab3 = st.tabs(["🏢 Onboard Client", "📅 Create Event", "📊 System Overview"])

# --- TAB 1: CREATE CLIENT ---
with tab1:
    st.subheader("Register Client Organization")
    with st.form("client_form"):
        client_name = st.text_input("Client / Promoter Name", placeholder="e.g., Kudu Entertainment")
        client_phone = st.text_input("Contact Phone", placeholder="e.g., +267 71 234 567")
        submit_client = st.form_submit_button("Register Client", type="primary")
        
        if submit_client:
            if not client_name:
                st.error("Client name is required.")
            else:
                session = SessionLocal()
                try:
                    new_client = Client(name=client_name, contact_phone=client_phone)
                    session.add(new_client)
                    session.commit()
                    st.success(f"✅ Client '{client_name}' successfully registered!")
                except Exception as e:
                    session.rollback()
                    st.error("Error creating client. The name might already exist.")
                finally:
                    session.close()

# --- TAB 2: CREATE EVENT ---
with tab2:
    st.subheader("Initialize New Event")
    session = SessionLocal()
    clients = session.query(Client).all()
    client_options = {c.name: c.id for c in clients}
    
    if not clients:
        st.warning("⚠️ You must register a Client first before creating an Event.")
    else:
        with st.form("event_form"):
            selected_client = st.selectbox("Assign to Client", list(client_options.keys()))
            event_name = st.text_input("Event Name", placeholder="e.g., Total Football Mania Soccer Tournament")
            event_date = st.date_input("Event Date", min_value=datetime.date.today())
            
            # --- NEW FIELD: CUSTOM GATE PIN ---
            st.markdown("#### Security Settings")
            gate_pin_input = st.text_input("Set Gate Access PIN (Bouncers will use this to login)", value="1234", type="password")
            
            submit_event = st.form_submit_button("Initialize Event", type="primary")
            
            if submit_event:
                if not event_name:
                    st.error("Event name is required.")
                elif not gate_pin_input:
                    st.error("Gate Access PIN is required.")
                else:
                    try:
                        new_event = Event(
                            name=event_name,
                            event_date=event_date,
                            gate_pin=gate_pin_input, # Saves the custom PIN to the database
                            client_id=client_options[selected_client]
                        )
                        session.add(new_event)
                        session.commit()
                        st.success(f"✅ Event '{event_name}' created under {selected_client} with PIN protection!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error creating event: {e}")
    session.close()

# --- TAB 3: SYSTEM OVERVIEW ---
with tab3:
    st.subheader("Global Stakeholders & Financial Status")
    session = SessionLocal()
    
    st.markdown("### 🏢 Promoters & Events")
    all_clients = session.query(Client).all()
    
    if not all_clients:
        st.info("No promoters registered in the system yet.")
    else:
        today = datetime.date.today()
        for client in all_clients:
            client_events = session.query(Event).filter_by(client_id=client.id).all()
            with st.expander(f"Promoter: {client.name} | 📞 {client.contact_phone or 'N/A'}"):
                if not client_events:
                    st.warning("Status: ⚪ Inactive (No events registered)")
                else:
                    st.success(f"Status: 🟢 Active ({len(client_events)} Event(s))")
                    event_data = []
                    for ev in client_events:
                        ev_date = ev.event_date.date() if isinstance(ev.event_date, datetime.datetime) else ev.event_date
                        if ev_date:
                            status = "🟢 Upcoming / Today" if ev_date >= today else "🔴 Completed"
                            date_str = ev_date.strftime("%Y-%m-%d")
                        else:
                            status = "⚪ Unknown"
                            date_str = "Not Set"
                            
                        ticket_count = session.query(Ticket).filter_by(event_id=ev.id).count()
                        event_data.append({
                            "Event Name": ev.name,
                            "Date": date_str,
                            "Status": status,
                            "Gate PIN": ev.gate_pin, # Allows Super Admin to view the PIN
                            "Total Tickets": ticket_count
                        })
                    st.table(pd.DataFrame(event_data))
    
    st.divider()

    st.markdown("### 👥 Global Authorized Vendors & Financials")
    all_vendors = session.query(Vendor).all()
    
    if not all_vendors:
        st.info("No vendors registered in the system yet.")
    else:
        vendor_data = []
        for v in all_vendors:
            vendor_data.append({
                "Vendor Name": v.name,
                "Phone": v.phone or "N/A",
                "Status": v.status,
                "Allocated Tickets": v.allocated_count,
                "Sold": v.sold_count,
                "Expected Revenue": f"P {v.expected_revenue:.2f}",
                "Remitted": f"P {v.remitted_funds:.2f}"
            })
        st.dataframe(pd.DataFrame(vendor_data), use_container_width=True)

    session.close()
