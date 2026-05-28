import streamlit as st
import pandas as pd
import pymssql
import plotly.express as px
import time

# 1. Page Setup
st.set_page_config(page_title="Student Activity Funds", layout="wide")
st.title("🎓 Student Activity Fund Dashboard")
st.write("Interactive overview of school accounts, cash flow, and vendor spending.")

# 2. Resilient Database Connection (Forcing it to wait for Azure Serverless to wake up)
@st.cache_resource
def init_connection():
    max_retries = 5
    retry_delay = 15  # Gives Azure a total of 75 seconds to spin up
    
    for attempt in range(max_retries):
        try:
            return pymssql.connect(
                server=st.secrets["DB_SERVER"],
                user=st.secrets["DB_USERNAME"],
                password=st.secrets["DB_PASSWORD"],
                database=st.secrets["DB_DATABASE"],
                login_timeout=30
            )
        except (pymssql.OperationalError, pymssql.InterfaceError) as e:
            # Detect Azure 40613 "database not currently available" sleep mode
            is_sleeping = False
            if hasattr(e, 'args') and len(e.args) > 0 and e.args[0] == 40613:
                is_sleeping = True
            elif "40613" in str(e):
                is_sleeping = True
                
            if is_sleeping and attempt < max_retries - 1:
                st.toast(f"😴 Azure is waking up the database... retrying in {retry_delay}s (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise e

try:
    conn = init_connection()
except Exception as e:
    st.error(f"❌ Connection failed permanently. If this keeps happening, double-check your password strings in your Streamlit Advanced Secrets box. Error: {e}")
    st.stop()

# 3. Fetch the Data (Using your built-in SQL Views)
@st.cache_data
def load_data():
    # Load monthly activity for trends
    activity_query = "SELECT * FROM saf.v_monthly_activity"
    activity_df = pd.read_sql(activity_query, conn)
    activity_df['month_end'] = pd.to_datetime(activity_df['month_end'])
    
    # Load top vendors for spending analysis
    vendor_query = "SELECT * FROM saf.v_top_vendors"
    vendors_df = pd.read_sql(vendor_query, conn)
    
    return activity_df, vendors_df

activity_df, vendors_df = load_data()

# 4. Interactive Sidebar Filters
st.sidebar.header("Filter Dashboard")
schools = activity_df['school'].dropna().unique()
selected_schools = st.sidebar.multiselect("Select School(s):", options=schools, default=schools)

# Apply filters to dataframes
f_activity = activity_df[activity_df['school'].isin(selected_schools)]
f_vendors = vendors_df[vendors_df['school'].isin(selected_schools)]

# 5. Dashboard Visualizations
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Net Cash Flow")
    if not f_activity.empty:
        monthly_trend = f_activity.groupby('month_end')['net_cash_flow'].sum().reset_index()
        fig_trend = px.line(monthly_trend, x='month_end', y='net_cash_flow', markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No data available for the selected schools.")

with col2:
    st.subheader("Top 10 Vendors by Total Spend")
    if not f_vendors.empty:
        top_v = f_vendors.groupby('vendor')['total_spend'].sum().nlargest(10).reset_index()
        fig_vendors = px.bar(top_v, x='vendor', y='total_spend', text_auto='.2s')
        st.plotly_chart(fig_vendors, use_container_width=True)
    else:
        st.info("No data available for the selected schools.")

# 6. Raw Data Tables
st.divider()
st.subheader("Raw Monthly Activity Data")
st.dataframe(f_activity, use_container_width=True)
