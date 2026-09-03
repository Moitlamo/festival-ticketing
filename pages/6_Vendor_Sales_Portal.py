import streamlit as st
import pandas as pd
import json
import os
from models import SessionLocal, Ticket
try:
    from streamlit_qrcode_scanner import qrcode_scanner
except ImportError:
    st.error("⚠️ Library missing. Please run: pip install streamlit-qrcode-scanner")
    st.stop()

st.set_page_config(page_title="Vendor Sales Portal", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stTextInput>div>div>input, .stSelectbox>div>div>select { background-color: #1e293b; color: white; }
    .stButton>button { background-color: #7f1d1d; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #991b1b; color: white; }
    .metric-box { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; text-align: center; margin-bottom: 15px;}
    .metric-value { font-size: 28px; font-weight: bold; color: white; }
    .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
    .status-badge { background-color: #065f46; padding: 15px; border-radius: 8px; text-align: center; border: 2px solid #34d399; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- LOAD VENDOR REGISTRY ---
VENDOR_FILE = "vendors.json"
def load_vendors():
    if os.path.exists(VENDOR_FILE):
        with open(VENDOR_FILE, "r") as f:
            return json.load(f)
    return {}

vendors_db = load_vendors()

st.title("💼 Vendor Sales Portal")
st.write("Scan tickets to register buyers and track your live inventory.")

# --- VENDOR AUTHENTICATION ---
vendor_options = ["Select Your Profile"] + [f"{v['name']} (ID: {k})" for k, v in vendors_db.items()]
selected_vendor = st.selectbox("Vendor Login", vendor_options)

if selected_vendor == "Select Your Profile":
    st.info("Please select your vendor profile to access the POS and inventory.")
    st.stop()

vendor_name = selected_vendor.split(" (ID:")[0]
st.success(f"✅ Logged in as: **{vendor_name}**")

# --- INITIALIZE POS STATE ---
if "pos_scanned_id" not in st.session_state:
    st.session_state.pos_scanned_id = None

tab1, tab2 = st.tabs(["📸 Point of Sale (Scan & Sell)", "📊 My Inventory"])

# ==========================================
# TAB 1: POINT OF SALE SCANNER
# ==========================================
with tab1:
    if not st.session_state.pos_scanned_id:
        st.write("### Sell a Ticket")
        camera_scan = qrcode_scanner(key='vendor_pos_scanner')
        
        with st.form("manual_pos_form"):
            manual_id = st.text_input("Or enter Ticket ID manually")
            submit_manual = st.form_submit_button("Find Ticket")
            
        if camera_scan:
            st.session_state.pos_scanned_id = camera_scan
            st.rerun()
        elif submit_manual and manual_id.strip():
            st.session_state.pos_scanned_id = manual_id.strip()
            st.rerun()
            
    else:
        # Ticket Registration Screen
        clean_id = st.session_state.pos_scanned_id
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.ticket_id == clean_id).first()
            
            if not ticket:
                st.error("❌ FAKE OR INVALID TICKET. Not recognized in the system.")
                if st.button("Scan Another Ticket"):
                    st.session_state.pos_scanned_id = None
                    st.rerun()
                    
            elif vendor_name not in str(ticket.buyer_phone):
                st.error("⚠️ This ticket belongs to a different vendor's batch.")
                if st.button("Scan Another Ticket"):
                    st.session_state.pos_scanned_id = None
                    st.rerun()
                    
            elif ticket.status in ["Sold", "Used"]:
                st.warning("⚠️ This ticket has ALREADY been sold and registered.")
                st.write(f"**Current Details:** {ticket.buyer_phone}")
                if st.button("Scan Another Ticket"):
                    st.session_state.pos_scanned_id = None
                    st.rerun()
                    
            elif ticket.status == "With_Vendor":
                st.markdown("""
                <div class="status-badge">
                    <h3 style='margin:0; color:white;'>Ticket Ready for Sale</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Extract event and value for display
                details = ticket.buyer_phone.split(" | ")
                event_name = [d for d in details if "Event:" in d][0] if len(details) > 1 else "Unknown Event"
                ticket_value = [d for d in details if "Value:" in d][0] if len(details) > 2 else "Unknown Value"
                
                st.write(f"**{event_name}** | **{ticket_value}**")
                
                with st.form("register_sale_form"):
                    buyer_cell = st.text_input("Enter Customer Cell Number (+267...)")
                    confirm_sale = st.form_submit_button("Confirm Sale & Register Ticket", use_container_width=True)
                    
                    if confirm_sale:
                        if not buyer_cell.strip():
                            st.error("Please enter the customer's phone number.")
                        else:
                            # Update status and append buyer number to preserve tracking data
                            ticket.status = "Sold"
                            ticket.buyer_phone = f"{ticket.buyer_phone} | Buyer: {buyer_cell.strip()}"
                            db.commit()
                            
                            st.success(f"✅ Sale Confirmed! Ticket registered to {buyer_cell.strip()}.")
                            st.session_state.pos_scanned_id = None
                            st.rerun()
                            
                if st.button("Cancel & Scan Different Ticket"):
                    st.session_state.pos_scanned_id = None
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Database Error: {e}")
        finally:
            db.close()

# ==========================================
# TAB 2: VENDOR INVENTORY DASHBOARD
# ==========================================
with tab2:
    db = SessionLocal()
    try:
        # Fetch all tickets belonging to this vendor
        vendor_tickets = db.query(Ticket).filter(Ticket.buyer_phone.like(f"%Vendor: {vendor_name}%")).all()
        
        if not vendor_tickets:
            st.info("No tickets have been assigned to your profile yet.")
        else:
            total_assigned = len(vendor_tickets)
            unsold_count = sum(1 for t in vendor_tickets if t.status == "With_Vendor")
            sold_count = sum(1 for t in vendor_tickets if t.status == "Sold")
            used_count = sum(1 for t in vendor_tickets if t.status == "Used")
            total_sales = sold_count + used_count
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{total_assigned}</div><div class="metric-label">Total Assigned</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{unsold_count}</div><div class="metric-label">Tickets on Hand</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#34d399;">{total_sales}</div><div class="metric-label">Total Sold</div></div>', unsafe_allow_html=True)

            st.write("---")
            st.write("### Recent Sales Log")
            
            # Extract just the sold/used tickets to show a ledger
            sales_data = []
            for t in vendor_tickets:
                if t.status in ["Sold", "Used"]:
                    # Extract the buyer number and value safely
                    parts = str(t.buyer_phone).split(" | ")
                    buyer = [p.replace("Buyer: ", "") for p in parts if "Buyer:" in p]
                    val = [p.replace("Value: ", "") for p in parts if "Value:" in p]
                    
                    sales_data.append({
                        "Ticket ID": t.ticket_id[:8],
                        "Customer Number": buyer[0] if buyer else "Not Registered",
                        "Value": val[0] if val else "Unknown",
                        "Gate Status": "Checked In" if t.status == "Used" else "Pending Entry"
                    })
            
            if sales_data:
                st.dataframe(pd.DataFrame(sales_data), use_container_width=True)
            else:
                st.info("No sales registered through the POS yet.")
                
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
    finally:
        db.close()
