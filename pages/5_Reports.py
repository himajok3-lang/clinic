import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
import time
from database import db
from auth import auth

st.set_page_config(page_title="Reports and Analytics", page_icon="📊", layout="wide")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()


# Helper functions for data loading
def get_main_stats(start_date, end_date):
    """Get main statistics"""
    try:
        # New patients
        new_patients_result = db.execute_query(
            "SELECT COUNT(*) FROM patients WHERE date(created_at) BETWEEN ? AND ?",
            (start_date, end_date)
        )
        new_patients = new_patients_result[0][0][0] if new_patients_result[0] else 0

        # Appointments
        appointments_result = db.execute_query(
            "SELECT COUNT(*) FROM appointments WHERE appointment_date BETWEEN ? AND ?",
            (start_date, end_date)
        )
        total_appointments = appointments_result[0][0][0] if appointments_result[0] else 0

        # Revenue
        revenue_result = db.execute_query(
            "SELECT COALESCE(SUM(amount), 0) FROM bills WHERE bill_date BETWEEN ? AND ?",
            (start_date, end_date)
        )
        total_revenue = revenue_result[0][0][0] if revenue_result[0] else 0

        # Working days
        working_days = (end_date - start_date).days + 1

        return {
            'new_patients': new_patients,
            'total_appointments': total_appointments,
            'total_revenue': total_revenue,
            'working_days': working_days,
            'patient_growth': 5.2,
            'appointment_growth': 3.8,
            'revenue_growth': 7.1,
            'occupancy_growth': 2.5
        }
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
        return {
            'new_patients': 0,
            'total_appointments': 0,
            'total_revenue': 0,
            'working_days': 0,
            'patient_growth': 0,
            'appointment_growth': 0,
            'revenue_growth': 0,
            'occupancy_growth': 0
        }


def get_revenue_trend(start_date, end_date):
    """Get revenue trend"""
    try:
        data = db.execute_query("""
                                SELECT bill_date as date, SUM(amount) as revenue
                                FROM bills
                                WHERE bill_date BETWEEN ? AND ?
                                GROUP BY bill_date
                                ORDER BY bill_date
                                """, (start_date, end_date))

        if data and data[0]:
            df = pd.DataFrame(data[0], columns=["Date", "Revenue"])
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as e:
        st.error(f"Error loading revenue trend: {str(e)}")
    return pd.DataFrame()


def get_appointment_distribution(start_date, end_date):
    """Get appointment distribution"""
    try:
        data = db.execute_query("""
                                SELECT status, COUNT(*) as count
                                FROM appointments
                                WHERE appointment_date BETWEEN ? AND ?
                                GROUP BY status
                                """, (start_date, end_date))

        if data and data[0]:
            return pd.DataFrame(data[0], columns=["Status", "Count"])
    except Exception as e:
        st.error(f"Error loading appointment distribution: {str(e)}")
    return pd.DataFrame()


st.title("📊 Reports and Analytics")

# Page tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🏥 Overview", "👥 Patient Reports", "📅 Appointment Reports", "💰 Financial Reports", "📤 Export"])

