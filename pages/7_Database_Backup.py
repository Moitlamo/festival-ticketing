import pandas as pd
from datetime import datetime
import streamlit as st
from models import engine # Ensure this points to your active models.py

st.divider()

# Standalone Backup Section
st.subheader("💾 Database Backup & Export")
st.caption("Download a complete, real-time snapshot of all issued tickets and gate scans.")

try:
    # 1. Query the entire tickets table directly into a dataframe
    df_backup = pd.read_sql_table("tickets", con=engine)
    
    # 2. Convert dataframe to CSV format
    csv_data = df_backup.to_csv(index=False).encode('utf-8')
    
    # 3. Generate a dynamic filename with the exact date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    export_filename = f"festival_backup_{timestamp}.csv"
    
    # 4. Render the Streamlit download button
    st.download_button(
        label="📥 Download Full Database (CSV)",
        data=csv_data,
        file_name=export_filename,
        mime="text/csv",
        type="primary",
        use_container_width=True
    )
    
except Exception as e:
    st.error("🚨 Backup failed to generate. Check database connection.")
    st.code(str(e))
