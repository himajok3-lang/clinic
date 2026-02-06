import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
from auth import auth
from database import db

# Streamlit page configuration
st.set_page_config(
    page_title="Clinic Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None


def load_css():
    """Load CSS styles"""
    st.markdown("""
        <style>
        .main {
            direction: ltr;
            text-align: left;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }
        .sidebar-content {
            direction: ltr;
            text-align: left;
        }
        </style>
    """, unsafe_allow_html=True)


def show_login_page():
    """Display login page"""
    load_css()

    st.markdown("""
        <div class="header">
            <h1 style="text-align: center; margin: 0;">🏥 Clinic Management System</h1>
            <p style="text-align: center; margin: 0; opacity: 0.9;">Comprehensive Clinic Management Solution</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)

            st.subheader("🔐 Login to System")

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "👤 Username",
                    placeholder="Enter your username",
                    help="Enter your registered username"
                )

                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    placeholder="Enter your password",
                    help="Enter your account password"
                )

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_submit = st.form_submit_button(
                        "🚀 Login",
                        use_container_width=True,
                        type="primary"
                    )
                with col_btn2:
                    reset_btn = st.form_submit_button(
                        "🔄 Reset",
                        use_container_width=True
                    )

                if login_submit:
                    if username and password:
                        with st.spinner("Verifying credentials..."):
                            time.sleep(1)
                            success, message = auth.login(username, password)

                            if success:
                                st.success("✅ Login successful!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password")
                    else:
                        st.warning("⚠️ Please enter username and password")

                if reset_btn:
                    st.rerun()

            # Help information
            with st.expander("💡 Login Help"):
                st.info("""
                **Default credentials:**
                - Admin: admin / admin123

                **Forgot password?** Please contact system administrator.
                """)

            st.markdown("</div>", unsafe_allow_html=True)


def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Total patients
        patients_result = db.execute_query("SELECT COUNT(*) FROM patients")
        total_patients = patients_result[0][0][0] if patients_result[0] else 0

        # New patients today
        new_patients_result = db.execute_query(
            "SELECT COUNT(*) FROM patients WHERE DATE(created_at) = ?",
            (date.today(),)
        )
        new_patients_today = new_patients_result[0][0][0] if new_patients_result[0] else 0

        # Today's appointments
        appointments_result = db.execute_query(
            """SELECT COUNT(*) FROM appointments 
               WHERE appointment_date = ? AND status = 'Scheduled'""",
            (date.today(),)
        )
        today_appointments = appointments_result[0][0][0] if appointments_result[0] else 0

        # Total revenue
        revenue_result = db.execute_query(
            """SELECT COALESCE(SUM(amount), 0) FROM bills 
               WHERE payment_status = 'Paid'"""
        )
        total_revenue = revenue_result[0][0][0] if revenue_result[0] else 0

        # Unpaid bills
        unpaid_result = db.execute_query(
            "SELECT COUNT(*) FROM bills WHERE payment_status = 'Unpaid'"
        )
        unpaid_bills = unpaid_result[0][0][0] if unpaid_result[0] else 0

        return {
            'total_patients': total_patients,
            'new_patients_today': new_patients_today,
            'today_appointments': today_appointments,
            'total_revenue': total_revenue,
            'unpaid_bills': unpaid_bills
        }

    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        return {
            'total_patients': 0,
            'new_patients_today': 0,
            'today_appointments': 0,
            'total_revenue': 0,
            'unpaid_bills': 0
        }


def show_dashboard():
    """Display main dashboard"""
    load_css()

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)

        st.markdown("<h1 style='text-align: center; font-size: 60px;'>🏥</h1>", unsafe_allow_html=True)

        # User information
        user = st.session_state.user
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                <h4 style='margin: 0; text-align: center;'>Welcome, {user['full_name']}</h4>
                <p style='margin: 0.2rem 0; text-align: center; color: #666;'>
                    👤 Role: {user['role']}
                </p>
                <p style='margin: 0; text-align: center; color: #666;'>
                    📧 {user.get('email', '')}
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation menu
        st.subheader("🧭 Quick Navigation")

        nav_items = [
            {"label": "🏠 Dashboard", "page": "app.py"},
            {"label": "👥 Patients Management", "page": "pages/1_Patients.py"},
            {"label": "📅 Appointments", "page": "pages/2_Appointments.py"},
            {"label": "📋 Medical Records", "page": "pages/3_Medical_Records.py"},
            {"label": "💰 Bills", "page": "pages/4_Bills.py"},
            {"label": "📊 Reports", "page": "pages/5_Reports.py"}
        ]

        if user.get('role') in ['admin', 'manager']:
            nav_items.append({"label": "👤 Users Management", "page": "pages/6_Users.py"})

        for item in nav_items:
            if st.button(item['label'], use_container_width=True, key=f"nav_{item['page']}"):
                st.switch_page(item['page'])

        st.markdown("---")

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            auth.logout()
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Main content
    st.title("🏠 Dashboard")

    # Quick statistics
    st.subheader("📊 Quick Overview")

    stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 Total Patients",
            stats['total_patients'],
            delta=stats['new_patients_today'],
            delta_color="normal"
        )

    with col2:
        st.metric(
            "📅 Today's Appointments",
            stats['today_appointments']
        )

    with col3:
        st.metric(
            "💰 Total Revenue",
            f"${stats['total_revenue']:,.0f}"
        )

    with col4:
        st.metric(
            "🧾 Unpaid Bills",
            stats['unpaid_bills']
        )

    # Main sections
    col1, col2 = st.columns(2)

    with col1:
        # Alerts and notifications
        with st.expander("🔔 Alerts and Notifications", expanded=True):
            try:
                # Today's appointments
                upcoming = db.execute_query("""
                    SELECT p.name, a.appointment_time 
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    WHERE a.appointment_date = ?
                    AND a.status = 'Scheduled'
                    ORDER BY a.appointment_time
                """, (date.today(),))

                if upcoming[0]:
                    st.info(f"📅 You have {len(upcoming[0])} appointments today")
                    for appointment in upcoming[0]:
                        st.write(f"⏰ {appointment[0]} - {appointment[1]}")
                else:
                    st.success("✅ No appointments scheduled for today")

                # Overdue bills
                overdue = db.execute_query("""
                    SELECT COUNT(*) 
                    FROM bills 
                    WHERE payment_status = 'Unpaid'
                    AND julianday('now') - julianday(bill_date) > 30
                """)

                if overdue[0] and overdue[0][0][0] > 0:
                    st.error(f"⚠️ There are {overdue[0][0][0]} overdue bills")
                else:
                    st.success("✅ No overdue bills")

            except Exception as e:
                st.error(f"Error loading alerts: {str(e)}")

    with col2:
        # Quick actions
        with st.expander("🚀 Quick Actions", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                if st.button("➕ New Patient", use_container_width=True, key="quick_add_patient"):
                    st.switch_page("pages/1_Patients.py")
                if st.button("📅 New Appointment", use_container_width=True, key="quick_add_appointment"):
                    st.switch_page("pages/2_Appointments.py")

            with col2:
                if st.button("🧾 New Bill", use_container_width=True, key="quick_add_bill"):
                    st.switch_page("pages/4_Bills.py")
                if st.button("📊 View Reports", use_container_width=True, key="quick_view_reports"):
                    st.switch_page("pages/5_Reports.py")

    # Today's appointments
    with st.expander("📅 Today's Appointments", expanded=True):
        try:
            appointments = db.execute_query("""
                SELECT p.name, a.appointment_time, a.status, a.doctor_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.appointment_date = ?
                ORDER BY a.appointment_time
            """, (date.today(),))

            if appointments[0]:
                for appointment in appointments[0]:
                    status_icon = "✅" if appointment[2] == "Completed" else "⏳"
                    status_text = "Completed" if appointment[2] == "Completed" else "Scheduled"
                    st.write(f"{status_icon} {appointment[0]} - {appointment[1]} - {appointment[3]} ({status_text})")
            else:
                st.info("📝 No appointments for today")

        except Exception as e:
            st.error(f"Error loading appointments: {str(e)}")

    # Recent activity section
    st.subheader("📋 Recent Activity")

    col1, col2 = st.columns(2)

    with col1:
        # Recent patients
        try:
            recent_patients = db.execute_query("""
                SELECT name, phone, created_at 
                FROM patients 
                ORDER BY created_at DESC 
                LIMIT 5
            """)

            if recent_patients[0]:
                st.write("**👥 Recent Patients**")
                for patient in recent_patients[0]:
                    st.write(f"• {patient[0]} ({patient[1]})")
            else:
                st.info("📭 No data available")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    with col2:
        # Recent bills
        try:
            recent_bills = db.execute_query("""
                SELECT p.name, b.amount, b.payment_status 
                FROM bills b
                JOIN patients p ON b.patient_id = p.id
                ORDER BY b.created_at DESC 
                LIMIT 5
            """)

            if recent_bills[0]:
                st.write("**💰 Recent Bills**")
                for bill in recent_bills[0]:
                    status_icon = "💚" if bill[2] == "Paid" else "💔"
                    st.write(f"• {bill[0]} - ${bill[1]:,.0f} {status_icon}")
            else:
                st.info("📭 No data available")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")


def main():
    """Main application function"""
    try:
        if not auth.is_logged_in():
            show_login_page()
        else:
            show_dashboard()
    except Exception as e:
        st.error(f"System error: {str(e)}")
        st.info("Please refresh the page or contact technical support")


if __name__ == "__main__":
    main()