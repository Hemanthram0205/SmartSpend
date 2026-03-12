import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from contextlib import contextmanager
import hashlib
import os
import re

# ---------- PAGE CONFIG (MUST BE FIRST) ----------
st.set_page_config(
    page_title="SmartSpend - Expense Tracker", 
    page_icon="💰", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- DATABASE UTILITIES ----------
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect("expenses.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with proper schema"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      email TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Categories table
        c.execute('''CREATE TABLE IF NOT EXISTS categories
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      name TEXT NOT NULL,
                      emoji TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')

        # Check if expenses table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
        table_exists = c.fetchone() is not None
        
        if not table_exists:
            c.execute('''CREATE TABLE expenses
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          category TEXT NOT NULL,
                          amount REAL NOT NULL CHECK(amount >= 0),
                          date TEXT NOT NULL,
                          description TEXT,
                          user_id INTEGER NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_expenses_user_date 
                         ON expenses(user_id, date DESC)''')
        else:
            c.execute("PRAGMA table_info(expenses)")
            columns = [column[1] for column in c.fetchall()]
            
            if 'user_id' not in columns:
                c.execute('''ALTER TABLE expenses ADD COLUMN user_id INTEGER''')
                c.execute("SELECT id FROM users WHERE id = 1")
                if c.fetchone():
                    c.execute("UPDATE expenses SET user_id = 1 WHERE user_id IS NULL")
                else:
                    c.execute("DELETE FROM expenses WHERE user_id IS NULL")
        
        conn.commit()

# ---------- AUTHENTICATION FUNCTIONS ----------
def hash_password(password):
    salt = os.urandom(16).hex()
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()
    return f"pbkdf2${salt}${pw_hash}"

def verify_password(password, password_hash):
    if password_hash.startswith('pbkdf2$'):
        _, salt, hash_val = password_hash.split('$')
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100000).hex()
        return pw_hash == hash_val
    else:
        # Fallback to legacy sha256
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

def create_user(username, password, email=None):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            if not username or not password:
                return False, "Username and password are required"
            if len(password) < 6:
                return False, "Password must be at least 6 characters"
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return False, "Invalid email address format"
            
            password_hash = hash_password(password)
            c.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                     (username.strip(), password_hash, email))
            conn.commit()
            return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Error: {str(e)}"

def authenticate_user(username, password):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if user and verify_password(password, user['password_hash']):
            return user['id']
        return None

# ---------- DATA OPERATIONS ----------
def get_current_user_expenses(user_id):
    with get_db_connection() as conn:
        try:
            df = pd.read_sql(
                "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC", 
                conn, 
                params=(user_id,)
            )
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            st.error(f"Error loading expenses: {str(e)}")
            return pd.DataFrame()

def add_expense(category, amount, expense_date, description, user_id):
    if description and len(description) > 200:
        description = description[:200]
        
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            date_str = expense_date.isoformat() if hasattr(expense_date, 'isoformat') else str(expense_date)
            desc_str = description.strip() if description else ""
            c.execute(
                "INSERT INTO expenses (category, amount, date, description, user_id) VALUES (?, ?, ?, ?, ?)",
                (category.strip(), amount, date_str, desc_str, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Error adding expense: {str(e)}")
            return False

def delete_expense(expense_id, user_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
        conn.commit()
        return c.rowcount > 0

def get_expense_summary(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Main aggregations
        c.execute("""
            SELECT 
                COALESCE(SUM(amount), 0) as total_expenses,
                COALESCE(AVG(amount), 0) as average_expense,
                COUNT(id) as expense_count,
                COALESCE(MAX(amount), 0) as largest_expense,
                COALESCE(SUM(CASE WHEN strftime('%Y-%m', date) = strftime('%Y-%m', 'now', 'localtime') THEN amount ELSE 0 END), 0) as monthly_expenses,
                COALESCE(SUM(CASE WHEN date >= date('now', '-30 days', 'localtime') THEN amount ELSE 0 END), 0) as last_30_days,
                COALESCE(SUM(CASE WHEN date >= date('now', '-7 days', 'localtime') THEN amount ELSE 0 END), 0) as last_7_days
            FROM expenses 
            WHERE user_id = ?
        """, (user_id,))
        
        row = c.fetchone()
        if not row or row['expense_count'] == 0:
            return None
            
        summary = dict(row)
        summary['daily_average'] = summary['last_30_days'] / 30 if summary['last_30_days'] else 0
        
        # Top category
        c.execute("""
            SELECT category 
            FROM expenses 
            WHERE user_id = ? 
            GROUP BY category 
            ORDER BY COUNT(id) DESC 
            LIMIT 1
        """, (user_id,))
        cat_row = c.fetchone()
        summary['top_category'] = cat_row['category'] if cat_row else 'N/A'
        
        return summary

def format_currency(amount):
    return f"₹{amount:,.2f}"

# ---------- CHART FUNCTIONS ----------
def create_monthly_trend_chart(df):
    if df.empty or 'date' not in df.columns:
        return None
        
    monthly = df.groupby(df['date'].dt.to_period('M')).agg({'amount': 'sum', 'id': 'count'}).reset_index()
    monthly['date'] = monthly['date'].astype(str)
    monthly['amount_formatted'] = monthly['amount'].apply(format_currency)
    
    fig = px.line(monthly, x='date', y='amount', 
                  title='📈 Monthly Expense Trends',
                  labels={'amount': 'Amount (₹)', 'date': 'Month'},
                  line_shape='spline',
                  custom_data=[monthly['amount_formatted'], monthly['id']])
    fig.update_traces(
        line=dict(width=4, color='#667eea'),
        mode='lines+markers',
        marker=dict(size=10, color='#667eea'),
        hovertemplate='<b>%{x}</b><br>Amount: %{customdata[0]}<br>Transactions: %{customdata[1]}<extra></extra>'
    )
    fig.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', size=12),
        title_font=dict(size=18, color='#e2e8f0'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_category_pie_chart(df):
    if df.empty:
        return None
        
    category_totals = df.groupby('category')['amount'].sum().reset_index()
    category_totals = category_totals.sort_values('amount', ascending=False)
    category_totals['amount_formatted'] = category_totals['amount'].apply(format_currency)
    
    colors = ['#667eea', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6']
    
    fig = px.pie(category_totals, values='amount', names='category',
                 title='🎯 Category Distribution',
                 hole=0.5,
                 custom_data=[category_totals['amount_formatted']],
                 color_discrete_sequence=colors)
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Amount: %{customdata[0]}<br>Percentage: %{percent}<extra></extra>',
        textposition='outside',
        textinfo='percent+label'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', size=12),
        title_font=dict(size=18, color='#e2e8f0'),
        showlegend=True,
        legend=dict(font=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_daily_expense_chart(df):
    if df.empty or 'date' not in df.columns:
        return None
        
    last_30_days = datetime.now() - timedelta(days=30)
    recent_expenses = df[df['date'] >= last_30_days]
    
    if recent_expenses.empty:
        return None
        
    daily = recent_expenses.groupby(recent_expenses['date'].dt.date)['amount'].sum().reset_index()
    daily['amount_formatted'] = daily['amount'].apply(format_currency)
    
    fig = px.bar(daily, x='date', y='amount',
                 title='📊 Daily Expenses (Last 30 Days)',
                 labels={'amount': 'Amount (₹)', 'date': 'Date'},
                 custom_data=[daily['amount_formatted']])
    fig.update_traces(
        marker_color='#10b981',
        marker_line_color='#059669',
        marker_line_width=1,
        hovertemplate='<b>%{x}</b><br>Amount: %{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', size=12),
        title_font=dict(size=18, color='#e2e8f0'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=50, b=20),
        bargap=0.3
    )
    return fig

def create_category_bar_chart(df):
    if df.empty:
        return None
        
    category_totals = df.groupby('category')['amount'].sum().reset_index()
    category_totals = category_totals.sort_values('amount', ascending=True)
    category_totals['amount_formatted'] = category_totals['amount'].apply(format_currency)
    
    fig = px.bar(category_totals, y='category', x='amount',
                 title='💳 Expenses by Category',
                 labels={'amount': 'Amount (₹)', 'category': 'Category'},
                 orientation='h',
                 custom_data=[category_totals['amount_formatted']])
    fig.update_traces(
        marker_color='#8b5cf6',
        marker_line_color='#7c3aed',
        marker_line_width=1,
        hovertemplate='<b>%{y}</b><br>Amount: %{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', size=12),
        title_font=dict(size=18, color='#e2e8f0'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
        margin=dict(l=20, r=20, t=50, b=20),
        bargap=0.4
    )
    return fig

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* App Title */
    .app-title {
        text-align: center;
        font-size: 3.5em;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        padding: 20px 0;
        margin-bottom: 10px;
        letter-spacing: 2px;
    }
    
    .app-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1em;
        margin-bottom: 30px;
    }
    
    /* User welcome banner */
    .user-welcome {
        text-align: center;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 25px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .user-welcome h3 {
        color: #e2e8f0;
        margin: 0;
        font-size: 1.2em;
    }
    
    .isolation-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
        margin-left: 10px;
        display: inline-block;
    }
    
    /* Navigation container */
    .nav-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 30px;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        text-align: center;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.2);
        border-color: rgba(139, 92, 246, 0.4);
    }
    
    .metric-card h3 {
        color: #94a3b8;
        font-size: 0.95em;
        margin-bottom: 8px;
        font-weight: 500;
    }
    
    .metric-card h2 {
        color: #e2e8f0;
        font-size: 1.6em;
        margin: 0;
        font-weight: 700;
    }
    
    /* Chart container */
    .chart-container {
        background: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 20px;
    }
    
    /* Auth container */
    .auth-container {
        max-width: 420px;
        margin: 40px auto;
        padding: 40px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .auth-header h2 {
        color: #e2e8f0;
        font-size: 1.8em;
        margin-bottom: 8px;
    }
    
    .auth-header p {
        color: #94a3b8;
        font-size: 1em;
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        transition: all 0.3s ease !important;
        font-size: 1em !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Danger button for delete */
    .delete-btn > button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    
    .delete-btn > button:hover {
        box-shadow: 0 10px 30px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Logout button */
    .logout-btn > button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    
    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 1.5em;
        font-weight: 700;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
    }
    
    /* Expense row card */
    .expense-row {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    
    .expense-row:hover {
        background: rgba(102, 126, 234, 0.1);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .expense-info {
        flex: 1;
    }
    
    .expense-category {
        font-size: 1.1em;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 4px;
    }
    
    .expense-details {
        font-size: 0.9em;
        color: #94a3b8;
    }
    
    .expense-amount {
        font-size: 1.2em;
        font-weight: 700;
        color: #10b981;
        margin-right: 20px;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #94a3b8;
    }
    
    .empty-state-icon {
        font-size: 4em;
        margin-bottom: 20px;
    }
    
    .empty-state h3 {
        color: #e2e8f0;
        font-size: 1.5em;
        margin-bottom: 10px;
    }
    
    /* Form container */
    .form-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
        margin: 30px 0;
    }
    
    /* Category emoji mapping */
    .category-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 500;
        background: rgba(102, 126, 234, 0.2);
        color: #a5b4fc;
    }
</style>
""", unsafe_allow_html=True)

# ---------- INITIALIZATION ----------
init_db()

# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "show_login" not in st.session_state:
    st.session_state.show_login = True
if "show_register" not in st.session_state:
    st.session_state.show_register = False

# ---------- CATEGORY HELPERS ----------
CATEGORY_EMOJIS = {
    "Food": "🍔",
    "Transport": "🚗",
    "Shopping": "🛍️",
    "Bills": "📄",
    "Entertainment": "🎬",
    "Healthcare": "🏥",
    "Other": "📦"
}

def get_user_categories(user_id):
    cats = CATEGORY_EMOJIS.copy()
    if not user_id: 
        return cats
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("SELECT name, emoji FROM categories WHERE user_id = ?", (user_id,))
            for row in c.fetchall():
                cats[row['name']] = row['emoji'] or "📦"
        except sqlite3.OperationalError:
            pass # Table might not exist yet during init
    return cats

def get_category_emoji(category):
    user_id = st.session_state.get('user_id')
    cats = get_user_categories(user_id)
    return cats.get(category, "📦")

def add_custom_category(user_id, name, emoji):
    with get_db_connection() as conn:
        c = conn.cursor()
        # Avoid duplicates
        c.execute("SELECT id FROM categories WHERE user_id=? AND name=?", (user_id, name.strip()))
        if not c.fetchone():
            c.execute("INSERT INTO categories (user_id, name, emoji) VALUES (?, ?, ?)", 
                      (user_id, name.strip(), emoji.strip() if emoji else "📦"))
            conn.commit()
            return True
        return False

# ---------- AUTHENTICATION PAGE ----------
def show_auth_page():
    st.markdown("<h1 class='app-title'>💰 SmartSpend</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Track your expenses intelligently</p>", unsafe_allow_html=True)
    
    if st.session_state.show_register:
        show_register_form()
    else:
        show_login_form()

def show_login_form():
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.markdown("""
        <div class='auth-header'>
            <h2>🔐 Welcome Back</h2>
            <p>Sign in to access your expenses</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        
        if submitted:
            if username and password:
                user_id = authenticate_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.show_login = False
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            else:
                st.error("⚠️ Please fill in all fields")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create New Account", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

def show_register_form():
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.markdown("""
        <div class='auth-header'>
            <h2>🚀 Create Account</h2>
            <p>Start tracking your expenses today</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email (optional)", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            if username and password:
                if password == confirm_password:
                    success, message = create_user(username, password, email)
                    if success:
                        st.success("✅ Account created! Please login.")
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match")
            else:
                st.error("⚠️ Username and password are required")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- MAIN APP ----------
def show_main_app():
    # Title
    st.markdown("<h1 class='app-title'>💰 SmartSpend</h1>", unsafe_allow_html=True)
    
    # User welcome message
    st.markdown(f"""
        <div class="user-welcome">
            <h3>👋 Welcome back, <strong>{st.session_state.username}</strong>!
            <span class="isolation-badge">🔒 Private Space</span></h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    st.markdown("<div class='nav-container'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()
    with col2:
        if st.button("➕ Add Expense", use_container_width=True):
            st.session_state.page = "Add Expense"
            st.rerun()
    with col3:
        if st.button("📋 View All", use_container_width=True):
            st.session_state.page = "View All"
            st.rerun()
    with col4:
        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.show_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Page content
    if st.session_state.page == "Dashboard":
        show_dashboard()
    elif st.session_state.page == "Add Expense":
        show_add_expense()
    elif st.session_state.page == "View All":
        show_view_all()

def show_dashboard():
    st.markdown("<div class='section-header'>📊 Expense Dashboard</div>", unsafe_allow_html=True)
    
    df = get_current_user_expenses(st.session_state.user_id)
    summary = get_expense_summary(st.session_state.user_id)
    
    if summary and not df.empty:
        # Metrics Row 1
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>💰 Total Spent</h3>
                    <h2>{format_currency(summary['total_expenses'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📅 This Month</h3>
                    <h2>{format_currency(summary['monthly_expenses'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📝 Transactions</h3>
                    <h2>{summary['expense_count']}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📊 Daily Average</h3>
                    <h2>{format_currency(summary['daily_average'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Metrics Row 2
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>🔥 Last 7 Days</h3>
                    <h2>{format_currency(summary['last_7_days'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>📆 Last 30 Days</h3>
                    <h2>{format_currency(summary['last_30_days'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>💵 Avg Expense</h3>
                    <h2>{format_currency(summary['average_expense'])}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <h3>🏆 Top Category</h3>
                    <h2>{get_category_emoji(summary['top_category'])} {summary['top_category']}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📈 Visual Analytics</div>", unsafe_allow_html=True)
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            monthly_chart = create_monthly_trend_chart(df)
            if monthly_chart:
                st.plotly_chart(monthly_chart, use_container_width=True)
            else:
                st.info("No data for monthly trends")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            category_pie = create_category_pie_chart(df)
            if category_pie:
                st.plotly_chart(category_pie, use_container_width=True)
            else:
                st.info("No data for category distribution")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            daily_chart = create_daily_expense_chart(df)
            if daily_chart:
                st.plotly_chart(daily_chart, use_container_width=True)
            else:
                st.info("No expenses in the last 30 days")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            category_bar = create_category_bar_chart(df)
            if category_bar:
                st.plotly_chart(category_bar, use_container_width=True)
            else:
                st.info("No data for category breakdown")
            st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <h3>No expenses yet</h3>
                <p>Start tracking your spending by adding your first expense!</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("➕ Add Your First Expense", use_container_width=True):
                st.session_state.page = "Add Expense"
                st.rerun()

def show_add_expense():
    st.markdown("<div class='section-header'>➕ Add New Expense</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)
    
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            user_cats = get_user_categories(st.session_state.user_id)
            category = st.selectbox(
                "Category",
                list(user_cats.keys()),
                format_func=lambda x: f"{get_category_emoji(x)} {x}"
            )
            amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01, format="%.2f")
        
        with col2:
            expense_date = st.date_input("Date", value=date.today())
            description = st.text_input("Description (optional)", placeholder="Enter description")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Add Expense", use_container_width=True)
        
        if submitted:
            if category and amount > 0:
                success = add_expense(category, amount, expense_date, description, st.session_state.user_id)
                if success:
                    st.success("✅ Expense added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add expense")
            else:
                st.error("⚠️ Please fill in all required fields")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.expander("🛠️ Manage Custom Categories"):
        with st.form("add_category_form", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_cat_name = st.text_input("New Category Name", placeholder="e.g. Travel")
            with col2:
                new_cat_emoji = st.text_input("Emoji", max_chars=2, placeholder="✈️")
            submit_cat = st.form_submit_button("Add Category")
            if submit_cat:
                if new_cat_name:
                    if add_custom_category(st.session_state.user_id, new_cat_name, new_cat_emoji):
                        st.success(f"Added new category: {new_cat_emoji} {new_cat_name}")
                        st.rerun()
                    else:
                        st.error("Category already exists!")
                else:
                    st.error("Please enter a category name.")

def show_view_all():
    st.markdown("<div class='section-header'>📋 All Expenses</div>", unsafe_allow_html=True)
    
    df = get_current_user_expenses(st.session_state.user_id)
    
    if df.empty:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <h3>No expenses found</h3>
                <p>Add some expenses to see them here</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Action Bar
        col1, col2 = st.columns([3, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # alignment
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name='smartspend_expenses.csv',
                mime='text/csv',
                use_container_width=True
            )
            
        with col1:
            st.markdown("<p style='color: #94a3b8; padding-top: 15px;'>Edit cells directly or select rows to delete. Click Save Changes when done.</p>", unsafe_allow_html=True)
        
        # Prepare DataEditor
        edit_df = df[['id', 'date', 'category', 'description', 'amount']].copy()
        edit_df['date'] = pd.to_datetime(edit_df['date']).dt.date
        
        edited_state = st.data_editor(
            edit_df,
            hide_index=True,
            column_config={
                "id": None, # hidden
                "date": st.column_config.DateColumn("Date", required=True),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Expense Category",
                    width="medium",
                    options=list(get_user_categories(st.session_state.user_id).keys()),
                    required=True
                ),
                "description": st.column_config.TextColumn("Description"),
                "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0.01, format="%.2f", required=True)
            },
            num_rows="dynamic",
            use_container_width=True,
            key="expense_editor_grid"
        )
        
        # We need a form or simple button to save
        if st.button("💾 Save Changes", use_container_width=True):
            changes = st.session_state.expense_editor_grid
            changes_made = False
            
            # Deletions
            for row_idx in changes.get("deleted_rows", []):
                expense_id = int(edit_df.iloc[row_idx]["id"])
                delete_expense(expense_id, st.session_state.user_id)
                changes_made = True
            
            # Edits
            for row_idx, edits in changes.get("edited_rows", {}).items():
                row_idx = int(row_idx)
                orig_row = edit_df.iloc[row_idx]
                expense_id = int(orig_row["id"])
                new_cat = edits.get("category", orig_row["category"])
                new_desc = edits.get("description", orig_row["description"])
                new_amt = edits.get("amount", orig_row["amount"])
                new_date = edits.get("date", orig_row["date"])
                
                with get_db_connection() as conn:
                    conn.execute("UPDATE expenses SET category=?, description=?, amount=?, date=? WHERE id=? AND user_id=?", 
                                 (new_cat, new_desc, new_amt, str(new_date), expense_id, st.session_state.user_id))
                    conn.commit()
                changes_made = True
                    
            # Additions
            for row in changes.get("added_rows", []):
                if "amount" in row and "category" in row and "date" in row:
                    add_expense(row["category"], row["amount"], row["date"], row.get("description", ""), st.session_state.user_id)
                    changes_made = True
                    
            if changes_made:
                st.success("✅ Changes saved successfully!")
                st.rerun()
            else:
                st.info("No changes to save.")

# ---------- MAIN APP LOGIC ----------
if st.session_state.show_login or st.session_state.user_id is None:
    show_auth_page()
else:
    show_main_app()
