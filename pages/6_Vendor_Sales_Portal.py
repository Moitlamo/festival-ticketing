import streamlit as st
from models import SessionLocal, Ticket, Vendor
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="Vendor Sales Portal", page_icon="💼")
st.title("💼 Vendor Sales Portal")
st.caption("Register sales and assign tickets to buyers.")

# 1. Fetch registered vendors
session = SessionLocal()
try:
    vendors = session.query(Vendor).all()
    vendor_names = ["Select Your Profile"] + [v.name for v in vendors]
except Exception:
    st.error("Database connection error.")
    vendor_names = ["Select Your Profile"]
finally:
    session.close()

# 2. Vendor Login
st.subheader("Vendor Login")
selected_vendor = st.selectbox("Select your authorized vendor profile", vendor_names, label_visibility="collapsed")

if selected_vendor == "Select Your Profile":
    st.info("Please select your vendor profile to access the POS and inventory.")
else:
    st.success(f"Logged in as: **{selected_vendor}**")
    st.divider()
    
    session = SessionLocal()
    try:
        # Load Available Inventory
        available_tickets = session.query(Ticket).filter_by(vendor_name=selected_vendor, status="With_Vendor").all()
        
        st.subheader("Live Inventory")
        st.metric(label="Tickets Ready to Sell", value=len(available_tickets))
        
        if len(available_tickets) > 0:
            st.write("### Register a Sale")
            
            # Create Tabs for the different sales methods
            tab1, tab2, tab3 = st.tabs(["⌨️ Enter Number", "📷 Scan QR", "🎟️ Auto-Assign (Digital)"])
            
            # --- TAB 1: SERIAL NUMBER ENTRY ---
            with tab1:
                st.caption("Sell a physical ticket by typing its 3-digit printed serial number.")
                with st.form("serial_sale_form", clear_on_submit=True):
                    serial_input = st.text_input("Ticket Serial Number", max_chars=3, placeholder="e.g., 025")
                    buyer_phone_1 = st.text_input("Buyer Phone Number", placeholder="e.g., 71234567", key="phone_1")
                    submit_serial = st.form_submit_button("Complete Sale", type="primary")
                    
                    if submit_serial:
                        if not serial_input.strip() or not buyer_phone_1.strip():
                            st.warning("Please enter both the serial number and the buyer's phone number.")
                        else:
                            formatted_serial = serial_input.strip().zfill(3)
                            ticket = session.query(Ticket).filter_by(printed_serial=formatted_serial, vendor_name=selected_vendor).first()
                            
                            if not ticket:
                                st.error(f"❌ Ticket #{formatted_serial} is not in your inventory.")
                            elif ticket.status != "With_Vendor":
                                st.error(f"⚠️ Ticket #{formatted_serial} has already been sold or used.")
                            else:
                                ticket.status = "Sold"
                                ticket.buyer_phone = buyer_phone_1.strip()
                                session.commit()
                                st.success(f"✅ Sale confirmed! Ticket #{formatted_serial} assigned to {buyer_phone_1}.")
                                st.balloons()
            
            # --- TAB 2: QR SCANNER ---
            with tab2:
                st.caption("Sell a physical ticket by scanning its printed QR code.")
                qr_code = qrcode_scanner(key='vendor_sales_scanner')
                
                if qr_code:
                    ticket = session.query(Ticket).filter_by(id=qr_code).first()
                    
                    if not ticket:
                        st.error("❌ Invalid ticket QR code.")
                    elif ticket.vendor_name != selected_vendor:
                        st.error("⚠️ This ticket belongs to a different vendor's inventory.")
                    elif ticket.status != "With_Vendor":
                        st.error("⚠️ This ticket has already been sold or used.")
                    else:
                        st.success("✅ Ticket verified in your inventory!")
                        with st.form("qr_sale_form", clear_on_submit=True):
                            buyer_phone_2 = st.text_input("Buyer Phone Number", placeholder="e.g., 71234567", key="phone_2")
                            submit_qr = st.form_submit_button("Confirm & Assign to Buyer", type="primary")
                            
                            if submit_qr:
                                if not buyer_phone_2.strip():
                                    st.warning("Please enter the buyer's phone number.")
                                else:
                                    ticket.status = "Sold"
                                    ticket.buyer_phone = buyer_phone_2.strip()
                                    session.commit()
                                    st.success(f"✅ Sale confirmed! Ticket assigned to {buyer_phone_2}.")
                                    st.balloons()

            # --- TAB 3: AUTO-ASSIGN DIGITAL TICKET ---
            with tab3:
                st.caption("Automatically grab the next available digital ticket in your inventory.")
                with st.form("digital_sale_form", clear_on_submit=True):
                    buyer_phone_3 = st.text_input("Buyer Phone Number", placeholder="e.g., 71234567", key="phone_3")
                    submit_digital = st.form_submit_button("Complete Digital Sale", type="primary")
                    
                    if submit_digital:
                        if not buyer_phone_3.strip():
                            st.warning("Please enter the buyer's phone number.")
                        else:
                            # Grab the first ticket that doesn't have a printed serial number (digital ticket)
                            digital_tickets = [t for t in available_tickets if t.printed_serial is None]
                            
                            if not digital_tickets:
                                st.error("❌ You have no digital tickets left in your inventory.")
                            else:
                                ticket_to_sell = digital_tickets[0]
                                ticket_to_sell.status = "Sold"
                                ticket_to_sell.buyer_phone = buyer_phone_3.strip()
                                session.commit()
                                st.success(f"✅ Sale confirmed! Digital ticket assigned to {buyer_phone_3}.")
                                st.balloons()
        else:
            st.warning("You have sold out of your current allocation. Please contact the promoter for a new batch.")
            
    except Exception as e:
        session.rollback()
        st.error("Error loading inventory.")
    finally:
        session.close()
