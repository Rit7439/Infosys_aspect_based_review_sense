import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3

# Configuration
API_URL = "http://localhost:8000"

# Database connection helper
def get_db():
    """Get database connection"""
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Page config
st.set_page_config(
    page_title="Aspect Sentiment Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: #ffffff;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
        border: 2px solid #3b82f6;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(59,130,246,0.3);
    }
    
    .stat-card h3 {
        font-size: 2rem;
        margin: 0;
        font-weight: 700;
        color: #ffffff;
    }
    
    .stat-card p {
        color: #e2e8f0;
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
    }
    
    .positive-card {
        background: linear-gradient(135deg, #1a4d2e 0%, #0f2818 100%);
        border-color: #10b981;
    }
    
    .negative-card {
        background: linear-gradient(135deg, #5a1a1a 0%, #3d0f0f 100%);
        border-color: #ef4444;
    }
    
    .neutral-card {
        background: linear-gradient(135deg, #5a3a1a 0%, #3d2410 100%);
        border-color: #f59e0b;
    }
    
    .info-card {
        background: linear-gradient(135deg, #1a3a5a 0%, #0f2438 100%);
        border-color: #3b82f6;
    }
    
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }
    
    .toggle-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
        justify-content: center;
    }
    
    .toggle-btn {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: 2px solid #667eea;
        background: white;
        color: #667eea;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .toggle-btn.active {
        background: #667eea;
        color: white;
    }
    
    .sentiment-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .sentiment-badge.positive {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .sentiment-badge.negative {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    
    .sentiment-badge.neutral {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .keyword-badge {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        margin: 0.2rem;
        background: #e0e7ff;
        color: #4338ca;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'login_mode' not in st.session_state:
    st.session_state.login_mode = 'user'  # 'user' or 'admin'

# Helper functions
def login_user(token, user_id, username, role):
    st.session_state.token = token
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.role = role
    if role == 'admin':
        st.session_state.page = 'admin_dashboard'
    else:
        st.session_state.page = 'user_dashboard'

def logout_user():
    st.session_state.token = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.page = 'login'

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def admin_login(username, password):
    """Login as admin"""
    try:
        response = requests.post(f"{API_URL}/admin/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            login_user(data['token'], data['user_id'], data['username'], data['role'])
            return True, "Login successful"
        else:
            error_msg = response.json().get('detail', 'Invalid credentials')
            return False, error_msg
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def user_login(username, password):
    """Login as user"""
    try:
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            login_user(data['token'], data['user_id'], data['username'], data['role'])
            return True, "Login successful"
        else:
            error_msg = response.json().get('detail', 'Invalid credentials')
            return False, error_msg
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_dashboard_stats():
    """Fetch dashboard statistics for admin"""
    try:
        response = requests.get(f"{API_URL}/admin/dashboard-stats", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return None

def get_aspect_categories():
    """Fetch aspect categories"""
    try:
        response = requests.get(f"{API_URL}/admin/aspect-categories", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []

def get_system_logs():
    """Fetch system logs"""
    try:
        response = requests.get(f"{API_URL}/admin/system-logs", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching logs: {e}")
        return []

def get_user_stats():
    """Fetch user statistics"""
    try:
        response = requests.get(f"{API_URL}/user-stats", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return None

# LOGIN PAGE
if not st.session_state.token:
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Aspect-Based Sentiment Analyzer</h1>
        <p>Analyze customer reviews with AI-powered aspect extraction and sentiment analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle between Admin and User login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Select Login Type")
        
        # Toggle buttons
        toggle_col1, toggle_col2 = st.columns(2)
        
        with toggle_col1:
            if st.button("👨‍💼 Admin Login", use_container_width=True, key="admin_toggle"):
                st.session_state.login_mode = 'admin'
                st.rerun()
        
        with toggle_col2:
            if st.button("👤 User Login", use_container_width=True, key="user_toggle"):
                st.session_state.login_mode = 'user'
                st.rerun()
        
        st.markdown("---")
        
        # ADMIN LOGIN
        if st.session_state.login_mode == 'admin':
            st.markdown("### 👨‍💼 Admin Login")
            st.info("Login with your admin credentials to access the admin dashboard")
            
            with st.form("admin_login_form"):
                admin_username = st.text_input("Admin Username / Email / ID", placeholder="Enter admin details")
                admin_password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
                admin_submit = st.form_submit_button("Login as Admin", use_container_width=True)
                
                if admin_submit:
                    if admin_username and admin_password:
                        success, message = admin_login(admin_username, admin_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter both username and password")
            
        
        # USER LOGIN
        else:
            st.markdown("### 👤 User Login")
            st.info("Login with your user credentials to use the sentiment analysis model")
            
            with st.form("user_login_form"):
                user_username = st.text_input("Username / Email / ID", placeholder="Enter your details")
                user_password = st.text_input("Password", type="password", placeholder="Enter your password")
                user_submit = st.form_submit_button("Login as User", use_container_width=True)
                
                if user_submit:
                    if user_username and user_password:
                        success, message = user_login(user_username, user_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter both username and password")
            
            st.markdown("---")
            st.markdown("### 📝 Create New Account")
            st.info("Don't have an account? Create one below to get started!")
            
            with st.form("user_register_form"):
                reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
                reg_email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
                reg_fullname = st.text_input("Full Name", placeholder="Enter your full name", key="reg_fullname")
                reg_password = st.text_input("Password", type="password", placeholder="Create a password", key="reg_password")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
                reg_submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if reg_submit:
                    if not all([reg_username, reg_email, reg_fullname, reg_password, reg_confirm]):
                        st.warning("Please fill in all fields")
                    elif reg_password != reg_confirm:
                        st.error("Passwords don't match!")
                    elif len(reg_password) < 6:
                        st.warning("Password must be at least 6 characters long")
                    else:
                        try:
                            response = requests.post(f"{API_URL}/register", json={
                                "username": reg_username,
                                "email": reg_email,
                                "full_name": reg_fullname,
                                "password": reg_password
                            })
                            if response.status_code == 200:
                                data = response.json()
                                login_user(data['token'], data['user_id'], data['username'], data['role'])
                                st.success("Account created successfully! Logging you in...")
                                st.rerun()
                            else:
                                error_msg = response.json().get('detail', 'Registration failed')
                                st.error(f"Registration failed: {error_msg}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

# ADMIN DASHBOARD
elif st.session_state.role == 'admin':
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: #667eea; margin: 0;'>👨���💼 Admin Panel</h3>
            <p style='color: #6b7280; margin: 0.5rem 0 0 0;'><strong>{st.session_state.username}</strong></p>
            <p style='color: #9ca3af; font-size: 0.9rem; margin: 0;'>Role: Admin</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Navigation")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = 'admin_dashboard'
            st.rerun()
        
        if st.button("🎓 Active Learning Corrections", use_container_width=True):
            st.session_state.page = 'al_corrections'
            st.rerun()
        
        if st.button("📊 Overall Sentiment Analysis", use_container_width=True):
            st.session_state.page = 'sentiment_analysis'
            st.rerun()
        
        if st.button("🎯 Users Activity Logs", use_container_width=True):
            st.session_state.page = 'activity_logs'
            st.rerun()
        
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = 'admin_profile'
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    # ADMIN DASHBOARD PAGE
    if st.session_state.page == 'admin_dashboard':
        st.markdown("""
        <div class="main-header">
            <h1>📊 Admin Dashboard</h1>
            <p>System Overview and Statistics</p>
        </div>
        """, unsafe_allow_html=True)
        
        stats = get_dashboard_stats()
        
        if stats:
            # Display stats cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card info-card">
                    <h3>{stats.get('total_users', 0)}</h3>
                    <p>Total Users</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>{stats.get('total_reviews', 0)}</h3>
                    <p>Reviews Submitted</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stat-card positive-card">
                    <h3>{stats.get('registered_users', 0)}</h3>
                    <p>Registered Users</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-card neutral-card">
                    <h3>{stats.get('total_models', 0)}</h3>
                    <p>No of Models</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Aspect Category Ratio
            st.markdown("<div class='section-header'>Aspect Category Ratio</div>", unsafe_allow_html=True)
            
            aspect_ratio = stats.get('aspect_ratio', {})
            if aspect_ratio:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=list(aspect_ratio.keys()),
                        values=list(aspect_ratio.values()),
                        hole=0.4
                    )])
                    fig_pie.update_layout(title="Aspect Distribution", height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    fig_bar = go.Figure(data=[go.Bar(
                        x=list(aspect_ratio.keys()),
                        y=list(aspect_ratio.values()),
                        marker=dict(color='#667eea')
                    )])
                    fig_bar.update_layout(title="Aspect Count", height=400, xaxis_title="Aspect", yaxis_title="Count")
                    st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No aspect data available yet.")
        else:
            st.error("Failed to load dashboard statistics. Please ensure the backend is running.")
    
    # ACTIVE LEARNING CORRECTIONS PAGE
    elif st.session_state.page == 'al_corrections':
        st.markdown("""
        <div class="main-header">
            <h1>🎓 Active Learning Corrections</h1>
            <p>Monitor all user corrections and model improvements</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get correction statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_corrections,
                    COUNT(DISTINCT user_id) as users_corrected,
                    SUM(CASE WHEN used_for_training = 1 THEN 1 ELSE 0 END) as used_for_training,
                    COUNT(DISTINCT aspect_id) as aspects_corrected
                FROM active_learning_corrections
            ''')
            
            corr_stats = cursor.fetchone()
            
            # Display stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card info-card">
                    <h3>{corr_stats['total_corrections'] or 0}</h3>
                    <p>Total Corrections</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-card positive-card">
                    <h3>{corr_stats['users_corrected'] or 0}</h3>
                    <p>Users Contributing</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stat-card neutral-card">
                    <h3>{corr_stats['used_for_training'] or 0}</h3>
                    <p>Used for Training</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-card negative-card">
                    <h3>{corr_stats['aspects_corrected'] or 0}</h3>
                    <p>Aspects Corrected</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Get detailed corrections
            cursor.execute('''
                SELECT 
                    alc.id,
                    u.username,
                    alc.original_sentiment,
                    alc.corrected_sentiment,
                    alc.confidence,
                    alc.review_text,
                    alc.corrected_at,
                    alc.used_for_training,
                    a.aspect
                FROM active_learning_corrections alc
                JOIN users u ON alc.user_id = u.id
                LEFT JOIN aspects a ON alc.aspect_id = a.id
                ORDER BY alc.corrected_at DESC
                LIMIT 100
            ''')
            
            corrections = cursor.fetchall()
            
            if corrections:
                st.markdown("<div class='section-header'>Recent Corrections (Latest 100)</div>", unsafe_allow_html=True)
                
                corr_df = pd.DataFrame(corrections)
                corr_df.columns = ['ID', 'Username', 'Original', 'Corrected', 'Confidence', 'Review Text', 'Time', 'Used', 'Aspect']
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    filter_user = st.selectbox("Filter by User", ['All'] + list(corr_df['Username'].unique()))
                with col2:
                    filter_status = st.selectbox("Filter by Training Status", ['All', 'Used for Training', 'Pending'])
                
                # Apply filters
                filtered_df = corr_df.copy()
                if filter_user != 'All':
                    filtered_df = filtered_df[filtered_df['Username'] == filter_user]
                if filter_status == 'Used for Training':
                    filtered_df = filtered_df[filtered_df['Used'] == 1]
                elif filter_status == 'Pending':
                    filtered_df = filtered_df[filtered_df['Used'] == 0]
                
                # Show corrections in expandable format
                for idx, row in filtered_df.iterrows():
                    status_badge = "✅ Used" if row['Used'] else "⏳ Pending"
                    with st.expander(f"User: {row['Username']} | {row['Original']} → {row['Corrected']} | {status_badge}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**Review:** {row['Review Text'][:100]}...")
                            st.write(f"**Aspect:** {row['Aspect'] or 'N/A'}")
                            st.write(f"**Confidence:** {row['Confidence']:.1%}")
                            st.write(f"**Timestamp:** {row['Time']}")
                        with col2:
                            st.metric("Correction ID", row['ID'])
                
                # Download option
                csv = corr_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Corrections Data",
                    data=csv,
                    file_name="active_learning_corrections.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No corrections recorded yet.")
            
            conn.close()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # OVERALL SENTIMENT ANALYSIS PAGE
    elif st.session_state.page == 'sentiment_analysis':
        st.markdown("""
        <div class="main-header">
            <h1>📊 Overall Sentiment Analysis</h1>
            <p>System-wide sentiment distribution and insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Overall sentiment statistics
            cursor.execute('''
                SELECT 
                    sentiment,
                    COUNT(*) as count
                FROM aspects
                GROUP BY sentiment
            ''')
            
            sentiment_data = cursor.fetchall()
            
            if sentiment_data:
                sentiment_dict = {row['sentiment']: row['count'] for row in sentiment_data}
                
                # Stats cards
                col1, col2, col3 = st.columns(3)
                
                total = sum(sentiment_dict.values())
                positive = sentiment_dict.get('positive', 0)
                negative = sentiment_dict.get('negative', 0)
                neutral = sentiment_dict.get('neutral', 0)
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card positive-card">
                        <h3>{positive}</h3>
                        <p>Positive ({positive/total*100:.1f}%)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-card negative-card">
                        <h3>{negative}</h3>
                        <p>Negative ({negative/total*100:.1f}%)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="stat-card neutral-card">
                        <h3>{neutral}</h3>
                        <p>Neutral ({neutral/total*100:.1f}%)</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pie chart
                    fig_pie = px.pie(
                        values=list(sentiment_dict.values()),
                        names=list(sentiment_dict.keys()),
                        title="Sentiment Distribution (All Aspects)",
                        color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'}
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Bar chart
                    fig_bar = px.bar(
                        x=list(sentiment_dict.keys()),
                        y=list(sentiment_dict.values()),
                        title="Sentiment Count",
                        color=list(sentiment_dict.keys()),
                        color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'},
                        labels={'x': 'Sentiment', 'y': 'Count'}
                    )
                    fig_bar.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                st.markdown("---")
                
                # Sentiment trend by aspect
                st.markdown("<div class='section-header'>Sentiment Analysis by Aspect</div>", unsafe_allow_html=True)
                
                cursor.execute('''
                    SELECT 
                        aspect,
                        sentiment,
                        COUNT(*) as count
                    FROM aspects
                    WHERE aspect IS NOT NULL
                    GROUP BY aspect, sentiment
                    ORDER BY aspect, sentiment
                ''')
                
                aspect_sentiment = cursor.fetchall()
                
                if aspect_sentiment and len(aspect_sentiment) > 0:
                    try:
                        # Convert to DataFrame with proper column names
                        aspect_df = pd.DataFrame([dict(row) for row in aspect_sentiment])
                        
                        if 'aspect' in aspect_df.columns and 'sentiment' in aspect_df.columns and 'count' in aspect_df.columns:
                            # Create grouped bar chart
                            fig_grouped = px.bar(
                                aspect_df,
                                x='aspect',
                                y='count',
                                color='sentiment',
                                title="Aspect-Sentiment Distribution (Grouped)",
                                color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'},
                                labels={'aspect': 'Aspect', 'count': 'Count', 'sentiment': 'Sentiment'},
                                barmode='group'
                            )
                            fig_grouped.update_layout(height=400, xaxis_tickangle=-45)
                            st.plotly_chart(fig_grouped, use_container_width=True)
                            
                            # Create stacked bar chart
                            fig_stacked = px.bar(
                                aspect_df,
                                x='aspect',
                                y='count',
                                color='sentiment',
                                title="Aspect-Sentiment Distribution (Stacked)",
                                color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'},
                                labels={'aspect': 'Aspect', 'count': 'Count', 'sentiment': 'Sentiment'},
                                barmode='stack'
                            )
                            fig_stacked.update_layout(height=400, xaxis_tickangle=-45)
                            st.plotly_chart(fig_stacked, use_container_width=True)
                            
                            # Pivot table for detailed view
                            pivot_table = aspect_df.pivot_table(index='aspect', columns='sentiment', values='count', fill_value=0)
                            
                            st.markdown("**Aspect-Sentiment Matrix (Detailed View)**")
                            st.dataframe(pivot_table, use_container_width=True)
                            
                            # Add percentage breakdown
                            st.markdown("**Sentiment Percentage by Aspect**")
                            percentage_table = pivot_table.div(pivot_table.sum(axis=1), axis=0) * 100
                            percentage_table = percentage_table.round(2)
                            st.dataframe(percentage_table, use_container_width=True)
                        else:
                            st.warning("No aspect data available for visualization")
                    except Exception as e:
                        st.error(f"Error creating visualization: {str(e)}")
            
            conn.close()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # USERS ACTIVITY LOGS PAGE
    elif st.session_state.page == 'activity_logs':
        st.markdown("""
        <div class="main-header">
            <h1>🎯 Users Activity Logs</h1>
            <p>Track all user reviews and their sentiments</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get all reviews with aspects
            cursor.execute('''
                SELECT 
                    r.id as review_id,
                    u.id as user_id,
                    u.username,
                    r.review_text,
                    r.product_name,
                    r.created_at,
                    a.sentiment,
                    a.confidence,
                    a.aspect
                FROM reviews r
                JOIN users u ON r.user_id = u.id
                LEFT JOIN aspects a ON r.id = a.review_id
                ORDER BY r.created_at DESC
                LIMIT 500
            ''')
            
            activity_data = cursor.fetchall()
            
            if activity_data:
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                
                total_reviews = len(set([row['review_id'] for row in activity_data]))
                total_users = len(set([row['user_id'] for row in activity_data]))
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card info-card">
                        <h3>{total_reviews}</h3>
                        <p>Total Reviews</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-card positive-card">
                        <h3>{total_users}</h3>
                        <p>Active Users</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                positive_count = len([row for row in activity_data if row['sentiment'] == 'positive'])
                negative_count = len([row for row in activity_data if row['sentiment'] == 'negative'])
                
                with col3:
                    st.markdown(f"""
                    <div class="stat-card positive-card">
                        <h3>{positive_count}</h3>
                        <p>Positive Sentiments</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="stat-card negative-card">
                        <h3>{negative_count}</h3>
                        <p>Negative Sentiments</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Filter options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    selected_user = st.selectbox("Filter by User", ['All'] + list(set([row['username'] for row in activity_data])))
                
                with col2:
                    selected_sentiment = st.selectbox("Filter by Sentiment", ['All', 'positive', 'negative', 'neutral'])
                
                with col3:
                    search_text = st.text_input("Search in review text")
                
                # Apply filters
                filtered_activity = activity_data
                
                if selected_user != 'All':
                    filtered_activity = [row for row in filtered_activity if row['username'] == selected_user]
                
                if selected_sentiment != 'All':
                    filtered_activity = [row for row in filtered_activity if row['sentiment'] == selected_sentiment]
                
                if search_text:
                    filtered_activity = [row for row in filtered_activity if search_text.lower() in row['review_text'].lower()]
                
                st.markdown("---")
                
                # Display activity logs
                st.markdown(f"<div class='section-header'>Activity Records ({len(filtered_activity)})</div>", unsafe_allow_html=True)
                
                for idx, row in enumerate(filtered_activity):
                    sentiment_color = {'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'}.get(row['sentiment'] or 'unknown', '#6b7280')
                    
                    col_main, col_delete = st.columns([0.95, 0.05])
                    
                    with col_main:
                        st.markdown(f"""
                        <div style='background: #1a1a2e; border: 1px solid #16213e; padding: 1rem; border-radius: 8px; margin: 0.8rem 0; border-left: 4px solid {sentiment_color};'>
                            <div style='display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 1rem; margin-bottom: 0.5rem;'>
                                <div><strong style='color: #64b5f6;'>User ID:</strong> <span style='color: #e0e0e0;'>{row['user_id']}</span></div>
                                <div><strong style='color: #64b5f6;'>Username:</strong> <span style='color: #e0e0e0;'>{row['username']}</span></div>
                                <div><strong style='color: #64b5f6;'>Product:</strong> <span style='color: #e0e0e0;'>{row['product_name'] or 'N/A'}</span></div>
                                <div><strong style='color: #64b5f6;'>Timestamp:</strong> <span style='color: #e0e0e0;'>{row['created_at']}</span></div>
                            </div>
                            <div style='margin: 0.5rem 0;'>
                                <strong style='color: #64b5f6;'>Review:</strong> <span style='color: #b0bec5;'>{row['review_text'][:150]}...</span>
                            </div>
                            <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;'>
                                <div><strong style='color: #64b5f6;'>Aspect:</strong> <span style='color: #e0e0e0;'>{row['aspect'] or 'N/A'}</span></div>
                                <div><strong style='color: #64b5f6;'>Sentiment:</strong> <span style='color: {sentiment_color}; font-weight: bold;'>{(row['sentiment'] or 'unknown').upper()}</span></div>
                                <div><strong style='color: #64b5f6;'>Confidence:</strong> <span style='color: #e0e0e0;'>{row['confidence']:.1%}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_delete:
                        if st.button("🗑️", key=f"delete_user_{idx}_{row['user_id']}", help="Delete this user"):
                            try:
                                conn_delete = get_db()
                                cursor_delete = conn_delete.cursor()
                                
                                # Delete user's active learning corrections
                                cursor_delete.execute('DELETE FROM active_learning_corrections WHERE user_id = ?', (row['user_id'],))
                                
                                # Delete user's reviews and aspects
                                cursor_delete.execute('''
                                    DELETE FROM aspects WHERE review_id IN 
                                    (SELECT id FROM reviews WHERE user_id = ?)
                                ''', (row['user_id'],))
                                cursor_delete.execute('DELETE FROM reviews WHERE user_id = ?', (row['user_id'],))
                                
                                # Delete the user
                                cursor_delete.execute('DELETE FROM users WHERE id = ?', (row['user_id'],))
                                
                                conn_delete.commit()
                                conn_delete.close()
                                
                                st.success(f"✅ User '{row['username']}' and all their data has been deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting user: {str(e)}")
                
                # Download option
                activity_df = pd.DataFrame(filtered_activity)
                csv = activity_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Activity Logs",
                    data=csv,
                    file_name="users_activity_logs.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No activity records found.")
            
            conn.close()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # ADMIN PROFILE PAGE
    elif st.session_state.page == 'admin_profile':
        st.markdown("""
        <div class="main-header">
            <h1>👤 Admin Profile</h1>
            <p>Manage your admin account settings</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile Information Section
        st.markdown("<div class='section-header'>Profile Information</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                <h4 style='color: #667eea; margin: 0 0 1rem 0;'>Account Details</h4>
                <p style='margin: 0.5rem 0;'><strong>Username:</strong> {st.session_state.username}</p>
                <p style='margin: 0.5rem 0;'><strong>User ID:</strong> {st.session_state.user_id}</p>
                <p style='margin: 0.5rem 0;'><strong>Role:</strong> Administrator</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Get admin stats
            stats = get_dashboard_stats()
            if stats:
                st.markdown(f"""
                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #667eea; margin: 0 0 1rem 0;'>System Overview</h4>
                    <p style='margin: 0.5rem 0;'><strong>Total Users:</strong> {stats.get('total_users', 0)}</p>
                    <p style='margin: 0.5rem 0;'><strong>Total Reviews:</strong> {stats.get('total_reviews', 0)}</p>
                    <p style='margin: 0.5rem 0;'><strong>Total Models:</strong> {stats.get('total_models', 0)}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Change Password Section
        st.markdown("<div class='section-header'>Change Password</div>", unsafe_allow_html=True)
        
        with st.form("admin_change_password_form"):
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
            """, unsafe_allow_html=True)
            
            current_password = st.text_input("Current Password", type="password", 
                                            placeholder="Enter your current password")
            new_password = st.text_input("New Password", type="password", 
                                        placeholder="Enter new password (min 6 characters)")
            confirm_password = st.text_input("Confirm New Password", type="password", 
                                            placeholder="Re-enter new password")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submit = st.form_submit_button("Change Password", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if cancel:
                st.rerun()
            
            if submit:
                # Validation
                if not current_password or not new_password or not confirm_password:
                    st.error("All fields are required!")
                elif len(new_password) < 6:
                    st.error("New password must be at least 6 characters long!")
                elif new_password != confirm_password:
                    st.error("New passwords do not match!")
                elif current_password == new_password:
                    st.warning("New password must be different from current password!")
                else:
                    # Call API to change password
                    try:
                        response = requests.post(
                            f"{API_URL}/change-password",
                            headers=get_headers(),
                            json={
                                "current_password": current_password,
                                "new_password": new_password
                            }
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Password changed successfully!")
                            st.balloons()
                        elif response.status_code == 401:
                            st.error("❌ Current password is incorrect!")
                        else:
                            error_msg = response.json().get('detail', 'Failed to change password')
                            st.error(f"❌ {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

# USER DASHBOARD
elif st.session_state.role == 'user':
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: #667eea; margin: 0;'>👤 User Panel</h3>
            <p style='color: #6b7280; margin: 0.5rem 0 0 0;'><strong>{st.session_state.username}</strong></p>
            <p style='color: #9ca3af; font-size: 0.9rem; margin: 0;'>Role: User</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Navigation")
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = 'user_dashboard'
            st.rerun()
        
        if st.button("📝 Submit Review", use_container_width=True):
            st.session_state.page = 'submit_review'
            st.rerun()
        
        if st.button("📊 Batch Analysis", use_container_width=True):
            st.session_state.page = 'batch_analysis'
            st.rerun()
        
        if st.button("🎓 Active Learning", use_container_width=True):
            st.session_state.page = 'active_learning'
            st.rerun()
        
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = 'profile'
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    # USER DASHBOARD PAGE
    if st.session_state.page == 'user_dashboard':
        st.markdown("""
        <div class="main-header">
            <h1>📊 Your Dashboard</h1>
            <p>Your sentiment analysis statistics</p>
        </div>
        """, unsafe_allow_html=True)
        
        stats = get_user_stats()
        
        if stats:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card info-card">
                    <h3>{stats.get('total_reviews', 0)}</h3>
                    <p>Total Reviews</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <h3>{stats.get('total_aspects', 0)}</h3>
                    <p>Total Aspects</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stat-card positive-card">
                    <h3>{stats.get('positive_aspects', 0)}</h3>
                    <p>Positive</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stat-card negative-card">
                    <h3>{stats.get('negative_aspects', 0)}</h3>
                    <p>Negative</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                <div class="stat-card neutral-card">
                    <h3>{stats.get('neutral_aspects', 0)}</h3>
                    <p>Neutral</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Visualization
            if stats['total_aspects'] > 0:
                st.markdown("<div class='section-header'>Sentiment Distribution</div>", unsafe_allow_html=True)
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Positive', 'Negative', 'Neutral'],
                    values=[stats['positive_aspects'], stats['negative_aspects'], stats['neutral_aspects']],
                    marker=dict(colors=['#10b981', '#ef4444', '#f59e0b']),
                    hole=0.4
                )])
                fig_pie.update_layout(title="Your Sentiment Breakdown", height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data available yet. Submit your first review!")
        
        # Your Submitted Reviews Section
        st.markdown("---")
        st.markdown("<div class='section-header'>📋 Your Submitted Reviews</div>", unsafe_allow_html=True)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get user's reviews directly from database
            cursor.execute('''
                SELECT 
                    r.id,
                    r.review_text,
                    r.product_name,
                    r.created_at
                FROM reviews r
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (st.session_state.user_id,))
            
            user_reviews = cursor.fetchall()
            
            if user_reviews and len(user_reviews) > 0:
                # Create tabs for different views
                view_tab1, view_tab2 = st.tabs(["📝 List View", "📊 Analysis View"])
                
                with view_tab1:
                    st.markdown("### All Your Reviews")
                    
                    for idx, review in enumerate(user_reviews, 1):
                        # Get aspects for this review
                        cursor.execute('''
                            SELECT aspect, sentiment, confidence
                            FROM aspects
                            WHERE review_id = ?
                        ''', (review['id'],))
                        
                        aspects = cursor.fetchall()
                        
                        with st.expander(f"📄 Review {idx}: {review['review_text'][:60]}...", expanded=False):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Review Text:**\n{review['review_text']}")
                                st.markdown(f"**Product:** {review['product_name']}")
                                st.markdown(f"**Date:** {review['created_at']}")
                            
                            with col2:
                                st.metric("Aspects Found", len(aspects))
                            
                            # Show aspects
                            if aspects and len(aspects) > 0:
                                st.markdown("**Detected Aspects:**")
                                for aspect in aspects:
                                    sentiment = aspect['sentiment'].lower() if aspect['sentiment'] else 'unknown'
                                    color_map = {
                                        'positive': '#10b981',
                                        'negative': '#ef4444',
                                        'neutral': '#f59e0b'
                                    }
                                    color = color_map.get(sentiment, '#6b7280')
                                    
                                    st.markdown(f"""
                                    <div style='background: #f3f4f6; padding: 0.8rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid {color};'>
                                        <strong>{aspect['aspect'] or 'Unknown'}</strong> → 
                                        <span style='color: {color}; font-weight: bold;'>{sentiment.upper()}</span>
                                        <span style='color: #6b7280; margin-left: 1rem;'>Confidence: {aspect['confidence']:.1%}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No aspects detected for this review")
                
                with view_tab2:
                    st.markdown("### Your Sentiment Analysis")
                    
                    # Get all aspects for all user reviews
                    cursor.execute('''
                        SELECT a.aspect, a.sentiment, a.confidence
                        FROM aspects a
                        JOIN reviews r ON a.review_id = r.id
                        WHERE r.user_id = ?
                    ''', (st.session_state.user_id,))
                    
                    all_aspects_data = cursor.fetchall()
                    
                    if all_aspects_data and len(all_aspects_data) > 0:
                        # Convert to DataFrame
                        aspects_df = pd.DataFrame([dict(row) for row in all_aspects_data])
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="stat-card info-card">
                                <h3>{len(user_reviews)}</h3>
                                <p>Total Reviews</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="stat-card positive-card">
                                <h3>{len(all_aspects_data)}</h3>
                                <p>Total Aspects</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            avg_conf = aspects_df['confidence'].mean() if 'confidence' in aspects_df.columns else 0
                            st.markdown(f"""
                            <div class="stat-card neutral-card">
                                <h3>{avg_conf:.1%}</h3>
                                <p>Avg Confidence</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Sentiment distribution
                        if 'sentiment' in aspects_df.columns:
                            sentiment_counts = aspects_df['sentiment'].value_counts()
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Pie Chart
                                fig_pie = px.pie(
                                    values=sentiment_counts.values,
                                    names=sentiment_counts.index,
                                    title="Your Sentiment Distribution (Pie)",
                                    color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'}
                                )
                                fig_pie.update_layout(height=400)
                                st.plotly_chart(fig_pie, use_container_width=True)
                            
                            with col2:
                                # Bar Chart
                                fig_bar = px.bar(
                                    x=sentiment_counts.index,
                                    y=sentiment_counts.values,
                                    color=sentiment_counts.index,
                                    color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'},
                                    labels={'x': 'Sentiment', 'y': 'Count'},
                                    title="Your Sentiment Distribution (Bar)"
                                )
                                fig_bar.update_layout(height=400, showlegend=False)
                                st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.info("No aspect data available yet")
                
                conn.close()
            else:
                st.info("No reviews submitted yet. Go to 'Submit Review' to add your first review!")
                conn.close()
        
        except Exception as e:
            st.error(f"Error fetching reviews: {str(e)}")
        
        # FEEDBACK SECTION
        st.markdown("---")
        st.markdown("""
        <div class="main-header">
            <h1>💬 Model Feedback</h1>
            <p>Help us improve by sharing your feedback on the model</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get existing feedback from this user
            cursor.execute('''
                SELECT rating, feedback_text, feedback_type, created_at
                FROM user_feedback
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (st.session_state.user_id,))
            
            user_feedbacks = cursor.fetchall()
            
            # Feedback submission form
            st.markdown("<div class='section-header'>📝 Submit Your Feedback</div>", unsafe_allow_html=True)
            
            with st.form("feedback_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    rating = st.slider("How would you rate the model?", 1, 5, 4, 
                                      help="1 = Poor, 5 = Excellent")
                    st.markdown(f"<p style='text-align: center; color: #64b5f6; font-weight: bold;'>{rating}/5 ⭐</p>", 
                               unsafe_allow_html=True)
                
                with col2:
                    feedback_type = st.selectbox("Feedback Type", 
                                                ["General", "Accuracy", "Performance", "Feature Request", "Bug Report", "Other"])
                
                feedback_text = st.text_area("Your Feedback", 
                                           placeholder="Tell us what you think about the model...",
                                           height=150)
                
                col_submit, col_clear = st.columns(2)
                
                with col_submit:
                    submit_feedback = st.form_submit_button("📤 Submit Feedback", use_container_width=True)
                
                with col_clear:
                    if st.form_submit_button("Clear", use_container_width=True):
                        st.rerun()
                
                if submit_feedback:
                    try:
                        # Get current local time
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        cursor.execute('''
                            INSERT INTO user_feedback (user_id, rating, feedback_text, feedback_type, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (st.session_state.user_id, rating, feedback_text if feedback_text.strip() else None, feedback_type, current_time))
                        
                        conn.commit()
                        st.success("✅ Thank you! Your feedback has been saved successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving feedback: {str(e)}")
            
            # Display previous feedback
            if user_feedbacks and len(user_feedbacks) > 0:
                st.markdown("---")
                st.markdown("<div class='section-header'>📋 Your Previous Feedback</div>", unsafe_allow_html=True)
                
                for idx, feedback in enumerate(user_feedbacks, 1):
                    rating_stars = "⭐" * feedback['rating'] + "☆" * (5 - feedback['rating'])
                    feedback_type_colors = {
                        "General": "#64b5f6",
                        "Accuracy": "#10b981",
                        "Performance": "#f59e0b",
                        "Feature Request": "#a855f7",
                        "Bug Report": "#ef4444",
                        "Other": "#6b7280"
                    }
                    
                    color = feedback_type_colors.get(feedback['feedback_type'], "#6b7280")
                    
                    st.markdown(f"""
                    <div style='background: #1a1a2e; border: 1px solid #16213e; padding: 1rem; border-radius: 8px; margin: 0.8rem 0; border-left: 4px solid {color};'>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 0.5rem;'>
                            <div><strong style='color: #f59e0b;'>{rating_stars}</strong></div>
                            <div><strong style='color: {color};'>{feedback['feedback_type']}</strong></div>
                        </div>
                        <div style='margin: 0.5rem 0;'>
                            <p style='color: #b0bec5;'>{feedback['feedback_text'] or 'No additional comments'}</p>
                        </div>
                        <div style='text-align: right;'>
                            <span style='color: #6b7280; font-size: 0.9rem;'>{feedback['created_at']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error loading feedback: {str(e)}")
    
    # SUBMIT REVIEW PAGE
    elif st.session_state.page == 'submit_review':
        st.markdown("""
        <div class="main-header">
            <h1>📝 Submit a Review</h1>
            <p>Enter your review and get instant aspect-based sentiment analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("review_form"):
            review_text = st.text_area("Your Review", height=200, 
                                      placeholder="Write your detailed review here...")
            submit = st.form_submit_button("Analyze Review", use_container_width=True)
            
            if submit and review_text.strip():
                with st.spinner("Analyzing..."):
                    try:
                        response = requests.post(f"{API_URL}/submit-review", 
                                               headers=get_headers(),
                                               json={"review_text": review_text})
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data['results']
                            
                            st.success("Analysis complete!")
                            
                            st.markdown("<div class='section-header'>Detected Aspects & Sentiments</div>", 
                                      unsafe_allow_html=True)
                            
                            for result in results:
                                sentiment_class = result['sentiment'].lower()
                                keywords_html = ' '.join([f'<span class="keyword-badge">{kw}</span>' 
                                                         for kw in result.get('keywords', [])])
                                
                                st.markdown(f"""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                                    <h4 style='color: #1f2937; margin: 0 0 0.5rem 0;'>{result['aspect']}</h4>
                                    <span class='sentiment-badge {sentiment_class}'>{result['sentiment'].upper()}</span>
                                    <span style='margin-left: 1rem; color: #6b7280;'>Confidence: {result['confidence']:.1%}</span>
                                    <div style='margin-top: 1rem;'>
                                        <strong style='color: #6b7280;'>Keywords:</strong><br>
                                        {keywords_html if keywords_html else '<span style="color: #9ca3af;">No keywords</span>'}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Visualization
                            st.markdown("<div class='section-header'>Sentiment Visualization</div>", 
                                      unsafe_allow_html=True)
                            
                            df = pd.DataFrame(results)
                            sentiment_counts = df['sentiment'].value_counts()
                            
                            fig = px.bar(x=sentiment_counts.index, y=sentiment_counts.values,
                                       color=sentiment_counts.index,
                                       color_discrete_map={'positive': '#10b981', 'negative': '#ef4444', 'neutral': '#f59e0b'},
                                       labels={'x': 'Sentiment', 'y': 'Count'},
                                       title="Sentiment Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    # MY REVIEWS PAGE
    elif st.session_state.page == 'my_reviews':
        st.markdown("""
        <div class="main-header">
            <h1>📋 My Reviews</h1>
            <p>View all your submitted reviews</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            response = requests.get(f"{API_URL}/user-reviews", headers=get_headers())
            if response.status_code == 200:
                data = response.json()
                reviews = data['reviews']
                
                if reviews:
                    for review in reviews:
                        with st.expander(f"📅 {review['created_at'][:10]} - {len(review['aspects'])} aspects"):
                            st.markdown(f"**Review:** {review['review_text']}")
                            st.markdown("---")
                            
                            for aspect in review['aspects']:
                                sentiment_class = aspect['sentiment'].lower()
                                keywords_html = ' '.join([f'<span class="keyword-badge">{kw}</span>' 
                                                         for kw in aspect.get('keywords', [])])
                                
                                st.markdown(f"""
                                <div style='background: #f9fafb; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                                    <strong>{aspect['aspect']}</strong><br>
                                    <span class='sentiment-badge {sentiment_class}'>{aspect['sentiment'].upper()}</span>
                                    <span style='margin-left: 1rem;'>Confidence: {aspect['confidence']:.1%}</span><br>
                                    <div style='margin-top: 0.5rem;'>{keywords_html}</div>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("No reviews yet. Submit your first review!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # ACTIVE LEARNING PAGE
    elif st.session_state.page == 'active_learning':
        st.markdown("""
        <div class="main-header">
            <h1>🎓 Active Learning</h1>
            <p>Improve model accuracy by correcting uncertain predictions</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Introduction
        with st.expander("📖 What is Active Learning?", expanded=True):
            st.markdown("""
            **Active Learning** helps improve sentiment analysis by:
            1. **Identifying Uncertain Predictions**: Shows reviews where the model has low confidence (<50%)
            2. **Manual Correction**: You can correct the model's sentiment prediction
            3. **Model Retraining**: The corrected data is used to fine-tune the model
            4. **Continuous Improvement**: Over time, the model becomes more accurate
            
            ### How to use:
            - View uncertain samples below
            - Change the sentiment if you disagree with the prediction
            - Click "Save & Retrain" to update the model
            - Download corrections as CSV to track your feedback
            - Upload corrected data to evaluate model improvements
            """)
        
        st.markdown("---")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Uncertain Samples", "📥 Upload Train Set", "📥 Download Corrections", "📊 Model Stats", "⚙️ Retrain Model"])
        
        with tab1:
            st.markdown("### Review Predictions with Low Confidence (<50%)")
            
            try:
                response = requests.get(f"{API_URL}/uncertain-samples", headers=get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    samples = data.get('uncertain_samples', [])
                    
                    if samples:
                        # Initialize session state for corrections if needed
                        if 'corrections' not in st.session_state:
                            st.session_state.corrections = {}
                        
                        for idx, sample in enumerate(samples):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.markdown(f"""
                                <div style='background: #e0f2fe; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #0284c7;'>
                                    <strong style='color: #0c4a6e;'>Review ID:</strong> <span style='color: #0369a1;'>{sample['review_id']}</span><br>
                                    <strong style='color: #0c4a6e;'>Text:</strong> <span style='color: #0369a1;'>{sample['review_text'][:150]}...</span><br>
                                    <strong style='color: #0c4a6e;'>Aspect:</strong> <span style='color: #0369a1;'>{sample['aspect']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f"""
                                <div style='background: #e0f2fe; padding: 1rem; border-radius: 8px; text-align: center; border-left: 4px solid #0284c7;'>
                                    <strong style='color: #0c4a6e;'>Current Prediction</strong><br>
                                    <span style='font-size: 1.2rem; color: #0369a1; font-weight: bold;'>{sample['predicted_sentiment'].upper()}</span><br>
                                    <small style='color: #0c4a6e;'>Confidence: <span style='color: #0284c7; font-weight: bold;'>{sample['confidence']:.1%}</span></small>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col3:
                                st.markdown(f"<strong>Correct Sentiment:</strong>", unsafe_allow_html=True)
                                corrected = st.selectbox(
                                    "Select correct sentiment",
                                    ["positive", "negative", "neutral"],
                                    key=f"correction_{idx}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.corrections[str(sample['review_id'])] = {
                                    'aspect': sample['aspect'],
                                    'corrected_sentiment': corrected
                                }
                            
                            st.markdown("---")
                        
                        # Save & Retrain Button
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 Save & Retrain Model", use_container_width=True, key="save_retrain"):
                                if st.session_state.corrections:
                                    with st.spinner("Saving corrections and retraining model..."):
                                        try:
                                            response = requests.post(
                                                f"{API_URL}/save-corrections",
                                                headers=get_headers(),
                                                json={"corrections": st.session_state.corrections}
                                            )
                                            
                                            if response.status_code == 200:
                                                st.success("✅ Corrections saved and model retraining started!")
                                                st.session_state.corrections = {}
                                            else:
                                                st.error(f"Error: {response.json().get('detail')}")
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                else:
                                    st.warning("No corrections made yet.")
                        
                        with col2:
                            if st.button("📥 Download Corrections", use_container_width=True, key="download_corr"):
                                st.info("See the 'Download Corrections' tab below.")
                    else:
                        st.success("✅ Great! No uncertain samples found. Your model is confident!")
                else:
                    st.error("Failed to fetch uncertain samples.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with tab2:
            st.markdown("### Upload Corrected Train Set")
            st.info("Upload a CSV or Excel file with corrected reviews to retrain the model.")
            
            uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.markdown("### Preview Uploaded Data")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    if st.button("🚀 Analyze & Predict", use_container_width=True):
                        with st.spinner("Analyzing uploaded reviews..."):
                            try:
                                # Convert dataframe to list of dicts
                                records = df.to_dict('records')
                                
                                response = requests.post(
                                    f"{API_URL}/predict-batch",
                                    headers=get_headers(),
                                    json={"reviews": records}
                                )
                                
                                if response.status_code == 200:
                                    results = response.json().get('predictions', [])
                                    
                                    st.markdown("### Prediction Results")
                                    results_df = pd.DataFrame(results)
                                    st.dataframe(results_df, use_container_width=True)
                                    
                                    # Download results
                                    csv = results_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Predictions as CSV",
                                        data=csv,
                                        file_name="predictions.csv",
                                        mime="text/csv",
                                        use_container_width=True
                                    )
                                else:
                                    st.error(f"Error: {response.json().get('detail')}")
                            except Exception as e:
                                st.error(f"Error: {e}")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        
        with tab3:
            st.markdown("### Download Your Corrections")
            
            try:
                response = requests.get(f"{API_URL}/get-corrections", headers=get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    corrections = data.get('corrections', [])
                    
                    if corrections:
                        df_corrections = pd.DataFrame(corrections)
                        
                        st.markdown("### Your Corrections History")
                        st.dataframe(df_corrections, use_container_width=True)
                        
                        # Download as CSV
                        csv = df_corrections.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Corrections (CSV)",
                            data=csv,
                            file_name="sentiment_corrections.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                        # Download as Excel
                        try:
                            import openpyxl
                            from io import BytesIO
                            
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df_corrections.to_excel(writer, index=False)
                            excel_data = output.getvalue()
                            
                            st.download_button(
                                label="📥 Download Corrections (Excel)",
                                data=excel_data,
                                file_name="sentiment_corrections.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        except ImportError:
                            st.info("Excel export requires: `pip install openpyxl`")
                    else:
                        st.info("No corrections recorded yet.")
                else:
                    st.error("Failed to fetch corrections.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with tab4:
            st.markdown("### Model Performance Statistics")
            
            try:
                response = requests.get(f"{API_URL}/model-stats", headers=get_headers())
                
                if response.status_code == 200:
                    stats = response.json()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stat-card info-card">
                            <h3>{stats.get('total_uncertain', 0)}</h3>
                            <p>Uncertain Samples</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stat-card positive-card">
                            <h3>{stats.get('total_corrections', 0)}</h3>
                            <p>Corrections Made</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stat-card neutral-card">
                            <h3>{stats.get('avg_confidence', 0):.1%}</h3>
                            <p>Avg Confidence</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="stat-card negative-card">
                            <h3>{stats.get('model_version', 'v1')}</h3>
                            <p>Model Version</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Failed to fetch model stats.")
            except Exception as e:
                st.error(f"Error: {e}")

        with tab5:
            st.markdown("### ⚙️ Manual Model Retraining")
            st.info("Force the model to retrain using all available corrections in the database.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("""
                Click the button below to trigger the retraining process manually. 
                This will use theTF-IDF + Logistic Regression pipeline to update our sentiment predictions 
                based on your manual feedback.
                """)
            
            with col2:
                if st.button("🚀 Force Retrain Now", use_container_width=True, type="primary"):
                    with st.spinner("Retraining in progress..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/active-learning/retrain",
                                headers=get_headers()
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get('status') == 'success':
                                    st.success(f"✅ {data.get('message')}")
                                    st.balloons()
                                else:
                                    st.warning(f"⚠️ {data.get('message')}")
                            else:
                                st.error(f"❌ Retraining failed: {response.json().get('detail')}")
                        except Exception as e:
                            st.error(f"❌ Retraining error: {e}")
            
            st.markdown("---")
            st.markdown("#### Retraining History")
            # We could fetch this from the models table if exposed
            st.write("The system automatically retrains after every 3 new corrections, but you can always force an update here.")
    
    # PROFILE PAGE
    elif st.session_state.page == 'profile':
        st.markdown("""
        <div class="main-header">
            <h1>👤 Profile Management</h1>
            <p>Manage your account settings and change your password</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile Information Section
        st.markdown("<div class='section-header'>Profile Information</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                <h4 style='color: #667eea; margin: 0 0 1rem 0;'>Account Details</h4>
                <p style='margin: 0.5rem 0;'><strong>Username:</strong> {st.session_state.username}</p>
                <p style='margin: 0.5rem 0;'><strong>User ID:</strong> {st.session_state.user_id}</p>
                <p style='margin: 0.5rem 0;'><strong>Role:</strong> {st.session_state.role.capitalize()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Get user stats for profile
            stats = get_user_stats()
            if stats:
                st.markdown(f"""
                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
                    <h4 style='color: #667eea; margin: 0 0 1rem 0;'>Activity Summary</h4>
                    <p style='margin: 0.5rem 0;'><strong>Total Reviews:</strong> {stats.get('total_reviews', 0)}</p>
                    <p style='margin: 0.5rem 0;'><strong>Total Aspects:</strong> {stats.get('total_aspects', 0)}</p>
                    <p style='margin: 0.5rem 0;'><strong>Positive:</strong> {stats.get('positive_aspects', 0)} | 
                       <strong>Negative:</strong> {stats.get('negative_aspects', 0)} | 
                       <strong>Neutral:</strong> {stats.get('neutral_aspects', 0)}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Change Password Section
        st.markdown("<div class='section-header'>Change Password</div>", unsafe_allow_html=True)
        
        with st.form("change_password_form"):
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);'>
            """, unsafe_allow_html=True)
            
            current_password = st.text_input("Current Password", type="password", 
                                            placeholder="Enter your current password")
            new_password = st.text_input("New Password", type="password", 
                                        placeholder="Enter new password (min 6 characters)")
            confirm_password = st.text_input("Confirm New Password", type="password", 
                                            placeholder="Re-enter new password")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submit = st.form_submit_button("Change Password", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if cancel:
                st.rerun()
            
            if submit:
                # Validation
                if not current_password or not new_password or not confirm_password:
                    st.error("All fields are required!")
                elif len(new_password) < 6:
                    st.error("New password must be at least 6 characters long!")
                elif new_password != confirm_password:
                    st.error("New passwords do not match!")
                elif current_password == new_password:
                    st.warning("New password must be different from current password!")
                else:
                    # Call API to change password
                    try:
                        response = requests.post(
                            f"{API_URL}/change-password",
                            headers=get_headers(),
                            json={
                                "current_password": current_password,
                                "new_password": new_password
                            }
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Password changed successfully!")
                            st.balloons()
                        elif response.status_code == 401:
                            st.error("❌ Current password is incorrect!")
                        else:
                            error_msg = response.json().get('detail', 'Failed to change password')
                            st.error(f"❌ {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # BATCH ANALYSIS PAGE
    elif st.session_state.page == 'batch_analysis':
        st.markdown("""
        <div class="main-header">
            <h1>📊 Batch Analysis</h1>
            <p>Upload files and analyze sentiment distribution across aspects</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Upload section
        with st.expander("📤 Upload File", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                uploaded_file = st.file_uploader(
                    "Choose a CSV or Excel file",
                    type=["csv", "xlsx", "xls"],
                    help="File should contain a 'review_text' or 'text' column"
                )
            
            with col2:
                st.info("📋 Supported formats:\n- CSV\n- XLSX\n- XLS")
        
        if uploaded_file:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Loaded {len(df)} reviews")
                
                # Show preview
                with st.expander("👀 Preview Data", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)
                
                # Analyze button
                if st.button("🚀 Analyze & Generate Visualizations", use_container_width=True, key="analyze_batch"):
                    with st.spinner("Analyzing reviews and extracting aspects..."):
                        try:
                            # Convert dataframe to list of dicts
                            records = df.to_dict('records')
                            
                            # Call batch predict endpoint
                            response = requests.post(
                                f"{API_URL}/predict-batch",
                                headers=get_headers(),
                                json={"reviews": records},
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                predictions = response.json().get('predictions', [])
                                
                                if predictions:
                                    st.success(f"✅ Analyzed {len(predictions)} aspect predictions!")
                                    
                                    # Create analysis dataframe
                                    analysis_df = pd.DataFrame(predictions)
                                    
                                    # Tabs for different views
                                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                                        "📊 Sentiment Distribution",
                                        "🎯 Aspect Distribution",
                                        "📈 Aspect-Sentiment Heatmap",
                                        "📊 Aspect-Sentiment Bar Graph",
                                        "📋 Raw Data",
                                        "📥 Download Results"
                                    ])
                                    
                                    # Tab 1: Sentiment Distribution (Pie Chart)
                                    with tab1:
                                        st.markdown("### Sentiment Distribution (All Aspects)")
                                        
                                        sentiment_counts = analysis_df['sentiment'].value_counts()
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # Pie chart
                                            fig_pie = px.pie(
                                                values=sentiment_counts.values,
                                                names=sentiment_counts.index,
                                                title="Sentiment Distribution",
                                                color_discrete_map={
                                                    'positive': '#10b981',
                                                    'negative': '#ef4444',
                                                    'neutral': '#f59e0b'
                                                },
                                                hole=0.3
                                            )
                                            fig_pie.update_layout(
                                                height=400,
                                                font=dict(size=12),
                                                showlegend=True
                                            )
                                            st.plotly_chart(fig_pie, use_container_width=True)
                                        
                                        with col2:
                                            # Stats table
                                            st.markdown("#### Sentiment Count")
                                            stats_data = {
                                                'Sentiment': sentiment_counts.index,
                                                'Count': sentiment_counts.values,
                                                'Percentage': (sentiment_counts.values / sentiment_counts.sum() * 100).round(1)
                                            }
                                            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
                                    
                                    # Tab 2: Aspect Distribution (Bar Chart)
                                    with tab2:
                                        st.markdown("### Aspect Distribution")
                                        
                                        aspect_counts = analysis_df['aspect'].value_counts()
                                        
                                        fig_bar = px.bar(
                                            x=aspect_counts.values,
                                            y=aspect_counts.index,
                                            orientation='h',
                                            title="Most Mentioned Aspects",
                                            labels={'x': 'Count', 'y': 'Aspect'},
                                            color=aspect_counts.values,
                                            color_continuous_scale='Viridis'
                                        )
                                        fig_bar.update_layout(
                                            height=400,
                                            showlegend=False
                                        )
                                        st.plotly_chart(fig_bar, use_container_width=True)
                                        
                                        # Top aspects table
                                        st.markdown("#### Top 10 Aspects")
                                        top_aspects = aspect_counts.head(10).reset_index()
                                        top_aspects.columns = ['Aspect', 'Count']
                                        st.dataframe(top_aspects, use_container_width=True, hide_index=True)
                                    
                                    # Tab 3: Aspect-Sentiment Heatmap
                                    with tab3:
                                        st.markdown("### Aspect-Sentiment Correlation")
                                        
                                        # Create pivot table
                                        pivot_data = analysis_df.pivot_table(
                                            index='aspect',
                                            columns='sentiment',
                                            aggfunc='size',
                                            fill_value=0
                                        )
                                        
                                        # Heatmap
                                        fig_heatmap = px.imshow(
                                            pivot_data,
                                            labels=dict(x="Sentiment", y="Aspect", color="Count"),
                                            x=['Negative', 'Neutral', 'Positive'] if 'positive' in pivot_data.columns else list(pivot_data.columns),
                                            y=pivot_data.index,
                                            color_continuous_scale='YlGnBu',
                                            text_auto=True,
                                            title="Aspect-Sentiment Count Matrix"
                                        )
                                        fig_heatmap.update_layout(height=500)
                                        st.plotly_chart(fig_heatmap, use_container_width=True)
                                        
                                        # Raw pivot table
                                        st.markdown("#### Count Table")
                                        st.dataframe(pivot_data, use_container_width=True)
                                    
                                    # Tab 4: Aspect-Sentiment Bar Graph
                                    with tab4:
                                        st.markdown("### Aspect-Sentiment Distribution (Bar Graph)")
                                        
                                        # Create grouped bar chart
                                        aspect_sentiment = analysis_df.groupby(['aspect', 'sentiment']).size().reset_index(name='count')
                                        
                                        # Bar chart - grouped
                                        fig_bar_grouped = px.bar(
                                            aspect_sentiment,
                                            x='aspect',
                                            y='count',
                                            color='sentiment',
                                            title="Sentiment Count by Aspect",
                                            labels={'count': 'Count', 'aspect': 'Aspect', 'sentiment': 'Sentiment'},
                                            color_discrete_map={
                                                'positive': '#10b981',
                                                'negative': '#ef4444',
                                                'neutral': '#f59e0b'
                                            },
                                            barmode='group'
                                        )
                                        fig_bar_grouped.update_layout(
                                            height=500,
                                            xaxis_tickangle=-45,
                                            hovermode='x unified'
                                        )
                                        st.plotly_chart(fig_bar_grouped, use_container_width=True)
                                        
                                        st.markdown("---")
                                        
                                        # Stacked bar chart
                                        st.markdown("#### Stacked View (Percentage)")
                                        
                                        # Calculate percentages
                                        aspect_sentiment_pct = analysis_df.groupby(['aspect', 'sentiment']).size().unstack(fill_value=0)
                                        aspect_sentiment_pct = aspect_sentiment_pct.div(aspect_sentiment_pct.sum(axis=1), axis=0) * 100
                                        
                                        fig_bar_stacked = px.bar(
                                            aspect_sentiment_pct.reset_index().melt(id_vars='aspect', var_name='sentiment', value_name='percentage'),
                                            x='aspect',
                                            y='percentage',
                                            color='sentiment',
                                            title="Sentiment Distribution by Aspect (Percentage)",
                                            labels={'percentage': 'Percentage (%)', 'aspect': 'Aspect', 'sentiment': 'Sentiment'},
                                            color_discrete_map={
                                                'positive': '#10b981',
                                                'negative': '#ef4444',
                                                'neutral': '#f59e0b'
                                            },
                                            barmode='stack'
                                        )
                                        fig_bar_stacked.update_layout(
                                            height=500,
                                            xaxis_tickangle=-45,
                                            hovermode='x unified'
                                        )
                                        st.plotly_chart(fig_bar_stacked, use_container_width=True)
                                        
                                        st.markdown("---")
                                        
                                        # Detailed table
                                        st.markdown("#### Detailed Breakdown")
                                        detailed_table = analysis_df.groupby(['aspect', 'sentiment']).size().reset_index(name='Count')
                                        st.dataframe(detailed_table, use_container_width=True, hide_index=True)
                                    
                                    # Tab 5: Raw Data
                                    with tab5:
                                        st.markdown("### Detailed Predictions")
                                        
                                        # Show full dataframe with columns
                                        st.dataframe(analysis_df, use_container_width=True)
                                    
                                    # Tab 6: Download Results
                                    with tab6:
                                        st.markdown("### Export Results")
                                        
                                        # CSV download
                                        csv_data = analysis_df.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Download as CSV",
                                            data=csv_data,
                                            file_name="batch_analysis_results.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                                        
                                        # Excel download
                                        try:
                                            import openpyxl
                                            from io import BytesIO
                                            
                                            output = BytesIO()
                                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                                analysis_df.to_excel(writer, index=False, sheet_name='Results')
                                                
                                                # Add formatting
                                                workbook = writer.book
                                                worksheet = writer.sheets['Results']
                                                worksheet.column_dimensions['A'].width = 50
                                                worksheet.column_dimensions['B'].width = 20
                                                worksheet.column_dimensions['C'].width = 15
                                                worksheet.column_dimensions['D'].width = 15
                                            
                                            excel_data = output.getvalue()
                                            st.download_button(
                                                label="📊 Download as Excel",
                                                data=excel_data,
                                                file_name="batch_analysis_results.xlsx",
                                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                use_container_width=True
                                            )
                                        except ImportError:
                                            st.info("💡 Excel export requires: `pip install openpyxl`")
                                        
                                        st.markdown("---")
                                        st.markdown("### Summary Statistics")
                                        
                                        col1, col2, col3, col4 = st.columns(4)
                                        
                                        with col1:
                                            st.markdown(f"""
                                            <div class="stat-card info-card">
                                                <h3>{len(analysis_df)}</h3>
                                                <p>Total Predictions</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col2:
                                            st.markdown(f"""
                                            <div class="stat-card positive-card">
                                                <h3>{analysis_df['aspect'].nunique()}</h3>
                                                <p>Unique Aspects</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col3:
                                            try:
                                                if 'confidence' in analysis_df.columns:
                                                    conf_vals = analysis_df['confidence'].str.rstrip('%').astype(float)
                                                    avg_confidence = conf_vals[~(conf_vals.isin([float('inf'), float('-inf')]) | conf_vals.isna())].mean()
                                                    if pd.isna(avg_confidence):
                                                        avg_confidence = 0
                                                else:
                                                    avg_confidence = 0
                                            except:
                                                avg_confidence = 0
                                            
                                            st.markdown(f"""
                                            <div class="stat-card neutral-card">
                                                <h3>{avg_confidence:.1f}%</h3>
                                                <p>Avg Confidence</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col4:
                                            positive_pct = (analysis_df['sentiment'] == 'positive').sum() / len(analysis_df) * 100
                                            st.markdown(f"""
                                            <div class="stat-card positive-card">
                                                <h3>{positive_pct:.1f}%</h3>
                                                <p>Positive Reviews</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                else:
                                    st.warning("⚠️ No predictions generated. Try with different data.")
                            else:
                                st.error(f"❌ Error: {response.json().get('detail', 'Analysis failed')}")
                        except Exception as e:
                            st.error(f"❌ Error analyzing file: {str(e)}")
            
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #9ca3af; padding: 1rem;'>
    <p>&copy; {datetime.now().year} Aspect-Based Sentiment Analysis | All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
