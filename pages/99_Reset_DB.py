import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("⚠️ Selective Database Wipe")
st.error("DANGER ZONE: This action is irreversible. All tickets, inventory, and event data for the targeted events will be permanently deleted from the database.")

def fetch_events():
    try:
        response = supabase.table('events').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Events fetch error: {e}")
        return []

events_data = fetch_events()
event_names = [e.get('name') or e.get('event_name') or e.get('title') for e in events_data if e]

if not events_data:
    st.info("No events found in the database.")
else:
    # 1. Select the Safe Zone
    st.markdown("### 1. Choose the Event to Protect")
    keep_event_name = st.selectbox("Select the event to KEEP (Everything else will be wiped):", options=event_names)

    # 2. Safety Lock
    st.markdown("### 2. Confirm Purge")
    confirm_text = st.text_input(f"Type WIPE to confirm deletion of all events EXCEPT '{keep_event_name}'")

    if st.button("Purge Database", type="primary"):
        if confirm_text != "WIPE":
            st.warning("⚠️ You must type exactly 'WIPE' in all caps to unlock the purge button.")
        else:
            with st.spinner("Initiating database purge..."):
                try:
                    keep_event_id = None
                    events_to_delete = []

                    # Sort out the safe event from the condemned events
                    for e in events_data:
                        name = e.get('name') or e.get('event_name') or e.get('title')
                        if name == keep_event_name:
                            keep_event_id = e.get('id')
                        else:
                            events_to_delete.append(e)

                    if not events_to_delete:
                        st.success("No other events to delete! The database is already clean.")
                    else:
                        for event in events_to_delete:
                            ev_id = event.get('id')
                            ev_name = event.get('name') or event.get('event_name') or event.get('title')

                            st.write(f"🗑️ Purging data for: **{ev_name}**...")

                            # Step A: Wipe Dashboard Inventory
                            supabase.table('inventory').delete().eq('event_name', ev_name).execute()

                            # Step B: Wipe all Physical Tickets (By event_id to bypass limits safely)
                            supabase.table('tickets').delete().eq('event_id', ev_id).execute()

                            # Step C: Destroy the Event Profile itself
                            supabase.table('events').delete().eq('id', ev_id).execute()
                            
                        # Step D: Sweeping orphan tickets (tags that might have a bad/null event ID)
                        if keep_event_id:
                            st.write("🧹 Sweeping orphaned and broken tags...")
                            supabase.table('tickets').delete().neq('event_id', keep_event_id).execute()

                        st.success(f"✅ Database successfully wiped! Only '{keep_event_name}' remains.")
                        st.balloons()
                
                except Exception as e:
                    st.error(f"❌ An error occurred during the wipe: {e}")
