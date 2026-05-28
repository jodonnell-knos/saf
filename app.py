import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px

# 1. Page Setup
st.set_page_config(page_title="Student Activity Funds", layout="wide")
st.title("🎓 Student Activity Fund Dashboard")
st.write("Interactive overview of school accounts, cash flow, and vendor spending.")

# 2. Database Connection
@st.cache_resource
def init_connection():
    # Pulling credentials securely from Streamlit Secrets
    server = st.secrets["DB_SERVER"]
    database = st.secrets["DB_DATABASE"]
    username = st.secrets["DB_USERNAME"]
    password = st.secrets["DB_PASSWORD"]
    
    # Note: If Streamlit Cloud throws a driver error, change this 18 to a 17
    driver = '{ODBC Driver 18 for SQL Server}' 
    
    conn_str = f"DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(conn_str)

conn = init_connection()

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
        fig_trend = px.line(monthly_trend, x='month_
