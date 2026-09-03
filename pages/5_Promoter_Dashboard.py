import streamlit as st
import pandas as pd
import re
from models import SessionLocal, Ticket

st.set_page_config(page_title="Promoter Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    .stTextInput>div>div>input { background-color: #1e293b; color: white; }
    .metric-card { background-color: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #7f1d1d; }
    .metric-title { font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 32px; font-weight: bold; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Live Promoter Dashboard")
st.write("Real-time event financials, gate conversions, and vendor tracking.")

# --- SYSTEM AUTHENTICATION ---
USER_EVENT_MAP = {
    "moitlamoleririma": "Leririma Games",
    "moitlamotfm": "Total Football Mania",
    "moitlamoeea": "Education Excellence Awards"
}

admin_username = st.text_input("Enter System Username", type="password")

if not admin_username:
    st.info("Please enter your username to view live event metrics.")
    st.stop()

auth_key = admin_username.strip().lower()
selected_event = USER_EVENT_MAP.get(auth_key)

if not selected_event:
    st.error("⚠️ Invalid username. No event associated with this account.")
    st.stop()

st.success(f"✅ Dashboard locked to: **{selected_event}**")
st.markdown("---")

# --- DATA EXTRACTION & PROCESSING ---
db = SessionLocal()
try:
    all_tickets = db.query(Ticket).all()
    event_tickets = [t for t in all_tickets if selected_event in str(t.buyer_phone) or selected_event in str(t.ticket_type)]
    
    if not event_tickets:
        st.warning(f"No ticket data found yet for {selected_event}.")
        st.stop()

    total_revenue = 0.0
    digital_count = 0
    physical_count = 0
    scanned_count = 0
    vendor_stats = {}

    for t in event_tickets:
        if t.status == "Used":
            scanned_count += 1
            
        if t.ticket_type == "Physical":
            physical_count += 1
        else:
            digital_count += 1
            
        numeric_val = 0.0
        parts = str(t.buyer_phone).split(" | ")
        
        # Safely isolate ONLY the Value segment to prevent merging with phone numbers
        val_part = [p for p in parts if "Value:" in p]
        if val_part:
            try:
                val_str = val_part[0].replace("Value:", "").strip()
                numeric_val = float(re.sub(r'[^\d.]', '', val_str))
                total_revenue += numeric_val
            except:
                pass
                
        # Safely isolate ONLY the Vendor segment
        vendor_part = [p for p in parts if "Vendor:" in p]
        if vendor_part:
            try:
                v_name = vendor_part[0].replace("Vendor:", "").split("[")[0].strip()
                if v_name not in vendor_stats:
                    vendor_stats[v_name] = {"Tickets Issued": 0, "Gate Check-ins": 0, "Revenue Generated (P)": 0.0}
                
                vendor_stats[v_name]["Tickets Issued"] += 1
                
                if t.status == "Used":
                    vendor_stats[v_name]["Gate Check-ins"] += 1
                
                vendor_stats[v_name]["Revenue Generated (P)"] += numeric_val
            except:
                pass

    total_issued = len(event_tickets)
    attendance_rate = (scanned_count / total_issued) * 100 if total_issued > 0 else 0

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Estimated Gross Revenue</div>
            <div class="metric-value">P {total_revenue:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Tickets Issued</div>
            <div class="metric-value">{total_issued}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Live Gate Check-ins</div>
            <div class="metric-value">{scanned_count} <span style="font-size:16px; color:#34d399;">({attendance_rate:.1f}%)</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    colA, colB = st.columns([1, 2])
    
    with colA:
        st.subheader("Ticket Distribution")
        dist_df = pd.DataFrame({
            "Channel": ["Physical (Vendors)", "Digital (WhatsApp/SMS)"],
            "Count": [physical_count, digital_count]
        }).set_index("Channel")
        st.bar_chart(dist_df, color="#7f1d1d")
        
    with colB:
        st.subheader("Top Vendor Performance")
        if vendor_stats:
            vendor_df = pd.DataFrame.from_dict(vendor_stats, orient='index')
            vendor_df["Conversion %"] = (vendor_df["Gate Check-ins"] / vendor_df["Tickets Issued"] * 100).round(1)
            vendor_df = vendor_df.sort_values(by="Revenue Generated (P)", ascending=False)
            st.dataframe(vendor_df, use_container_width=True)
        else:
            st.info("No physical vendor data recorded for this event yet.")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
finally:
    db.close()
