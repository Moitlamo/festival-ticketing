import streamlit as st
from models import SessionLocal, Ticket, Event, Vendor

st.set_page_config(page_title="Vendor Portal", page_icon="🛒")
st.title("🛒 Vendor Sales Portal")
st.caption("Process live ticket sales securely.")

session = SessionLocal()

# 1. Get all registered vendors
vendors = session.query(Vendor).all()
vendor_names = [v.name for v in vendors]

if not vendor_names:
    st.warning("No vendors registered in the system.")
else:
    # --- STEP 1: IDENTIFY VENDOR ---
    st.markdown("### Step 1: Who is selling?")
    selected_vendor = st.selectbox("Select your Vendor Profile", vendor_names)
    
    # Find all events this specific vendor holds tickets for
    vendor_tickets = session.query(Ticket).filter_by(
        vendor_name=selected_vendor, 
        status="With_Vendor"
    ).all()
    
    # Extract unique event IDs from those tickets
    active_event_ids = list(set([t.event_id for t in vendor_tickets if t.event_id]))
    
    if not active_event_ids:
        st.info(f"🟢 {selected_vendor} currently has zero tickets assigned for any event.")
    else:
        # Fetch the actual Event names from the database
        active_events = session.query(Event).filter(Event.id.in_(active_event_ids)).all()
        event_dict = {e.name: e.id for e in active_events}
        
        st.divider()
        
        # --- STEP 2: THE GUARDRAIL (Select Event) ---
        st.markdown("### Step 2: Which event are you selling for right now?")
        selected_event_name = st.radio(
            "⚠️ You must select the correct event before selling:", 
            list(event_dict.keys())
        )
        selected_event_id = event_dict[selected_event_name]
        
        # Count tickets for the SELECTED event only
        event_specific_tickets = [t for t in vendor_tickets if t.event_id == selected_event_id]
        
        st.success(f"🎫 You have **{len(event_specific_tickets)}** tickets available for **{selected_event_name}**.")
        
        st.divider()
        
        # --- STEP 3: EXECUTE SALE ---
        st.markdown("### Step 3: Process Sale")
        with st.form("sale_form"):
            buyer_phone = st.text_input("Buyer Phone Number (Optional)", placeholder="e.g. 71234567")
            quantity = st.number_input("Number of Tickets to Sell", min_value=1, max_value=len(event_specific_tickets), value=1)
            
            submit_sale = st.form_submit_button("💳 Confirm Sale", type="primary", use_container_width=True)
            
            if submit_sale:
                try:
                    # Grab the exact number of tickets requested for THIS specific event
                    tickets_to_sell = session.query(Ticket).filter_by(
                        vendor_name=selected_vendor,
                        event_id=selected_event_id,
                        status="With_Vendor"
                    ).limit(quantity).all()
                    
                    for ticket in tickets_to_sell:
                        ticket.status = "Sold"
                        ticket.buyer_phone = buyer_phone
                        ticket.sold_by = selected_vendor
                    
                    session.commit()
                    st.success(f"✅ Successfully sold {quantity} ticket(s) for {selected_event_name}!")
                    st.balloons()
                except Exception as e:
                    session.rollback()
                    st.error(f"Sale failed: {e}")

session.close()
