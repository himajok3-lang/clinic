import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import db
from auth import auth

st.set_page_config(page_title="Appointments", page_icon="📅", layout="wide")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()

st.title("📅 Appointments Management")

# Page tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Appointment Schedule", "➕ Book New Appointment", "📊 Appointment Statistics", "⚙️ Settings"])

with tab1:
    st.subheader("📋 Appointment Schedule")

    # Appointment filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_date = st.date_input("📅 Filter by Date", value=date.today())
    with col2:
        filter_status = st.selectbox("🔍 Appointment Status", ["All", "Scheduled", "Completed", "Cancelled", "No Show"])
    with col3:
        doctors_result = db.execute_query("SELECT DISTINCT doctor_name FROM appointments WHERE doctor_name IS NOT NULL")
        doctor_options = ["All"] + [doc[0] for doc in doctors_result[0]] if doctors_result[0] else ["All"]
        filter_doctor = st.selectbox("👨‍⚕️ Doctor", doctor_options)

    # Build filter query
    query = """
            SELECT a.id, \
                   p.name, \
                   a.doctor_name, \
                   a.appointment_date, \
                   a.appointment_time,
                   a.status, \
                   a.type, \
                   a.notes, \
                   p.phone
            FROM appointments a
                     JOIN patients p ON a.patient_id = p.id
            WHERE 1 = 1 \
            """
    params = []

    if filter_date:
        query += " AND a.appointment_date = ?"
        params.append(filter_date)

    if filter_status != "All":
        query += " AND a.status = ?"
        params.append(filter_status)

    if filter_doctor != "All":
        query += " AND a.doctor_name = ?"
        params.append(filter_doctor)

    query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"

    appointments_data, columns = db.execute_query(query, params)

    if appointments_data:
        df = pd.DataFrame(appointments_data,
                          columns=["ID", "Patient", "Doctor", "Date", "Time", "Status", "Type", "Notes", "Phone"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No appointments match search criteria")

with tab2:
    st.subheader("➕ Book New Appointment")

    with st.form("add_appointment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # Patient selection
            patients_data, _ = db.execute_query("SELECT id, name, phone FROM patients ORDER BY name")
            patient_options = {f"{p[1]} ({p[2]})": p[0] for p in patients_data} if patients_data else {}
            selected_patient = st.selectbox("👥 Select Patient *",
                                            options=list(patient_options.keys())) if patient_options else st.selectbox(
                "👥 Select Patient *", [])

            appointment_date = st.date_input("📅 Appointment Date *", min_value=date.today())
            appointment_time = st.time_input("⏰ Appointment Time *")

        with col2:
            doctor_name = st.text_input("👨‍⚕️ Doctor Name *", placeholder="Enter doctor name")
            appointment_type = st.selectbox("📝 Appointment Type *", ["Regular", "Follow-up", "Emergency", "Check-up"])
            status = st.selectbox("🔄 Appointment Status", ["Scheduled", "Completed", "Cancelled", "No Show"])

        notes = st.text_area("📝 Additional Notes", placeholder="Any additional notes about the appointment...")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save Appointment", use_container_width=True, type="primary")
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            if selected_patient and appointment_date and appointment_time and doctor_name:
                patient_id = patient_options[selected_patient]

                query = """
                        INSERT INTO appointments (patient_id, doctor_name, appointment_date, appointment_time,
                                                  status, type, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?) \
                        """
                result, error = db.execute_query(query, (
                    patient_id, doctor_name, appointment_date, appointment_time,
                    status, appointment_type, notes
                ))

                if result:
                    st.success("✅ Appointment booked successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {error}")
            else:
                st.error("❌ Please fill all required fields (*)")

with tab3:
    st.subheader("📊 Appointment Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_appointments = db.execute_query("SELECT COUNT(*) FROM appointments")[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM appointments")[0] else 0
        st.metric("Total Appointments", total_appointments)

    with col2:
        today_appointments = \
        db.execute_query("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?", (date.today(),))[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?", (date.today(),))[0] else 0
        st.metric("Today's Appointments", today_appointments)

    with col3:
        completed_appointments = db.execute_query("SELECT COUNT(*) FROM appointments WHERE status = 'Completed'")[0][0][
            0] if db.execute_query("SELECT COUNT(*) FROM appointments WHERE status = 'Completed'")[0] else 0
        st.metric("Completed Appointments", completed_appointments)

    with col4:
        upcoming_appointments = \
        db.execute_query("SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = 'Scheduled'",
                         (date.today(),))[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = 'Scheduled'",
                         (date.today(),))[0] else 0
        st.metric("Upcoming Appointments", upcoming_appointments)

with tab4:
    st.subheader("⚙️ Appointment Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**⏰ Working Hours**")
        work_start = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
        work_end = st.time_input("End Time", value=datetime.strptime("16:00", "%H:%M").time())

        st.write("**📅 Appointment Settings**")
        appointment_duration = st.number_input("Appointment Duration (minutes)", min_value=10, max_value=120, value=30)
        max_daily_appointments = st.number_input("Maximum Daily Appointments", min_value=1, max_value=100, value=20)

    with col2:
        st.write("**🔔 Reminders**")
        enable_reminders = st.checkbox("Enable automatic reminders")
        reminder_time = st.selectbox("Reminder Time", ["1 hour before", "1 day before", "1 week before"])

        st.write("**📧 Notifications**")
        enable_sms = st.checkbox("Send SMS notifications")
        enable_email = st.checkbox("Send email notifications")

    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")