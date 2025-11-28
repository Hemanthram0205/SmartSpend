"""
SmartSpend - Professional Expense Tracker Application
A secure, multi-user expense tracking system with comprehensive analytics.

Author: Hemanth Ram. S
Version: 2.0.0
License: MIT
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from contextlib import contextmanager
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import calendar
import hashlib
import secrets
import logging
from pathlib import Path

# Third-party imports for visualization
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class Config:
    """Application configuration constants."""
    APP_NAME = "SmartSpend"
    APP_VERSION = "2.0.0"
    DATABASE_NAME = "expenses.db"
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_SALT_LENGTH = 32
    SESSION_TIMEOUT_MINUTES = 30
    CURRENCY_SYMBOL = "₹"
    DATE_FORMAT = "%d-%m-%Y"
    DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"
    
class ExpenseCategory(Enum):
    """Predefined expense categories."""
    FOOD = "Food"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    INVESTMENT = "Investment"
    OTHER = "Other"
    
    @classmethod
    def get_list(cls) -> List[str]:
        """Return list of category values."""
        return [cat.value for cat in cls]

class ThemeColors:
    """UI theme color constants."""
    PRIMARY = "#3b82f6"
    PRIMARY_DARK = "#1e40af"
    SUCCESS = "#10b981"
    DANGER = "#ef4444"
    WARNING = "#f59e0b"
    INFO = "#6366f1"
    BACKGROUND_DARK = "#0f1115"
    CARD_BACKGROUND = "#1e293b"
    CARD_BORDER = "#475569"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smartspend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class User:
    """User model."""
    id: int
    username: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Expense:
    """Expense model."""
    id: int
    category: str
    amount: float
    date: datetime
    description: str
    user_id: int
    created_at: Optional[datetime] = None

@dataclass
class ExpenseSummary:
    """Expense summary statistics model."""
    total_expenses: float
    average_expense: float
    expense_count: int
    top_category: str
    largest_expense: float
    monthly_expenses: float
    last_30_days: float
    last_7_days: float
    daily_average: float

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

class DatabaseManager:
    """Centralized database management class."""
    
    def __init__(self, db_name: str = Config.DATABASE_NAME):
        """Initialize database manager."""
        self.db_name = db_name
        self.db_path = Path(db_name)
        
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection object
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_name,
                check_same_thread=False,
                timeout=10.0
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def initialize_schema(self) -> None:
        """Initialize database schema with proper tables and indices."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        password_salt TEXT NOT NULL,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        CONSTRAINT username_length CHECK (LENGTH(username) >= 3)
                    )
                ''')
                
                # Expenses table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        amount REAL NOT NULL CHECK(amount > 0),
                        date TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        user_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indices for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_expenses_user_date 
                    ON expenses(user_id, date DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_expenses_category 
                    ON expenses(category)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_users_username 
                    ON users(username)
                ''')
                
                # Trigger for updated_at timestamp
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_expense_timestamp 
                    AFTER UPDATE ON expenses
                    BEGIN
                        UPDATE expenses SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                    END
                ''')
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database schema: {e}")
            raise
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for backup file. If None, auto-generates timestamped name.
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{Config.DATABASE_NAME}_{timestamp}.db"
            
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
                
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

# ============================================================================
# SECURITY & AUTHENTICATION
# ============================================================================

class SecurityManager:
    """Handle security-related operations."""
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt for password hashing."""
        return secrets.token_hex(Config.PASSWORD_SALT_LENGTH)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """
        Hash password with salt using SHA-256.
        
        Args:
            password: Plain text password
            salt: Random salt string
            
        Returns:
            str: Hashed password
        """
        salted_password = f"{password}{salt}".encode()
        return hashlib.sha256(salted_password).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored password hash
            salt: Password salt
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return SecurityManager.hash_password(password, salt) == password_hash
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < Config.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {Config.PASSWORD_MIN_LENGTH} characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username or len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return False, "Username can only contain letters, numbers, underscore and hyphen"
        
        return True, ""

# ============================================================================
# USER MANAGEMENT
# ============================================================================

class UserManager:
    """Manage user operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize user manager with database manager."""
        self.db = db_manager
        self.security = SecurityManager()
    
    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: User password
            email: Optional email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate inputs
            username = username.strip()
            
            is_valid, error_msg = self.security.validate_username(username)
            if not is_valid:
                return False, error_msg
            
            is_valid, error_msg = self.security.validate_password_strength(password)
            if not is_valid:
                return False, error_msg
            
            # Hash password
            salt = self.security.generate_salt()
            password_hash = self.security.hash_password(password, salt)
            
            # Insert user
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO users (username, password_hash, password_salt, email)
                       VALUES (?, ?, ?, ?)""",
                    (username, password_hash, salt, email)
                )
                conn.commit()
                
            logger.info(f"User created successfully: {username}")
            return True, "Account created successfully!"
            
        except sqlite3.IntegrityError:
            logger.warning(f"Attempted to create duplicate username: {username}")
            return False, "Username already exists"
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, f"Error creating account: {str(e)}"
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[int]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id, password_hash, password_salt, is_active
                       FROM users WHERE username = ?""",
                    (username.strip(),)
                )
                user = cursor.fetchone()
                
                if not user:
                    logger.warning(f"Login attempt for non-existent user: {username}")
                    return None
                
                if not user['is_active']:
                    logger.warning(f"Login attempt for inactive user: {username}")
                    return None
                
                if self.security.verify_password(
                    password,
                    user['password_hash'],
                    user['password_salt']
                ):
                    # Update last login
                    cursor.execute(
                        "UPDATE users SET last_login = ? WHERE id = ?",
                        (datetime.now(), user['id'])
                    )
                    conn.commit()
                    
                    logger.info(f"Successful login: {username}")
                    return user['id']
                
                logger.warning(f"Failed login attempt: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def get_user_info(self, user_id: int) -> Optional[User]:
        """
        Get user information by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email, created_at FROM users WHERE id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        created_at=row['created_at']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user info: {e}")
            return None

# ============================================================================
# EXPENSE MANAGEMENT
# ============================================================================

class ExpenseManager:
    """Manage expense operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize expense manager with database manager."""
        self.db = db_manager
    
    def add_expense(
        self,
        user_id: int,
        category: str,
        amount: float,
        expense_date: date,
        description: str = ""
    ) -> Tuple[bool, str]:
        """
        Add a new expense.
        
        Args:
            user_id: User ID who owns the expense
            category: Expense category
            amount: Expense amount
            expense_date: Date of expense
            description: Optional description
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate inputs
            if amount <= 0:
                return False, "Amount must be greater than zero"
            
            if category not in ExpenseCategory.get_list():
                return False, "Invalid category"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO expenses (user_id, category, amount, date, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, category.strip(), amount, expense_date.isoformat(), description.strip())
                )
                conn.commit()
                
            logger.info(f"Expense added for user {user_id}: {category} - {amount}")
            return True, "Expense added successfully!"
            
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            return False, f"Error adding expense: {str(e)}"
    
    def delete_expense(self, expense_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete an expense (with ownership verification).
        
        Args:
            expense_id: Expense ID to delete
            user_id: User ID for ownership verification
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                    (expense_id, user_id)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Expense {expense_id} deleted by user {user_id}")
                    return True, "Expense deleted successfully!"
                else:
                    logger.warning(f"Delete attempt failed - expense {expense_id} by user {user_id}")
                    return False, "Expense not found or access denied"
                    
        except Exception as e:
            logger.error(f"Error deleting expense: {e}")
            return False, f"Error deleting expense: {str(e)}"
    
    def update_expense(
        self,
        expense_id: int,
        user_id: int,
        category: Optional[str] = None,
        amount: Optional[float] = None,
        expense_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Update an existing expense.
        
        Args:
            expense_id: Expense ID to update
            user_id: User ID for ownership verification
            category: New category (optional)
            amount: New amount (optional)
            expense_date: New date (optional)
            description: New description (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            updates = []
            params = []
            
            if category is not None:
                updates.append("category = ?")
                params.append(category.strip())
            
            if amount is not None:
                if amount <= 0:
                    return False, "Amount must be greater than zero"
                updates.append("amount = ?")
                params.append(amount)
            
            if expense_date is not None:
                updates.append("date = ?")
                params.append(expense_date.isoformat())
            
            if description is not None:
                updates.append("description = ?")
                params.append(description.strip())
            
            if not updates:
                return False, "No updates provided"
            
            params.extend([expense_id, user_id])
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""UPDATE expenses SET {', '.join(updates)}
                        WHERE id = ? AND user_id = ?""",
                    params
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Expense {expense_id} updated by user {user_id}")
                    return True, "Expense updated successfully!"
                else:
                    return False, "Expense not found or access denied"
                    
        except Exception as e:
            logger.error(f"Error updating expense: {e}")
            return False, f"Error updating expense: {str(e)}"
    
    @st.cache_data(ttl=300)
    def get_user_expenses(_self, user_id: int) -> pd.DataFrame:
        """
        Get all expenses for a user (with caching).
        
        Args:
            user_id: User ID
            
        Returns:
            DataFrame of expenses
        """
        try:
            with _self.db.get_connection() as conn:
                df = pd.read_sql(
                    """SELECT id, category, amount, date, description, created_at
                       FROM expenses 
                       WHERE user_id = ? 
                       ORDER BY date DESC, created_at DESC""",
                    conn,
                    params=(user_id,)
                )
                
                if not df.empty and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                return df
                
        except Exception as e:
            logger.error(f"Error fetching expenses: {e}")
            return pd.DataFrame()
    
    def get_expense_summary(self, user_id: int) -> Optional[ExpenseSummary]:
        """
        Calculate comprehensive expense statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            ExpenseSummary object or None if no data
        """
        df = self.get_user_expenses(user_id)
        
        if df.empty or 'amount' not in df.columns:
            return None
        
        try:
            df['date'] = pd.to_datetime(df['date'])
            today = datetime.now()
            
            # Calculate time-based expenses
            current_month_mask = (
                (df['date'].dt.month == today.month) & 
                (df['date'].dt.year == today.year)
            )
            last_30_days_mask = df['date'] >= (today - timedelta(days=30))
            last_7_days_mask = df['date'] >= (today - timedelta(days=7))
            
            monthly_expenses = df[current_month_mask]['amount'].sum()
            last_30_days = df[last_30_days_mask]['amount'].sum()
            last_7_days = df[last_7_days_mask]['amount'].sum()
            
            # Get top category
            top_category = 'N/A'
            if not df['category'].empty:
                category_mode = df['category'].mode()
                if not category_mode.empty:
                    top_category = category_mode.iloc[0]
            
            return ExpenseSummary(
                total_expenses=float(df['amount'].sum()),
                average_expense=float(df['amount'].mean()),
                expense_count=len(df),
                top_category=top_category,
                largest_expense=float(df['amount'].max()),
                monthly_expenses=float(monthly_expenses),
                last_30_days=float(last_30_days),
                last_7_days=float(last_7_days),
                daily_average=float(last_30_days / 30) if last_30_days > 0 else 0.0
            )
            
        except Exception as e:
            logger.error(f"Error calculating summary: {e}")
            return None

# ============================================================================
# DATA VISUALIZATION
# ============================================================================

class ChartGenerator:
    """Generate charts and visualizations."""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount in currency."""
        return f"{Config.CURRENCY_SYMBOL}{amount:,.2f}"
    
    @staticmethod
    def get_chart_layout() -> dict:
        """Get common chart layout configuration."""
        return {
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': dict(color='white', size=12),
            'hoverlabel': dict(bgcolor="white", font_size=12),
            'margin': dict(l=20, r=20, t=40, b=20)
        }
    
    @classmethod
    def create_monthly_trend_chart(cls, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create monthly expense trend line chart."""
        if df.empty or 'date' not in df.columns:
            return None
        
        try:
            monthly = df.groupby(df['date'].dt.to_period('M')).agg({
                'amount': 'sum',
                'id': 'count'
            }).reset_index()
            
            monthly['date'] = monthly['date'].astype(str)
            monthly['amount_formatted'] = monthly['amount'].apply(cls.format_currency)
            
            fig = px.line(
                monthly,
                x='date',
                y='amount',
                title='📈 Monthly Expense Trends',
                labels={'amount': f'Amount ({Config.CURRENCY_SYMBOL})', 'date': 'Month'},
                line_shape='spline',
                custom_data=['amount_formatted', 'id']
            )
            
            fig.update_traces(
                line=dict(width=4, color=ThemeColors.PRIMARY),
                hovertemplate='<b>%{x}</b><br>Amount: %{customdata[0]}<br>Transactions: %{customdata[1]}<extra></extra>'
            )
            
            fig.update_layout(**cls.get_chart_layout())
            return fig
            
        except Exception as e:
            logger.error(f"Error creating monthly trend chart: {e}")
            return None
    
    @classmethod
    def create_category_pie_chart(cls, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create category distribution pie chart."""
        if df.empty:
            return None
        
        try:
            category_totals = df.groupby('category')['amount'].sum().reset_index()
            category_totals = category_totals.sort_values('amount', ascending=False)
            category_totals['amount_formatted'] = category_totals['amount'].apply(cls.format_currency)
            
            fig = px.pie(
                category_totals,
                values='amount',
                names='category',
                title='🥧 Expense Distribution by Category',
                hole=0.4,
                custom_data=['amount_formatted']
            )
            
            fig.update_traces(
                hovertemplate='<b>%{label}</b><br>Amount: %{customdata[0]}<br>Percentage: %{percent}<extra></extra>'
            )
            
            fig.update_layout(**cls.get_chart_layout())
            return fig
            
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            return None
    
    @classmethod
    def create_daily_expense_chart(cls, df: pd.DataFrame, days: int = 30) -> Optional[go.Figure]:
        """Create daily expense bar chart."""
        if df.empty or 'date' not in df.columns:
            return None
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_expenses = df[df['date'] >= cutoff_date]
            
            if recent_expenses.empty:
                return None
            
            daily = recent_expenses.groupby(recent_expenses['date'].dt.date)['amount'].sum().reset_index()
            daily['amount_formatted'] = daily['amount'].apply(cls.format_currency)
            
            fig = px.bar(
                daily,
                x='date',
                y='amount',
                title=f'📊 Daily Expenses (Last {days} Days)',
                labels={'amount': f'Amount ({Config.CURRENCY_SYMBOL})', 'date': 'Date'},
                custom_data=['amount_formatted']
            )
            
            fig.update_traces(
                marker_color=ThemeColors.SUCCESS,
                hovertemplate='<b>%{x}</b><br>Amount: %{customdata[0]}<extra></extra>'
            )
            
            fig.update_layout(**cls.get_chart_layout())
            return fig
            
        except Exception as e:
            logger.error(f"Error creating daily chart: {e}")
            return None
    
    @classmethod
    def create_category_bar_chart(cls, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create horizontal bar chart for categories."""
        if df.empty:
            return None
        
        try:
            category_totals = df.groupby('category')['amount'].sum().reset_index()
            category_totals = category_totals.sort_values('amount', ascending=True)
            category_totals['amount_formatted'] = category_totals['amount'].apply(cls.format_currency)
            
            fig = px.bar(
                category_totals,
                y='category',
                x='amount',
                title='📊 Expenses by Category',
                labels={'amount': f'Amount ({Config.CURRENCY_SYMBOL})', 'category': 'Category'},
                orientation='h',
                custom_data=['amount_formatted']
            )
            
            fig.update_traces(
                marker_color=ThemeColors.INFO,
                hovertemplate='<b>%{y}</b><br>Amount: %{customdata[0]}<extra></extra>'
            )
            
            fig.update_layout(**cls.get_chart_layout())
            return fig
            
        except Exception as e:
            logger.error(f"Error creating category bar chart: {e}")
            return None
    
    @classmethod
    def create_spending_timeline(cls, df: pd.DataFrame) -> Optional[go.Figure]:
        """Create cumulative spending timeline."""
        if df.empty or 'date' not in df.columns:
            return None
        
        try:
            df_sorted = df.sort_values('date')
            df_sorted['cumulative_amount'] = df_sorted['amount'].cumsum()
            df_sorted['amount_formatted'] = df_sorted['amount'].apply(cls.format_currency)
            df_sorted['cumulative_formatted'] = df_sorted['cumulative_amount'].apply(cls.format_currency)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_sorted['date'],
                y=df_sorted['cumulative_amount'],
                mode='lines',
                name='Cumulative Spending',
                line=dict(color=ThemeColors.PRIMARY, width=3),
                customdata=df_sorted['cumulative_formatted'],
                hovertemplate='<b>%{x}</b><br>Cumulative: %{customdata}<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_sorted['date'],
                y=df_sorted['amount'],
                mode='markers',
                name='Individual Expenses',
                marker=dict(color=ThemeColors.DANGER, size=6),
                customdata=df_sorted['amount_formatted'],
                hovertemplate='<b>%{x}</b><br>Amount: %{customdata}<extra></extra>'
            ))
            
            fig.update_layout(
                title='📈 Cumulative Spending Timeline',
                xaxis_title='Date',
                yaxis_title=f'Amount ({Config.CURRENCY_SYMBOL})',
                hovermode='x unified',
                **cls.get_chart_layout()
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating timeline: {e}")
            return None

# ============================================================================
# UI COMPONENTS
# ============================================================================

class UIComponents:
    """Reusable UI components."""
    
    @staticmethod
    def render_custom_css():
        """Render custom CSS styles."""
        st.markdown("""
            <style>
                .main {
                    background-color: #0f1115;
                    color: white;
                }
                .app-title {
                    text-align: center;
                    font-size: 3.5em; 
                    font-weight: 900;
                    color: transparent; 
                    background: linear-gradient(90deg, #4f46e5, #3b82f6, #1e40af); 
                    -webkit-background-clip: text;
                    background-clip: text;
                    padding: 20px 0;
                    margin-bottom: 15px;
                    letter-spacing: 2px;
                    text-shadow: 0 0 30px rgba(59, 130, 246, 0.3);
                }
                .app-subtitle {
                    text-align: center;
                    color: #94a3b8;
                    font-size: 1.1em;
                    margin-bottom: 30px;
                }
                .nav-container {
                    background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
                    padding: 20px;
                    border-radius: 16px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    margin-bottom: 25px;
                    border: 1px solid #333;
                }
                .stButton button {
                    background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                    color: white;
                    font-weight: 600;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 24px;
                    transition: all 0.3s ease;
                    font-size: 15px;
                    width: 100%;
                    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
                }
                .stButton button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
                }
                .metric-card {
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    padding: 20px;
                    border-radius: 12px;
                    border: 1px solid #475569;
                    text-align: center;
                    min-height: 130px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    transition: transform 0.2s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                .metric-card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                .metric-card h3 {
                    margin-bottom: 8px;
                    font-size: 0.85em;
                    color: #94a3b8;
                    font-weight: 500;
                }
                .metric-card h2 {
                    font-size: 1.5em;
                    margin: 0;
                    color: white;
                    font-weight: 700;
                }
                .user-welcome {
                    text-align: center;
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    padding: 15px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    border: 1px solid #475569;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                .chart-container {
                    background: #1e1e1e;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    border: 1px solid #333;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                .auth-container {
                    max-width: 450px;
                    margin: 50px auto;
                    padding: 40px;
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    border-radius: 16px;
                    border: 1px solid #475569;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
                }
                .isolation-badge {
                    background: #10b981;
                    color: white;
                    padding: 5px 14px;
                    border-radius: 20px;
                    font-size: 0.75em;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .page-header {
                    border-bottom: 2px solid #3b82f6;
                    padding-bottom: 10px;
                    margin-bottom: 25px;
                }
                .info-box {
                    background: rgba(59, 130, 246, 0.1);
                    border-left: 4px solid #3b82f6;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                .warning-box {
                    background: rgba(245, 158, 11, 0.1);
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                .success-box {
                    background: rgba(16, 185, 129, 0.1);
                    border-left: 4px solid #10b981;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 15px 0;
                }
                /* Improve form styling */
                .stTextInput input, .stNumberInput input, .stSelectbox select {
                    background-color: #1e293b !important;
                    border: 1px solid #475569 !important;
                    color: white !important;
                    border-radius: 8px !important;
                }
                .stDateInput input {
                    background-color: #1e293b !important;
                    border: 1px solid #475569 !important;
                    color: white !important;
                    border-radius: 8px !important;
                }
                /* Data table styling */
                .dataframe {
                    background-color: #1e293b !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_metric_card(title: str, value: str, icon: str = ""):
        """Render a metric card."""
        st.markdown(f"""
            <div class="metric-card">
                <h3>{icon} {title}</h3>
                <h2>{value}</h2>
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_page_header(title: str, icon: str = ""):
        """Render a page header."""
        st.markdown(f"""
            <div class="page-header">
                <h2>{icon} {title}</h2>
            </div>
        """, unsafe_allow_html=True)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manage Streamlit session state."""
    
    @staticmethod
    def initialize():
        """Initialize session state variables."""
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
        if "last_activity" not in st.session_state:
            st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        return st.session_state.user_id is not None
    
    @staticmethod
    def logout():
        """Clear session and logout user."""
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.show_login = True
        st.session_state.page = "Dashboard"
        logger.info("User logged out")
    
    @staticmethod
    def check_session_timeout():
        """Check if session has timed out."""
        if SessionManager.is_authenticated():
            last_activity = st.session_state.get('last_activity', datetime.now())
            if datetime.now() - last_activity > timedelta(minutes=Config.SESSION_TIMEOUT_MINUTES):
                SessionManager.logout()
                return True
        return False
    
    @staticmethod
    def update_activity():
        """Update last activity timestamp."""
        st.session_state.last_activity = datetime.now()

# ============================================================================
# APPLICATION PAGES
# ============================================================================

class AuthPage:
    """Authentication page (login/register)."""
    
    def __init__(self, user_manager: UserManager):
        """Initialize auth page with user manager."""
        self.user_manager = user_manager
    
    def render(self):
        """Render authentication page."""
        st.markdown(f"""
            <h1 class='app-title'>{Config.APP_NAME}</h1>
            <p class='app-subtitle'>Professional Expense Tracking & Analytics</p>
        """, unsafe_allow_html=True)
        
        if st.session_state.show_register:
            self.render_register_form()
        else:
            self.render_login_form()
    
    def render_login_form(self):
        """Render login form."""
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("🔐 Login to Your Account")
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            with col2:
                register_btn = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if login_btn:
                if username and password:
                    with st.spinner("Authenticating..."):
                        user_id = self.user_manager.authenticate_user(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = username
                            st.session_state.show_login = False
                            SessionManager.update_activity()
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                else:
                    st.error("⚠️ Please fill in all fields")
            
            if register_btn:
                st.session_state.show_register = True
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def render_register_form(self):
        """Render registration form."""
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("🚀 Create Your Account")
        
        st.markdown("""
            <div class='info-box'>
                <strong>Password Requirements:</strong>
                <ul style='margin: 5px 0 0 20px; font-size: 0.9em;'>
                    <li>At least 8 characters long</li>
                    <li>Contains uppercase and lowercase letters</li>
                    <li>Contains at least one number</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Choose a username (min 3 characters)")
            email = st.text_input("Email (Optional)", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                create_btn = st.form_submit_button("✨ Create Account", type="primary", use_container_width=True)
            with col2:
                back_btn = st.form_submit_button("← Back to Login", use_container_width=True)
            
            if create_btn:
                if username and password:
                    if password == confirm_password:
                        with st.spinner("Creating account..."):
                            success, message = self.user_manager.create_user(username, password, email)
                            if success:
                                st.success(f"✅ {message} Please login.")
                                st.session_state.show_register = False
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.error("❌ Passwords do not match")
                else:
                    st.error("⚠️ Please fill in all required fields")
            
            if back_btn:
                st.session_state.show_register = False
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)


class DashboardPage:
    """Main dashboard page."""
    
    def __init__(self, expense_manager: ExpenseManager, chart_generator: ChartGenerator):
        """Initialize dashboard with managers."""
        self.expense_manager = expense_manager
        self.chart_generator = chart_generator
    
    def render(self):
        """Render dashboard page."""
        UIComponents.render_page_header("Dashboard Overview", "📊")
        
        user_id = st.session_state.user_id
        df = self.expense_manager.get_user_expenses(user_id)
        summary = self.expense_manager.get_expense_summary(user_id)
        
        if summary and not df.empty:
            self.render_metrics(summary)
            self.render_charts(df)
        else:
            st.markdown("""
                <div class='info-box'>
                    <h3>🎯 Welcome to SmartSpend!</h3>
                    <p>You haven't recorded any expenses yet. Start by adding your first expense to see powerful analytics and insights.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ Add Your First Expense", type="primary"):
                st.session_state.page = "Add Expense"
                st.rerun()
    
    def render_metrics(self, summary: ExpenseSummary):
        """Render metric cards."""
        st.subheader("📈 Key Metrics")
        
        # Row 1
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            UIComponents.render_metric_card(
                "Total Spent",
                ChartGenerator.format_currency(summary.total_expenses),
                "💰"
            )
        with col2:
            UIComponents.render_metric_card(
                "This Month",
                ChartGenerator.format_currency(summary.monthly_expenses),
                "📅"
            )
        with col3:
            UIComponents.render_metric_card(
                "Transactions",
                str(summary.expense_count),
                "📝"
            )
        with col4:
            UIComponents.render_metric_card(
                "Daily Average",
                ChartGenerator.format_currency(summary.daily_average),
                "📊"
            )
        
        # Row 2
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            UIComponents.render_metric_card(
                "Last 7 Days",
                ChartGenerator.format_currency(summary.last_7_days),
                "🔥"
            )
        with col2:
            UIComponents.render_metric_card(
                "Last 30 Days",
                ChartGenerator.format_currency(summary.last_30_days),
                "📆"
            )
        with col3:
            UIComponents.render_metric_card(
                "Average Expense",
                ChartGenerator.format_currency(summary.average_expense),
                "💵"
            )
        with col4:
            UIComponents.render_metric_card(
                "Top Category",
                summary.top_category,
                "🏆"
            )
    
    def render_charts(self, df: pd.DataFrame):
        """Render analytics charts."""
        st.subheader("📊 Visual Analytics")
        
        # Row 1: Monthly Trend & Category Distribution
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            chart = self.chart_generator.create_monthly_trend_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("Insufficient data for monthly trends")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            chart = self.chart_generator.create_category_pie_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("Insufficient data for category distribution")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Row 2: Category Breakdown & Daily Expenses
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            chart = self.chart_generator.create_category_bar_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("Insufficient data for category breakdown")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            chart = self.chart_generator.create_daily_expense_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("No expenses in the last 30 days")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Row 3: Spending Timeline
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        chart = self.chart_generator.create_spending_timeline(df)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("Insufficient data for spending timeline")
        st.markdown("</div>", unsafe_allow_html=True)


class AddExpensePage:
    """Add expense page."""
    
    def __init__(self, expense_manager: ExpenseManager):
        """Initialize with expense manager."""
        self.expense_manager = expense_manager
    
    def render(self):
        """Render add expense page."""
        UIComponents.render_page_header("Add New Expense", "➕")
        
        st.markdown("""
            <div class='info-box'>
                Record your expenses to track spending patterns and gain insights into your financial habits.
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.selectbox(
                    "Category *",
                    ExpenseCategory.get_list(),
                    index=0,
                    help="Select the category that best describes this expense"
                )
                amount = st.number_input(
                    f"Amount ({Config.CURRENCY_SYMBOL}) *",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    help="Enter the expense amount"
                )
            
            with col2:
                expense_date = st.date_input(
                    "Date *",
                    value=date.today(),
                    max_value=date.today(),
                    help="Select the date of expense"
                )
                description = st.text_input(
                    "Description (Optional)",
                    placeholder="e.g., Lunch at restaurant",
                    help="Add a brief description"
                )
            
            submitted = st.form_submit_button("💾 Add Expense", type="primary", use_container_width=True)
            
            if submitted:
                if category and amount > 0 and expense_date:
                    with st.spinner("Adding expense..."):
                        success, message = self.expense_manager.add_expense(
                            st.session_state.user_id,
                            category,
                            amount,
                            expense_date,
                            description
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            
                            # Clear cache to refresh data
                            st.cache_data.clear()
                            
                            if st.button("📊 View Dashboard"):
                                st.session_state.page = "Dashboard"
                                st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("⚠️ Please fill in all required fields correctly")


class ViewExpensesPage:
    """View all expenses page."""
    
    def __init__(self, expense_manager: ExpenseManager):
        """Initialize with expense manager."""
        self.expense_manager = expense_manager
    
    def render(self):
        """Render view expenses page."""
        UIComponents.render_page_header("All Expenses", "📋")
        
        user_id = st.session_state.user_id
        df = self.expense_manager.get_user_expenses(user_id)
        
        if df.empty:
            st.markdown("""
                <div class='info-box'>
                    <p>No expenses found. Start tracking by adding your first expense!</p>
                </div>
            """, unsafe_allow_html=True)
            return
        
        # Filter options
        with st.expander("🔍 Filter Options", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                categories = ['All'] + ExpenseCategory.get_list()
                selected_category = st.selectbox("Category", categories)
            
            with col2:
                date_from = st.date_input("From Date", value=None)
            
            with col3:
                date_to = st.date_input("To Date", value=None)
        
        # Apply filters
        filtered_df = df.copy()
        
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
        if date_from:
            filtered_df = filtered_df[filtered_df['date'] >= pd.to_datetime(date_from)]
        
        if date_to:
            filtered_df = filtered_df[filtered_df['date'] <= pd.to_datetime(date_to)]
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(filtered_df))
        with col2:
            st.metric("Total Amount", ChartGenerator.format_currency(filtered_df['amount'].sum() if not filtered_df.empty else 0))
        with col3:
            st.metric("Average", ChartGenerator.format_currency(filtered_df['amount'].mean() if not filtered_df.empty else 0))
        
        # Display table
        if not filtered_df.empty:
            display_df = filtered_df.copy()
            display_df['date'] = display_df['date'].dt.strftime(Config.DATE_FORMAT)
            display_df['amount'] = display_df['amount'].apply(ChartGenerator.format_currency)
            
            # Select columns to display
            columns_to_show = ['date', 'category', 'description', 'amount']
            
            st.dataframe(
                display_df[columns_to_show],
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Export option
            csv = display_df[columns_to_show].to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No expenses match the selected filters")


class DeleteExpensePage:
    """Delete expense page."""
    
    def __init__(self, expense_manager: ExpenseManager):
        """Initialize with expense manager."""
        self.expense_manager = expense_manager
    
    def render(self):
        """Render delete expense page."""
        UIComponents.render_page_header("Delete Expense", "❌")
        
        st.markdown("""
            <div class='warning-box'>
                <strong>⚠️ Warning:</strong> Deleting an expense is permanent and cannot be undone.
            </div>
        """, unsafe_allow_html=True)
        
        user_id = st.session_state.user_id
        df = self.expense_manager.get_user_expenses(user_id)
        
        if df.empty:
            st.info("No expenses to delete")
            return
        
        # Create display dataframe
        display_df = df.copy()
        display_df['date'] = display_df['date'].dt.strftime(Config.DATE_FORMAT)
        display_df['amount'] = display_df['amount'].apply(ChartGenerator.format_currency)
        display_df['label'] = (
            display_df['date'] + " | " +
            display_df['category'] + " | " +
            display_df['amount'] +
            (" | " + display_df['description'] if 'description' in display_df.columns else "")
        )
        
        # Selection
        expense_to_delete = st.selectbox(
            "Select an expense to delete",
            options=display_df['id'].tolist(),
            format_func=lambda x: display_df[display_df['id'] == x]['label'].iloc[0]
        )
        
        # Show details of selected expense
        if expense_to_delete:
            selected = display_df[display_df['id'] == expense_to_delete].iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Date", selected['date'])
            with col2:
                st.metric("Category", selected['category'])
            with col3:
                st.metric("Amount", selected['amount'])
            with col4:
                st.metric("Description", selected.get('description', 'N/A'))
        
        # Confirmation
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                with st.spinner("Deleting..."):
                    success, message = self.expense_manager.delete_expense(
                        expense_to_delete,
                        user_id
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class SmartSpendApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize application."""
        # Configure Streamlit
        st.set_page_config(
            page_title=f"{Config.APP_NAME} - Professional Expense Tracker",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        self.user_manager = UserManager(self.db_manager)
        self.expense_manager = ExpenseManager(self.db_manager)
        self.chart_generator = ChartGenerator()
        
        # Initialize session
        SessionManager.initialize()
        
        # Initialize database
        self.db_manager.initialize_schema()
        
        # Apply custom CSS
        UIComponents.render_custom_css()
    
    def render_navigation(self):
        """Render navigation menu."""
        st.markdown(f"""
            <div class="user-welcome">
                <h3>👋 Welcome back, <strong>{st.session_state.username}</strong>! 
                <span class="isolation-badge">🔒 Secure Session</span></h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='nav-container'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
            if st.button("❌ Delete Expense", use_container_width=True):
                st.session_state.page = "Delete Expense"
                st.rerun()
        
        with col5:
            if st.button("🚪 Logout", use_container_width=True):
                SessionManager.logout()
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def run(self):
        """Run the application."""
        # Check session timeout
        if SessionManager.check_session_timeout():
            st.warning("⏰ Session expired. Please login again.")
            st.rerun()
        
        # Update activity
        SessionManager.update_activity()
        
        # Render appropriate page
        if not SessionManager.is_authenticated():
            auth_page = AuthPage(self.user_manager)
            auth_page.render()
        else:
            self.render_navigation()
            
            # Route to appropriate page
            if st.session_state.page == "Dashboard":
                page = DashboardPage(self.expense_manager, self.chart_generator)
            elif st.session_state.page == "Add Expense":
                page = AddExpensePage(self.expense_manager)
            elif st.session_state.page == "View All":
                page = ViewExpensesPage(self.expense_manager)
            elif st.session_state.page == "Delete Expense":
                page = DeleteExpensePage(self.expense_manager)
            else:
                page = DashboardPage(self.expense_manager, self.chart_generator)
            
            page.render()
        
        # Footer
        st.markdown("---")
        st.markdown(f"""
            <div style='text-align: center; color: #64748b; font-size: 0.85em; padding: 10px;'>
                {Config.APP_NAME} v{Config.APP_VERSION} | Professional Expense Tracking System<br>
                Made with ❤️ using Streamlit | © 2024 All Rights Reserved
            </div>
        """, unsafe_allow_html=True)


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        app = SmartSpendApp()
        app.run()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        st.error(f"⚠️ An unexpected error occurred. Please contact support.")
        st.error(f"Error details: {str(e)}")
