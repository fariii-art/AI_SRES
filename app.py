"""
app.py — SERS Smart Emergency Response System
Complete with Login System, Three Dashboards, and Interactive Maps
"""

import streamlit as st
import pandas as pd
import datetime
import json

# Import modules
from database import (
    init_db, verify_user,
    insert_incident, get_all_incidents, get_incidents_by_reporter,
    update_status, get_pending_incidents, get_stats,
    get_all_users, create_user, delete_user
)
from ai.model import EmergencyModel
from ai.priority import PriorityEngine
from ai.router import Router

# Try to import map service (optional)
try:
    from services.map_service import map_service
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False

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
        background: linear-gradient(135deg, #1e3a5f 0%, #0f2b45 100%);
    }
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
    .stSidebar {
        background: rgba(0,0,0,0.3) !important;
        backdrop-filter: blur(10px);
    }
    .login-container {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        max-width: 400px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'voice_text' not in st.session_state:
    st.session_state.voice_text = None


# ==================== VOICE RECOGNITION ====================
def voice_input_component():
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
                    statusDiv.innerHTML = '🎙️ Listening...';
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


# ==================== LOGIN PAGE ====================
def show_login():
    st.markdown('<div class="main-header">🚨 SMART EMERGENCY RESPONSE SYSTEM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Emergency Dispatch for Pakistan</div>', unsafe_allow_html=True)
    
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
        
        # Voice input
        st.markdown("### 🎤 Voice Input")
        voice_input_component()
        
        # Handle voice input
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
                    "📝 Description",
                    height=100,
                    placeholder="Describe the emergency...",
                    value=default_text
                )
            
            submitted = st.form_submit_button("🚨 Submit Report", use_container_width=True)
            
            if submitted and description.strip():
                with st.spinner("🤖 Analyzing emergency..."):
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
    
    # Tab 2: Emergency Map
    with tab2:
        st.header("Emergency Incident Map")
        if MAP_AVAILABLE:
            incidents = get_all_incidents()
            units = router.get_unit_status()
            if incidents:
                map_obj = map_service.create_full_dashboard_map(incidents[:100], units, show_heatmap=True)
                map_service.display_map(map_obj)
            else:
                st.info("No incidents to display")
        else:
            st.info("🗺️ Map service loading... Please refresh.")
    
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
                with st.expander(f"#{inc['id']} - {inc['category']} | {inc['city']}", expanded=False):
                    st.write(f"**Priority:** {inc['level']} ({inc['priority']}/100)")
                    st.write(f"**Description:** {inc['description']}")
                    st.write(f"**Unit:** {inc['unit']} | **ETA:** {int(inc['eta'])} min")
                    
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
        if MAP_AVAILABLE:
            incidents = get_all_incidents()
            units = router.get_unit_status()
            if incidents:
                map_obj = map_service.create_full_dashboard_map(incidents[:100], units, show_heatmap=True)
                map_service.display_map(map_obj)
        else:
            st.info("🗺️ Map loading...")
    
    with tab3:
        incidents = get_all_incidents()
        if incidents:
            df = pd.DataFrame(incidents)
            st.dataframe(df, use_container_width=True)


# ==================== ADMIN DASHBOARD ====================
def admin_dashboard():
    st.markdown(f"### 👑 Welcome, {st.session_state.user['full_name']}")
    st.markdown("*System Administration*")
    
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", stats['total'])
    col2.metric("Pending", stats['pending'])
    col3.metric("Dispatched", stats['dispatched'])
    col4.metric("Resolved", stats['resolved'])
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🗺️ National Map", "👥 Users", "🚒 Units"])
    
    with tab1:
        incidents = get_all_incidents()
        if incidents:
            df = pd.DataFrame(incidents)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Category Distribution")
                st.bar_chart(df['category'].value_counts())
            with col2:
                st.subheader("Priority Level")
                st.bar_chart(df['level'].value_counts())
    
    with tab2:
        if MAP_AVAILABLE:
            incidents = get_all_incidents()
            units = router.get_unit_status()
            if incidents:
                map_obj = map_service.create_full_dashboard_map(incidents, units, show_heatmap=True)
                map_service.display_map(map_obj)
        else:
            st.info("🗺️ Map loading...")
    
    with tab3:
        users = get_all_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True)
    
    with tab4:
        units = router.get_unit_status()
        df_units = pd.DataFrame(units)
        df_units['Status'] = df_units['available'].apply(lambda x: "✅ Available" if x else "🔴 Deployed")
        st.dataframe(df_units[['id', 'type', 'city', 'Status']], use_container_width=True)


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
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5);'>SERS - Smart Emergency Response System | AI-Powered Emergency Dispatch for Pakistan</p>", unsafe_allow_html=True)
