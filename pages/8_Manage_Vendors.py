import streamlit as st
import pandas as pd
from models import SessionLocal, Vendor, Ticket

st.set_page_config(page_title="Manage Vendors", page_icon="🧑‍💼")
st.title("🧑‍💼 Manage Vendors")
st.caption("Register authorized sellers and track their contact details and ticket inventory.")

# Form to add a new vendor with expanded details
with st.form("add_vendor_form", clear_on_submit=True):
    new_vendor_name = st.text_input("Vendor Name & Code (e.g., Presto Restaurant [VEND-001])")
    contact_details = st.text_input("Contact Details (Phone Number / Email)")
    address = st.text_input("Physical Address (e.g., Plot 1234, Xhosa Ward)")
    location = st.text_input("City/Village (e.g., Mahalapye)")
    
    submitted = st.form_submit_button("Register Vendor", type="primary")

if submitted:
    if not new_vendor_name.strip():
        st.warning("Please enter a vendor name.")
    else:
        session = SessionLocal()
        try:
            new_vendor = Vendor(
                name=new_vendor_name.strip(),
                contact_details=contact_details.strip() if contact_details else None,
                address=address.strip() if address else None,
                location=location.strip() if location else None
            )
            session.add(new_vendor)
            session.commit()
            st.success(f"✅ Vendor '{new_vendor_name}' successfully registered!")
            st.balloons()
        except Exception:
            session.rollback()
            st.error("🚨 This vendor name already exists in the system.")
        finally:
            session.close()

# Display the current list of authorized vendors
st.divider()
st.subheader("Currently Registered Vendors")

session = SessionLocal()
existing_vendors = session.query(Vendor).all()

if existing_vendors:
    for v in existing_vendors:
        # Use an expander to keep the list clean while showing full details
        with st.expander(f"🏷️ **{v.name}**"):
            st.write(f"**Contact:** {v.contact_details or 'Not provided'}")
            st.write(f"**Address:** {v.address or 'Not provided'}")
            st.write(f"**Location:** {v.location or 'Not provided'}")
            
            st.divider()
            st.write("### 🎟️ Assigned Ticket Inventory")
            
            # Fetch all tickets assigned to this specific vendor
            vendor_tickets = session.query(Ticket).filter_by(vendor_name=v.name).all()
            
            if vendor_tickets:
                # Prepare data for a clean table view
                ticket_data = []
                for t in vendor_tickets:
                    ticket_data.append({
                        "Identifier (Serial/ID)": t.printed_serial if t.printed_serial else f"Digital: {t.id[-6:]}",
                        "Type": t.ticket_type,
                        "Status": t.status,
                        "Buyer Phone": t.buyer_phone if t.buyer_phone else "---"
                    })
                
                # Display the inventory as a scrollable DataFrame
                df = pd.DataFrame(ticket_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Add a quick math summary at the bottom
                sold_count = len([t for t in vendor_tickets if t.status in ["Sold", "Used"]])
                st.caption(f"**Total Assigned:** {len(vendor_tickets)} | **Sold/Used:** {sold_count} | **Remaining Inventory:** {len(vendor_tickets) - sold_count}")
            else:
                st.info("No tickets currently assigned to this vendor.")
else:
    st.info("No vendors registered yet.")
    
session.close()
