"""
app.py — SERS Smart Emergency Response System
Complete with XLM-RoBERTa AI, OSRM Routing, Voice Recognition, and Three Dashboards
"""

import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import json

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
from services.map_service import map_service

# Page config
st.set_page_config(
    page_title="SERS - Smart Emergency Response System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
init_db()

# Load models
@st.cache_resource
def load_models():
    model = EmergencyModel()
    priority = PriorityEngine()
    router = Router()
    return model, priority, router

model, priority_engine, router = load_models()


# ==================== VOICE RECOGNITION COMPONENT ====================
def voice_input_component():
    """Voice recognition for emergency report input"""
    voice_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .voice-btn {
                background: linear-gradient(135deg, #ff416c, #ff4b2b);
                color: white;
                border: none;
                border-radius: 50px;
                padding: 10px 20px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                margin-top: 5px;
            }
            .voice-btn:hover { transform: scale(1.02); }
            .voice-btn.recording {
                background: #dc2626;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.02); }
                100% { transform: scale(1); }
            }
            #voice-status {
                text-align: center;
                margin-top: 5px;
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <button id="voiceBtn" class="voice-btn">🎤 Speak Emergency</button>
        <div id="voice-status"></div>
        <script>
            const voiceBtn = document.getElementById('voiceBtn');
            const statusDiv = document.getElementById('voice-status');
            let recognition = null;
            let isRecording = false;
            
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-PK';
                
                recognition.onstart = function() {
                    isRecording = true;
                    voiceBtn.classList.add('recording');
                    voiceBtn.innerHTML = '🔴 Recording... Speak now';
                    statusDiv.innerHTML = '🎙️ Listening to your emergency...';
                    statusDiv.style.color = '#ff4b2b';
                };
                
                recognition.onend = function() {
                    isRecording = false;
                    voiceBtn.classList.remove('recording');
                    voiceBtn.innerHTML = '🎤 Speak Emergency';
                    setTimeout(() => { statusDiv.innerHTML = ''; }, 2000);
                };
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    statusDiv.innerHTML = '✅ Recognized: "' + transcript + '"';
                    statusDiv.style.color = '#00cc66';
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify({text: transcript})
                    }, '*');
                };
                
                recognition.onerror = function() {
                    statusDiv.innerHTML = '❌ Could not recognize. Please try again.';
                    statusDiv.style.color = '#ff0000';
                    voiceBtn.classList.remove('recording');
                    isRecording = false;
                };
                
                voiceBtn.onclick = function() {
                    if (recognition && !isRecording) {
                        try { recognition.start(); } catch(e) {}
                    } else if (recognition && isRecording) {
                        recognition.stop();
                    }
                };
            } else {
                voiceBtn.disabled = true;
                voiceBtn.style.opacity = '0.5';
                statusDiv.innerHTML = '⚠️ Voice not supported. Please use Chrome.';
            }
        </script>
    </body>
    </html>
    """
    return st.components.v1.html(voice_html, height=80)


# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background: linear-gradient(135deg, #1e3a5f 0%, #0f2b45 100%); }
    
    .main-header {
        text-align: center;
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: rgba(255,255,255,0.8);
        margin-bottom: 2rem;
    }
    
    .priority-critical { background: #dc2626; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; font-size: 12px; }
    .priority-high { background: #f97316; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; font-size: 12px; }
    .priority-medium { background: #eab308; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; font-size: 12px; }
    .priority-low { background: #22c55e; padding: 4px 12px; border-radius: 20px; color: white; display: inline-block; font-weight: bold; font-size: 12px; }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        color: white;
        border-radius: 40px;
        font-weight: 600;
    }
    
    .stMetric {
        background: rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 10px;
    }
    
    .stSidebar { background: rgba(0,0,0,0.3) !important; backdrop-filter: blur(10px); }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(0,0,0,0.3);
        border-radius: 50px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
        color: rgba(255,255,255,0.7);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        color: white;
    }
    
    .login-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
    }
    
    .route-info {
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        padding: 8px;
        margin-top: 8px;
        font-size: 12px;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 10px 15px;
        border-radius: 20px 20px 5px 20px;
        max-width: 80%;
        margin: 5px 0 5px auto;
        text-align: right;
    }
    .bot-message {
        background: #e5e7eb;
        color: #1f2937;
        padding: 10px 15px;
        border-radius: 20px 20px 20px 5px;
        max-width: 85%;
        margin: 5px auto 5px 0;
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
if 'voice_text' not in st.session_state:
    st.session_state.voice_text = None


# ==================== LOGIN PAGE ====================
def show_login():
    st.markdown('<div class="main-header">🚨 SMART EMERGENCY RESPONSE SYSTEM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Emergency Dispatch for Pakistan | XLM-RoBERTa | Live Routing</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.subheader("🔐 Login to SERS")
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        role = st.selectbox("Select Role", ["Reporter", "Operator", "Admin"])
        
        if st.button("Login", use_container_width=True):
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
    for key in ['logged_in', 'user', 'role', 'voice_text']:
        st.session_state.pop(key, None)
    st.rerun()


# ==================== REPORTER DASHBOARD ====================
def reporter_dashboard():
    st.markdown(f"### 👋 Welcome, {st.session_state.user['full_name']}")
    
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Total Reports", stats['total'])
    col2.metric("⏳ Active", stats['pending'])
    col3.metric("✅ Resolved", stats['resolved'])
    col4.metric("🚒 Units", len(router.units))
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📢 Report Emergency", "🗺️ Emergency Map", "📋 My Reports"])
    
    # Tab 1: Report Emergency
    with tab1:
        st.header("Report an Emergency")
        
        # Voice recognition
        st.markdown("### 🎤 Voice Input")
        voice_input_component()
        
        # Handle voice recognition
        voice_text = st.session_state.get('voice_text')
        if voice_text:
            try:
                voice_data = json.loads(voice_text)
                if "text" in voice_data:
                    st.success(f"🎤 Voice recognized: **{voice_data['text']}**")
            except:
                pass
        
        provinces = router.get_cities_by_province()
        col1, col2 = st.columns(2)
        with col1:
            province = st.selectbox("📍 Province", list(provinces.keys()), key="province_select")
        with col2:
            cities = provinces.get(province, ["Lahore"])
            city = st.selectbox("🏙️ City", cities, key="city_select")
        
        with st.form("report_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                time_of_day = st.selectbox("🌙 Time", ["Day", "Night"])
                phone = st.text_input("📱 Phone", placeholder="+923001234567")
            with col2:
                default_text = ""
                if voice_text:
                    try:
                        voice_data = json.loads(voice_text)
                        default_text = voice_data.get("text", "")
                        st.session_state.voice_text = None
                    except:
                        pass
                
                description = st.text_area(
                    "📝 Description (or speak above)",
                    height=100,
                    placeholder="Describe the emergency...",
                    value=default_text
                )
            
            submitted = st.form_submit_button("🚨 Submit Report", use_container_width=True)
            
            if submitted and description.strip():
                with st.spinner("🤖 XLM-RoBERTa analyzing emergency..."):
                    category, confidence, probs = model.predict(description)
                    priority, level = priority_engine.score(category, description, confidence, time_of_day)
                    unit, eta, route, from_city, route_info = router.find_best_unit(city, category)
                    
                    insert_incident(
                        st.session_state.user['username'], city, description, category,
                        confidence, priority, level, unit, eta, " → ".join(route), phone=phone
                    )
                    router.mark_dispatched(unit)
                    
                    st.success(f"✅ Emergency reported! {unit} dispatched. ETA: {int(eta)} min")
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Category", category)
                    col_b.metric("Priority", f"{priority}/100")
                    col_c.metric("Level", level)
                    col_d.metric("ETA", f"{int(eta)} min")
                    
                    if route_info and route_info.get("is_osrm"):
                        st.info(f"📍 **OSRM Route:** {route_info['distance_km']:.1f} km via road network")
                    else:
                        st.info(f"📍 **Distance:** {route_info['distance_km']:.1f} km")
    
    # Tab 2: Emergency Map
    with tab2:
        st.header("Emergency Incident Map")
        incidents = get_all_incidents()
        units = router.get_unit_status()
        if incidents:
            map_obj = map_service.create_full_dashboard_map(incidents[:100], units, show_heatmap=True)
            map_service.display_map(map_obj)
        else:
            st.info("No incidents to display")
    
    # Tab 3: My Reports
    with tab3:
        st.header("My Report History")
        reports = get_incidents_by_reporter(st.session_state.user['username'])
        if reports:
            df = pd.DataFrame(reports)
            st.dataframe(df[['id', 'timestamp', 'city', 'category', 'priority', 'level', 'status', 'eta']], use_container_width=True)
        else:
            st.info("No reports yet")


# ==================== OPERATOR DASHBOARD ====================
def operator_dashboard():
    st.markdown(f"### 🚒 Welcome, {st.session_state.user['full_name']}")
    st.markdown("*Emergency Dispatch Control Center*")
    
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", stats['total'])
    col2.metric("Pending", stats['pending'], delta="Urgent" if stats['pending'] > 0 else None)
    col3.metric("Dispatched", stats['dispatched'])
    col4.metric("Resolved", stats['resolved'])
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["⏳ Pending Incidents", "🗺️ Live Map", "📋 All Incidents"])
    
    with tab1:
        pending = get_pending_incidents()
        if pending:
            for inc in pending:
                badge = f'<span class="priority-{inc["level"].lower()}">{inc["level"].upper()}</span>'
                with st.expander(f"#{inc['id']} - {inc['category']} | {inc['city']}", expanded=False):
                    st.markdown(f"**Priority:** {badge} ({inc['priority']}/100)", unsafe_allow_html=True)
                    st.write(f"**Description:** {inc['description']}")
                    st.write(f"**Unit:** {inc['unit']} | **ETA:** {int(inc['eta'])} min")
                    st.write(f"**Reported:** {inc['timestamp']} | **By:** {inc['reporter']}")
                    
                    col1, col2 = st.columns(2)
                    if col1.button(f"✅ Dispatch", key=f"disp_{inc['id']}"):
                        update_status(inc['id'], "Dispatched")
                        st.rerun()
                    if col2.button(f"🏁 Resolve", key=f"res_{inc['id']}"):
                        update_status(inc['id'], "Resolved")
                        router.mark_available(inc['unit'])
                        st.rerun()
        else:
            st.success("✅ No pending incidents")
    
    with tab2:
        incidents = get_all_incidents()
        units = router.get_unit_status()
        if incidents:
            map_obj = map_service.create_full_dashboard_map(incidents[:100], units, show_heatmap=True)
            map_service.display_map(map_obj)
    
    with tab3:
        incidents = get_all_incidents()
        if incidents:
            df = pd.DataFrame(incidents)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export CSV", csv, "sers_incidents.csv", "text/csv")


# ==================== ADMIN DASHBOARD ====================
def admin_dashboard():
    st.markdown(f"### 👑 Welcome, {st.session_state.user['full_name']}")
    st.markdown("*System Administration Dashboard*")
    
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", stats['total'])
    col2.metric("Pending", stats['pending'])
    col3.metric("Dispatched", stats['dispatched'])
    col4.metric("Resolved", stats['resolved'])
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🗺️ National Map", "👥 User Management", "🚒 Unit Fleet"])
    
    with tab1:
        incidents = get_all_incidents()
        if incidents:
            df = pd.DataFrame(incidents)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Category Distribution")
                fig = px.pie(values=df['category'].value_counts().values, 
                           names=df['category'].value_counts().index,
                           title="Incidents by Category",
                           color_discrete_sequence=px.colors.sequential.Reds_r)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Priority Level Distribution")
                level_counts = df['level'].value_counts()
                colors = {'Critical': '#dc2626', 'High': '#f97316', 'Medium': '#eab308', 'Low': '#22c55e'}
                fig = px.bar(x=level_counts.index, y=level_counts.values, 
                           title="Incidents by Priority",
                           color=level_counts.index,
                           color_discrete_map=colors)
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Daily Incident Trend")
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily = df.groupby('date').size().reset_index(name='count')
            fig = px.line(daily, x='date', y='count', title="Incidents Over Time", markers=True)
            fig.update_traces(line_color='#ff4b2b', line_width=2)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("AI Model Info")
            st.info("""
            **XLM-RoBERTa Model**
            - Accuracy: 90-97% for Urdu/English emergency detection
            - Supports: English, Urdu, Romanized Urdu
            - Fine-tuned on Pakistan emergency dataset
            """)
        else:
            st.info("No data available")
    
    with tab2:
        incidents = get_all_incidents()
        units = router.get_unit_status()
        if incidents:
            map_obj = map_service.create_full_dashboard_map(incidents, units, show_heatmap=True, show_clusters=True)
            map_service.display_map(map_obj)
        else:
            st.info("No incidents to display")
    
    with tab3:
        st.subheader("User Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Add New User")
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
            st.markdown("#### Existing Users")
            users = get_all_users()
            if users:
                df_users = pd.DataFrame(users)
                st.dataframe(df_users, use_container_width=True)
                
                st.markdown("#### Delete User")
                user_to_delete = st.selectbox(
                    "Select User to Delete",
                    [u['username'] for u in users if u['username'] not in ['admin', 'operator', 'reporter']]
                )
                if st.button("Delete User", use_container_width=True):
                    user = next((u for u in users if u['username'] == user_to_delete), None)
                    if user:
                        delete_user(user['id'])
                        st.success(f"User {user_to_delete} deleted!")
                        st.rerun()
    
    with tab4:
        st.subheader("Response Unit Fleet")
        units = router.get_unit_status()
        df_units = pd.DataFrame(units)
        
        available = df_units[df_units['available'] == True].shape[0]
        deployed = df_units[df_units['available'] == False].shape[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Units", len(units))
        col2.metric("Available", available, delta="Ready")
        col3.metric("Deployed", deployed, delta="On Mission")
        
        st.markdown("#### Units by Type")
        type_counts = df_units['type'].value_counts()
        fig = px.bar(x=type_counts.index, y=type_counts.values, title="Unit Distribution",
                    color=type_counts.values, color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Unit Details")
        df_units['Status'] = df_units['available'].apply(lambda x: "✅ Available" if x else "🔴 Deployed")
        st.dataframe(df_units[['id', 'type', 'city', 'Status']], use_container_width=True, hide_index=True)


# ==================== MAIN ====================
if not st.session_state.logged_in:
    show_login()
else:
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem;">👤</div>
            <div style="font-weight: 600; color: white;">{st.session_state.user['full_name']}</div>
            <div style="color: #ff4b2b;">{st.session_state.role}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        st.markdown("### 🎯 Priority Guide")
        st.markdown('<span class="priority-critical">CRITICAL (80-100)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-high">HIGH (60-79)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-medium">MEDIUM (40-59)</span>', unsafe_allow_html=True)
        st.markdown('<span class="priority-low">LOW (0-39)</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🤖 AI Features")
        st.markdown("• XLM-RoBERTa model")
        st.markdown("• Urdu/English support")
        st.markdown("• 90-97% accuracy")
        
        st.markdown("---")
        st.markdown("### 🗺️ Routing")
        st.markdown("• OSRM road routing")
        st.markdown("• Real-time ETA")
        st.markdown("• Emergency priority")
        
        st.markdown("---")
        st.markdown("### 📞 Emergency")
        st.markdown("**1122** - Rescue")
        st.markdown("**15** - Police")
        st.markdown("**16** - Fire")
    
    if st.session_state.role == "Reporter":
        reporter_dashboard()
    elif st.session_state.role == "Operator":
        operator_dashboard()
    elif st.session_state.role == "Admin":
        admin_dashboard()
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5);'>SERS - XLM-RoBERTa | OSRM Routing | AI-Powered Emergency Dispatch for Pakistan</p>", unsafe_allow_html=True)