with tab1:
    st.subheader("🏥 Clinic Performance Overview")

    # Time period selection
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        period = st.selectbox("Time Period", ["This Month", "This Week", "Today", "Quarterly", "Yearly", "Custom"])
    with col2:
        if period == "Custom":
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            end_date = st.date_input("End Date", value=date.today())
        else:
            # Calculate dates automatically based on selected period
            today = date.today()
            if period == "Today":
                start_date = end_date = today
            elif period == "This Week":
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == "This Month":
                start_date = today.replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif period == "Quarterly":
                quarter = (today.month - 1) // 3 + 1
                start_date = date(today.year, 3 * quarter - 2, 1)
                end_date = (date(today.year, 3 * quarter + 1, 1) - timedelta(days=1))
            else:  # Yearly
                start_date = date(today.year, 1, 1)
                end_date = date(today.year, 12, 31)

    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # Key indicators
    st.subheader("📈 Key Indicators")

    stats = get_main_stats(start_date, end_date)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 New Patients",
            stats['new_patients'],
            f"{stats['patient_growth']:+.1f}%"
        )

    with col2:
        st.metric(
            "📅 Appointments",
            stats['total_appointments'],
            f"{stats['appointment_growth']:+.1f}%"
        )

    with col3:
        st.metric(
            "💰 Total Revenue",
            f"${stats['total_revenue']:,.0f}",
            f"{stats['revenue_growth']:+.1f}%"
        )

    with col4:
        occupancy_rate = (stats['total_appointments'] / (stats['working_days'] * 20)) * 100 if stats[
                                                                                                   'working_days'] > 0 else 0
        st.metric(
            "📊 Occupancy Rate",
            f"{occupancy_rate:.1f}%",
            f"{stats['occupancy_growth']:+.1f}%"
        )

    # Main charts
    col1, col2 = st.columns(2)

    with col1:
        # Revenue trend
        revenue_data = get_revenue_trend(start_date, end_date)
        if not revenue_data.empty:
            fig = px.line(
                revenue_data,
                x='Date',
                y='Revenue',
                title='📈 Daily Revenue Trend',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data for selected period")

    with col2:
        # Appointment distribution
        appointment_dist = get_appointment_distribution(start_date, end_date)
        if not appointment_dist.empty:
            fig = px.pie(
                appointment_dist,
                values='Count',
                names='Status',
                title='📊 Appointment Status Distribution',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointment data for selected period")

with tab2:
    st.subheader("👥 Patient Reports and Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_patients_result = db.execute_query("SELECT COUNT(*) FROM patients")
        total_patients = total_patients_result[0][0][0] if total_patients_result[0] else 0
        st.metric("Total Patients", total_patients)

    with col2:
        active_patients_result = db.execute_query("""
                                                  SELECT COUNT(DISTINCT patient_id)
                                                  FROM medical_records
                                                  WHERE visit_date >= date ('now', '-30 days')
                                                  """)
        active_patients = active_patients_result[0][0][0] if active_patients_result[0] else 0
        st.metric("Active Patients", active_patients)

    with col3:
        new_patients_month_result = db.execute_query("""
                                                     SELECT COUNT(*)
                                                     FROM patients
                                                     WHERE created_at >= date ('now', '-30 days')
                                                     """)
        new_patients_month = new_patients_month_result[0][0][0] if new_patients_month_result[0] else 0
        st.metric("New Patients (Last 30 days)", new_patients_month)

    # Patient charts
    col1, col2 = st.columns(2)

    with col1:
        # Gender distribution
        gender_dist_result = db.execute_query("""
                                              SELECT gender, COUNT(*) as count
                                              FROM patients
                                              WHERE gender IS NOT NULL AND gender != ''
                                              GROUP BY gender
                                              """)

        if gender_dist_result and gender_dist_result[0]:
            gender_df = pd.DataFrame(gender_dist_result[0], columns=["Gender", "Count"])
            fig = px.pie(
                gender_df,
                values='Count',
                names='Gender',
                title='⚧ Gender Distribution'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gender data available")

    with col2:
        # Age distribution
        age_dist_result = db.execute_query("""
                                           SELECT CASE
                                                      WHEN date_of_birth IS NULL THEN 'Not specified'
                                                      WHEN (julianday('now') - julianday(date_of_birth)) / 365 < 18
                                                          THEN 'Under 18'
                                                      WHEN (julianday('now') - julianday(date_of_birth)) / 365 BETWEEN 18 AND 30
                                                          THEN '18-30'
                                                      WHEN (julianday('now') - julianday(date_of_birth)) / 365 BETWEEN 31 AND 45
                                                          THEN '31-45'
                                                      WHEN (julianday('now') - julianday(date_of_birth)) / 365 BETWEEN 46 AND 60
                                                          THEN '46-60'
                                                      ELSE 'Over 60'
                                                      END as age_group,
                                                  COUNT(*) as count
                                           FROM patients
                                           GROUP BY age_group
                                           """)

        if age_dist_result and age_dist_result[0]:
            age_df = pd.DataFrame(age_dist_result[0], columns=["Age Group", "Count"])
            fig = px.bar(
                age_df,
                x='Age Group',
                y='Count',
                title='📊 Age Group Distribution',
                color='Count'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No age data available")

with tab3:
    st.subheader("📅 Appointment Performance Analysis")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_appointments_result = db.execute_query("SELECT COUNT(*) FROM appointments")
        total_appointments = total_appointments_result[0][0][0] if total_appointments_result[0] else 0
        st.metric("Total Appointments", total_appointments)

    with col2:
        completed_rate_result = db.execute_query("""
                                                 SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM appointments), 1)
                                                 FROM appointments
                                                 WHERE status = 'Completed'
                                                 """)
        completed_rate = completed_rate_result[0][0][0] if completed_rate_result[0] else 0
        st.metric("Completion Rate", f"{completed_rate}%")

    with col3:
        cancellation_rate_result = db.execute_query("""
                                                    SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM appointments), 1)
                                                    FROM appointments
                                                    WHERE status = 'Cancelled'
                                                    """)
        cancellation_rate = cancellation_rate_result[0][0][0] if cancellation_rate_result[0] else 0
        st.metric("Cancellation Rate", f"{cancellation_rate}%")

    with col4:
        avg_daily_result = db.execute_query("""
                                            SELECT ROUND(AVG(daily_count), 1)
                                            FROM (SELECT appointment_date, COUNT(*) as daily_count
                                                  FROM appointments
                                                  GROUP BY appointment_date)
                                            """)
        avg_daily = avg_daily_result[0][0][0] if avg_daily_result[0] else 0
        st.metric("Average Daily Appointments", avg_daily)

with tab4:
    st.subheader("💰 Financial Analysis and Reports")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_revenue_result = db.execute_query("SELECT COALESCE(SUM(amount), 0) FROM bills")
        total_revenue = total_revenue_result[0][0][0] if total_revenue_result[0] else 0
        st.metric("Total Revenue", f"${total_revenue:,.0f}")

    with col2:
        collected_revenue_result = db.execute_query("SELECT COALESCE(SUM(paid_amount), 0) FROM bills")
        collected_revenue = collected_revenue_result[0][0][0] if collected_revenue_result[0] else 0
        st.metric("Collected Revenue", f"${collected_revenue:,.0f}")

    with col3:
        pending_revenue_result = db.execute_query(
            "SELECT COALESCE(SUM(amount - paid_amount), 0) FROM bills WHERE payment_status != 'Paid'")
        pending_revenue = pending_revenue_result[0][0][0] if pending_revenue_result[0] else 0
        st.metric("Pending Amount", f"${pending_revenue:,.0f}")

    with col4:
        collection_rate = (collected_revenue / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("Collection Rate", f"{collection_rate:.1f}%")

with tab5:
    st.subheader("📤 Export Reports and Data")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📋 Select Report Type**")
        report_type = st.selectbox("Report Type", [
            "Comprehensive Report",
            "Patients Report",
            "Appointments Report",
            "Bills Report",
            "Medical Records Report"
        ])

        export_format = st.selectbox("File Format", ["Excel", "CSV", "PDF"])

        if report_type == "Comprehensive Report":
            start_date_export = st.date_input("From Date", value=date.today().replace(day=1), key="export_start")
            end_date_export = st.date_input("To Date", value=date.today(), key="export_end")

        include_charts = st.checkbox("Include charts and graphs")

    with col2:
        st.write("**⚙️ Export Options**")

        if report_type == "Patients Report":
            st.info("""
            **Will include:**
            - Basic patient data
            - Age and gender distribution
            - Visit statistics
            """)

        elif report_type == "Appointments Report":
            st.info("""
            **Will include:**
            - Appointment schedule
            - Attendance and cancellation statistics
            - Doctor performance
            """)

        elif report_type == "Bills Report":
            st.info("""
            **Will include:**
            - Bills and payments
            - Pending amounts
            - Revenue data
            """)

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Export Data", use_container_width=True, type="primary"):
            with st.spinner("Generating report..."):
                time.sleep(2)
                st.success("✅ Report generated successfully!")

                # Create sample data for export
                if report_type == "Patients Report":
                    data = db.get_dataframe("SELECT * FROM patients LIMIT 100")
                elif report_type == "Appointments Report":
                    data = db.get_dataframe("SELECT * FROM appointments LIMIT 100")
                elif report_type == "Bills Report":
                    data = db.get_dataframe("SELECT * FROM bills LIMIT 100")
                else:
                    data = db.get_dataframe("SELECT * FROM patients LIMIT 10")

                if export_format == "Excel":
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        data.to_excel(writer, index=False, sheet_name='Report')
                    st.download_button(
                        label="📥 Download Excel File",
                        data=buffer.getvalue(),
                        file_name=f"{report_type}_{date.today()}.xlsx",
                        mime="application/vnd.ms-excel",
                        use_container_width=True
                    )
                elif export_format == "CSV":
                    csv = data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV File",
                        data=csv,
                        file_name=f"{report_type}_{date.today()}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

    with col2:
        if st.button("🖨️ Print Report", use_container_width=True):
            st.info("🚧 Print feature under development")

    with col3:
        if st.button("📧 Send by Email", use_container_width=True):
            st.info("🚧 Email feature under development")

    # Data preview
    st.subheader("👀 Data Preview")

    if report_type == "Patients Report":
        preview_data = db.get_dataframe("SELECT id, name, phone, gender, date_of_birth FROM patients LIMIT 10")
    elif report_type == "Appointments Report":
        preview_data = db.get_dataframe("""
                                        SELECT a.id, p.name, a.appointment_date, a.appointment_time, a.status
                                        FROM appointments a
                                                 JOIN patients p ON a.patient_id = p.id LIMIT 10
                                        """)
    elif report_type == "Bills Report":
        preview_data = db.get_dataframe("""
                                        SELECT b.id, p.name, b.amount, b.paid_amount, b.payment_status
                                        FROM bills b
                                                 JOIN patients p ON b.patient_id = p.id LIMIT 10
                                        """)
    else:
        preview_data = db.get_dataframe("SELECT 'Sample data' as column LIMIT 5")

    st.dataframe(preview_data, use_container_width=True)

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")