"""
app.py — SERS Smart Emergency Response System
Complete with Login System and Three Dashboards (Admin, Operator, Reporter)
"""

import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go

# Import modules
from database import (
    init_db, verify_user, get_user_by_username,
    insert_incident, get_all_incidents, get_incidents_by_reporter,
    update_status, get_pending_incidents, get_stats,
    get_all_users, create_user, delete_user
)
from ai.model import EmergencyModel
from ai.priority import PriorityEngine
from ai.router import Router

# Page config
st.set_page_config(
    page_title="SERS - Smart Emergency Response System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Load models
@st.cache_resource
def load_models():
    model = EmergencyModel()
    priority = PriorityEngine()
    router = Router()
    return model, priority, router

model, priority_engine, router = load_models()

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    .main-header {
        background: linear-gradient(135deg, #ff6b6b, #feca57);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
    }
    .login-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
    }
    .priority-critical { background: #ff0000; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; }
    .priority-high { background: #ff6600; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; }
    .priority-medium { background: #ffaa00; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; }
    .priority-low { background: #00cc66; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; }
    .stButton > button {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        color: white;
        border-radius: 40px;
        font-weight: 600;
        width: 100%;
    }
    .stMetric {
        background: rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 10px;
    }
    .dashboard-card {
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None

# ==================== LOGIN PAGE ====================
def show_login():
    st.markdown('<p class="main-header">🚨 SMART EMERGENCY RESPONSE SYSTEM</p>', unsafe_allow_html=True)
    st.markdown("*AI-Powered Emergency Dispatch for Pakistan*")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.subheader("🔐 Login to SERS")
            st.markdown("---")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            role = st.selectbox("Select Role", ["Reporter", "Operator", "Admin"])
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_btn = st.button("Login", use_container_width=True)
            with col_btn2:
                st.markdown("")
            
            if login_btn:
                if username and password:
                    user = verify_user(username, password)
                    if user and user['role'] == role:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.role = role
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or role mismatch")
                else:
                    st.warning("⚠️ Please enter username and password")
            
            st.markdown("---")
            st.caption("Demo Credentials:")
            st.caption("Reporter: reporter / rep123")
            st.caption("Operator: operator / op123")
            st.caption("Admin: admin / admin123")
            st.markdown('</div>', unsafe_allow_html=True)

# ==================== LOGOUT ====================
def logout():
    for key in ['logged_in', 'user', 'role']:
        st.session_state.pop(key, None)
    st.rerun()

# ==================== REPORTER DASHBOARD ====================
def reporter_dashboard():
    st.markdown(f"### 👋 Welcome, {st.session_state.user['full_name']}")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📢 Report Emergency", "📋 My Reports"])
    
    # Tab 1: Report Emergency
    with tab1:
        st.header("Report an Emergency")
        
        with st.form("report_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                city = st.selectbox("📍 City", router.get_cities())
                time_of_day = st.selectbox("🌙 Time of Day", ["Day", "Night"])
                phone = st.text_input("📱 Phone Number (for alerts)", placeholder="+923001234567")
            
            with col2:
                st.markdown("### 📝 Incident Details")
                pass
            
            description = st.text_area(
                "Describe the emergency (English or Urdu)",
                height=150,
                placeholder="Examples:\n• Fire in building at Lahore\n• Car accident on highway near Islamabad\n• آگ لگ گئی ہے عمارت میں"
            )
            
            submitted = st.form_submit_button("🚨 Submit Emergency Report", use_container_width=True)
        
        if submitted and description.strip():
            with st.spinner("🤖 Analyzing emergency and dispatching unit..."):
                category, confidence, probs = model.predict(description)
                priority, level = priority_engine.score(category, description, confidence, time_of_day)
                unit, eta, route, from_city = router.find_best_unit(city, category)
                
                insert_incident(
                    st.session_state.user['username'], city, description, category,
                    confidence, priority, level, unit, eta, " → ".join(route),
                    phone=phone
                )
                router.mark_dispatched(unit)
                
                st.balloons()
                st.success("✅ Emergency reported successfully! Help is on the way.")
                
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("📋 Category", category)
                col_b.metric("🎯 Priority", f"{priority}/100")
                col_c.metric("📊 Level", level)
                col_d.metric("⏱️ ETA", f"{int(eta)} min")
                
                st.info(f"🚒 **Dispatched Unit:** `{unit}` from {from_city}\n\n**Route:** {' → '.join(route)}")
    
    # Tab 2: My Reports
    with tab2:
        st.header("My Report History")
        reports = get_incidents_by_reporter(st.session_state.user['username'])
        
        if reports:
            df = pd.DataFrame(reports)
            display_cols = ['id', 'timestamp', 'city', 'category', 'priority', 'level', 'status', 'eta']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 You haven't submitted any reports yet.")

# ==================== OPERATOR DASHBOARD ====================
def operator_dashboard():
    st.markdown(f"### 🚒 Welcome, {st.session_state.user['full_name']}")
    st.markdown("*Emergency Dispatch Control Center*")
    st.markdown("---")
    
    # Stats row
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", stats['total'])
    col2.metric("Pending", stats['pending'], delta="Urgent" if stats['pending'] > 0 else None)
    col3.metric("Dispatched", stats['dispatched'])
    col4.metric("Resolved", stats['resolved'])
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["⏳ Pending Incidents", "📋 All Incidents"])
    
    # Tab 1: Pending Incidents
    with tab1:
        st.header("Pending Incidents - Ready for Dispatch")
        pending = get_pending_incidents()
        
        if pending:
            for inc in pending:
                priority_badge = f'<span class="priority-{inc["level"].lower()}">{inc["level"].upper()} ({inc["priority"]})</span>'
                
                with st.expander(f"#{inc['id']} — {inc['category']} | Priority {priority_badge} | {inc['city']}", expanded=True):
                    st.markdown(f"**Reported by:** {inc['reporter']} | **Time:** {inc['timestamp']}")
                    st.markdown(f"**Description:** {inc['description']}")
                    st.markdown("---")
                    st.markdown(f"**Assigned Unit:** `{inc['unit']}` | **ETA:** {int(inc['eta'])} min")
                    st.markdown(f"**Route:** {inc['route']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Dispatch Unit", key=f"disp_{inc['id']}", use_container_width=True):
                            update_status(inc['id'], "Dispatched")
                            st.success(f"Unit {inc['unit']} dispatched!")
                            st.rerun()
                    with col2:
                        if st.button(f"🏁 Mark Resolved", key=f"res_{inc['id']}", use_container_width=True):
                            update_status(inc['id'], "Resolved")
                            router.mark_available(inc['unit'])
                            st.success(f"Incident #{inc['id']} resolved!")
                            st.rerun()
        else:
            st.success("✅ No pending incidents. All clear!")
            st.balloons()
    
    # Tab 2: All Incidents
    with tab2:
        st.header("All Incidents")
        incidents = get_all_incidents()
        
        if incidents:
            df = pd.DataFrame(incidents)
            display_cols = ['id', 'timestamp', 'city', 'category', 'priority', 'level', 'status', 'unit', 'eta']
            st.dataframe(df[display_cols], use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export CSV", csv, "sers_incidents.csv", "text/csv")

# ==================== ADMIN DASHBOARD ====================
def admin_dashboard():
    st.markdown(f"### 👑 Welcome, {st.session_state.user['full_name']}")
    st.markdown("*System Administration Dashboard*")
    st.markdown("---")
    
    # Stats row
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", stats['total'])
    col2.metric("Pending", stats['pending'])
    col3.metric("Dispatched", stats['dispatched'])
    col4.metric("Resolved", stats['resolved'])
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "📋 All Incidents", "👥 User Management", "🚒 Unit Fleet"])
    
    # Tab 1: Analytics
    with tab1:
        st.header("Analytics Dashboard")
        incidents = get_all_incidents()
        
        if incidents:
            df = pd.DataFrame(incidents)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Category Distribution")
                category_counts = df['category'].value_counts()
                fig = px.pie(values=category_counts.values, names=category_counts.index, title="Incidents by Category")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Priority Level Distribution")
                level_counts = df['level'].value_counts()
                fig = px.bar(x=level_counts.index, y=level_counts.values, title="Incidents by Priority", color=level_counts.index)
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Daily Incident Trend")
            daily = df.groupby(df['timestamp'].dt.date).size().reset_index(name='count')
            fig = px.line(daily, x='timestamp', y='count', title="Incidents Over Time")
            st.plotly_chart(fig, use_container_width=True)
            
            # Model info
            st.subheader("AI Model Performance")
            if hasattr(model, 'eval_accuracy'):
                st.metric("Model Accuracy", f"{model.eval_accuracy}%")
            st.code("""
            Model: TF-IDF + Logistic Regression
            Categories: Fire, Accident, Medical, Crime, Flood, Earthquake
            Languages: English, Urdu, Romanized Urdu
            """)
    
    # Tab 2: All Incidents
    with tab2:
        st.header("All Incidents")
        incidents = get_all_incidents()
        
        if incidents:
            df = pd.DataFrame(incidents)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Full Data", csv, "sers_full_data.csv", "text/csv")
    
    # Tab 3: User Management
    with tab3:
        st.header("User Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add New User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["Reporter", "Operator", "Admin"])
                new_fullname = st.text_input("Full Name")
                new_phone = st.text_input("Phone")
                
                if st.form_submit_button("Add User", use_container_width=True):
                    if create_user(new_username, new_password, new_role, new_fullname, new_phone):
                        st.success(f"User {new_username} created!")
                        st.rerun()
                    else:
                        st.error("Username already exists!")
        
        with col2:
            st.subheader("Existing Users")
            users = get_all_users()
            if users:
                df_users = pd.DataFrame(users)
                st.dataframe(df_users, use_container_width=True)
                
                st.subheader("Delete User")
                user_to_delete = st.selectbox("Select User to Delete", [u['username'] for u in users if u['username'] not in ['admin', 'operator', 'reporter']])
                if st.button("Delete User", use_container_width=True):
                    user = next((u for u in users if u['username'] == user_to_delete), None)
                    if user:
                        delete_user(user['id'])
                        st.success(f"User {user_to_delete} deleted!")
                        st.rerun()
    
    # Tab 4: Unit Fleet
    with tab4:
        st.header("Response Unit Fleet")
        units = router.get_unit_status()
        df_units = pd.DataFrame(units)
        df_units['Status'] = df_units['available'].apply(lambda x: "✅ Available" if x else "🔴 Deployed")
        st.dataframe(df_units[['id', 'type', 'city', 'Status']], use_container_width=True)

# ==================== MAIN ====================
if not st.session_state.logged_in:
    show_login()
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['full_name']}")
        st.markdown(f"*Role: {st.session_state.role}*")
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        st.markdown("### 🎯 Priority Guide")
        st.markdown('<span class="priority-critical">CRITICAL (80-100)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-high">HIGH (60-79)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-medium">MEDIUM (40-59)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-low">LOW (0-39)</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📞 Emergency")
        st.markdown("**1122** - Rescue")
        st.markdown("**15** - Police")
        st.markdown("**16** - Fire")
    
    # Render appropriate dashboard
    if st.session_state.role == "Reporter":
        reporter_dashboard()
    elif st.session_state.role == "Operator":
        operator_dashboard()
    elif st.session_state.role == "Admin":
        admin_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>SERS - Smart Emergency Response System | AI-Powered Emergency Dispatch for Pakistan</p>",
        unsafe_allow_html=True
    )