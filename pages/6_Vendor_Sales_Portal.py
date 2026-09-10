import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner
from models import SessionLocal, Ticket, Event, Vendor

st.set_page_config(page_title="Vendor Portal", page_icon="🛒")
st.title("🛒 Vendor Sales Portal")
st.caption("Process live ticket sales securely.")

session = SessionLocal()

vendors = session.query(Vendor).all()
vendor_names = [v.name for v in vendors]

if not vendor_names:
    st.warning("No vendors registered in the system.")
else:
    # --- STEP 1: IDENTIFY VENDOR ---
    st.markdown("### Step 1: Who is selling?")
    selected_vendor = st.selectbox("Select your Vendor Profile", vendor_names)
    
    vendor_tickets = session.query(Ticket).filter_by(
        vendor_name=selected_vendor, 
        status="With_Vendor"
    ).all()
    
    active_event_ids = list(set([t.event_id for t in vendor_tickets if t.event_id]))
    
    if not active_event_ids:
        st.info(f"🟢 {selected_vendor} currently has zero tickets assigned for any event.")
    else:
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
        
        event_specific_tickets = [t for t in vendor_tickets if t.event_id == selected_event_id]
        
        st.success(f"🎫 You have **{len(event_specific_tickets)}** unsold tickets available for **{selected_event_name}**.")
        
        st.divider()
        
        # --- STEP 3: EXECUTE SALE ---
        st.markdown("### Step 3: Process Sale")
        
        tab1, tab2 = st.tabs(["📷 Scan Paper Ticket", "🔢 Sell by Quantity (Digital)"])
        
        # --- TAB 1: THE PAPER SCANNER (LOCKED) ---
        with tab1:
            st.info("You must enter the buyer's phone number to unlock the scanner.")
            
            buyer_phone_paper = st.text_input("📱 Buyer Phone Number", placeholder="e.g. 71234567", key="paper_phone_input")
            
            # The Lock Logic
            if not buyer_phone_paper:
                st.warning("🔒 The scanner is locked. Enter a phone number above to activate it.")
            else:
                st.success("🔓 Scanner activated. Hold the printed QR code up to the camera.")
                
                qr_code = qrcode_scanner(key='vendor_qr_scanner')
                
                if qr_code:
                    if 'last_vendor_scan' not in st.session_state or st.session_state['last_vendor_scan'] != qr_code:
                        st.session_state['last_vendor_scan'] = qr_code
                        clean_uuid = qr_code.strip()
                        
                        try:
                            ticket_to_sell = session.query(Ticket).filter_by(id=clean_uuid).first()
                            
                            if not ticket_to_sell:
                                st.error("❌ INVALID TICKET: This code is not in the database.")
                            elif ticket_to_sell.event_id != selected_event_id:
                                st.error("🚨 WRONG EVENT: This ticket is for a different event!")
                            elif ticket_to_sell.vendor_name != selected_vendor:
                                st.error(f"🛑 UNAUTHORIZED: This ticket was allocated to {ticket_to_sell.vendor_name}.")
                            elif ticket_to_sell.status == "Sold":
                                st.warning("⚠️ ALREADY SOLD: This ticket was already processed!")
                            else:
                                ticket_to_sell.status = "Sold"
                                ticket_to_sell.sold_by = selected_vendor
                                ticket_to_sell.buyer_phone = buyer_phone_paper # Records the number
                                session.commit()
                                
                                st.success(f"✅ PAPER TICKET SOLD! Value: P {ticket_to_sell.price} | Assigned to: {buyer_phone_paper}")
                                st.balloons()
                                
                        except Exception as e:
                            session.rollback()
                            st.error(f"Scan error: {e}")
                            
                    if st.button("🔄 Scan Next Paper Ticket", type="primary", use_container_width=True):
                        st.session_state['last_vendor_scan'] = None
                        st.rerun()

        # --- TAB 2: ORIGINAL BULK DIGITAL SALE ---
        with tab2:
            st.info("Use this if you are selling digital tickets via WhatsApp or SMS.")
            with st.form("sale_form"):
                buyer_phone = st.text_input("Buyer Phone Number", placeholder="e.g. 71234567")
                
                max_tickets = len(event_specific_tickets) if len(event_specific_tickets) > 0 else 1
                quantity = st.number_input("Number of Tickets to Sell", min_value=1, max_value=max_tickets, value=1)
                
                submit_sale = st.form_submit_button("💳 Confirm Digital Sale", type="primary", use_container_width=True)
                
                if submit_sale:
                    if not buyer_phone:
                        st.error("Buyer Phone Number is required for digital sales.")
                    elif len(event_specific_tickets) < quantity:
                        st.error("You do not have enough tickets assigned to complete this sale.")
                    else:
                        try:
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
                            st.success(f"✅ Successfully sold {quantity} digital ticket(s) to {buyer_phone}!")
                            st.balloons()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Sale failed: {e}")

session.close()
