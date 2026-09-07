import streamlit as st
from models import SessionLocal, Ticket, Vendor

st.set_page_config(page_title="Vendor Sales Portal", page_icon="💼")
st.title("💼 Vendor Sales Portal")
st.caption("Scan tickets to register buyers and track your live inventory.")

# 1. Fetch registered vendors from the database
session = SessionLocal()
try:
    vendors = session.query(Vendor).all()
    # Create a list with a default placeholder, followed by actual vendor names
    vendor_names = ["Select Your Profile"] + [v.name for v in vendors]
except Exception as e:
    st.error("Database connection error.")
    vendor_names = ["Select Your Profile"]
finally:
    session.close()

# 2. Vendor Login Selection
st.subheader("Vendor Login")
selected_vendor = st.selectbox("Select your authorized vendor profile", vendor_names, label_visibility="collapsed")

if selected_vendor == "Select Your Profile":
    st.info("Please select your vendor profile to access the POS and inventory.")
else:
    st.success(f"Logged in as: **{selected_vendor}**")
    st.divider()
    
    # 3. Load Vendor's Specific Inventory
    session = SessionLocal()
    try:
        # Find all tickets assigned to this vendor that are NOT yet sold
        available_tickets = session.query(Ticket).filter_by(vendor_name=selected_vendor, status="With_Vendor").all()
        
        st.subheader("Live Inventory")
        st.metric(label="Tickets Ready to Sell", value=len(available_tickets))
        
        if len(available_tickets) > 0:
            with st.form("sell_ticket_form"):
                st.write("### Register a Sale")
                st.caption("Enter the customer's phone number to finalize the sale and issue the digital ticket.")
                
                buyer_phone = st.text_input("Buyer Phone Number", placeholder="e.g., 71234567")
                
                submitted = st.form_submit_button("Complete Sale & Issue Ticket", type="primary")
                
                if submitted:
                    if not buyer_phone.strip():
                        st.warning("Please enter the buyer's phone number to trace the ticket.")
                    else:
                        # Grab the first available ticket in their batch
                        ticket_to_sell = available_tickets[0]
                        
                        # Update the ticket status to Sold and assign the phone number
                        ticket_to_sell.status = "Sold"
                        ticket_to_sell.buyer_phone = buyer_phone.strip()
                        
                        session.commit()
                        st.success(f"✅ Sale confirmed! Ticket ID ending in {ticket_to_sell.id[-6:]} assigned to {buyer_phone}.")
                        st.balloons()
                        # Rerun the app to update the inventory counter instantly
                        st.rerun()
        else:
            st.warning("You have sold out of your current allocation. Please contact the promoter for a new batch.")
            
    except Exception as e:
        session.rollback()
        st.error("Error loading inventory.")
        st.code(str(e))
    finally:
        session.close()
