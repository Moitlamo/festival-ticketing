import streamlit as st
import datetime
from models import SessionLocal, Client, Event

st.set_page_config(page_title="Super Admin Dashboard", page_icon="👑")
st.title("👑 M.Marumo Technologies Admin")
st.caption("Global master control for SmartTec Ticket clients and events.")

# Create tabs to organize the dashboard
tab1, tab2 = st.tabs(["🏢 Onboard New Client", "📅 Create Event"])

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
            event_name = st.text_input("Event Name", placeholder="e.g., December Total Football Mania")
            event_date = st.date_input("Event Date", min_value=datetime.date.today())
            
            submit_event = st.form_submit_button("Initialize Event", type="primary")
            
            if submit_event:
                if not event_name:
                    st.error("Event name is required.")
                else:
                    try:
                        new_event = Event(
                            name=event_name,
                            event_date=event_date,
                            client_id=client_options[selected_client]
                        )
                        session.add(new_event)
                        session.commit()
                        st.success(f"✅ Event '{event_name}' created under {selected_client}!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error creating event: {e}")
    session.close()
