import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import db
from auth import auth

st.set_page_config(page_title="Medical Records", page_icon="📋", layout="wide")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()

st.title("📋 Medical Records")

# Page tabs
tab1, tab2, tab3 = st.tabs(["👥 Patient Medical Records", "➕ New Medical Record", "📊 Medical Statistics"])

with tab1:
    st.subheader("👥 Patient Medical Records")

    # Search for patient
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search Patient", placeholder="Enter patient name or phone number...")
    with col2:
        search_btn = st.button("Search", use_container_width=True)

    # Fetch patient data
    query = """
            SELECT p.id, \
                   p.name, \
                   p.phone, \
                   p.date_of_birth, \
                   p.gender, \
                   p.blood_type,
                   COUNT(mr.id)       as records_count,
                   MAX(mr.visit_date) as last_visit
            FROM patients p
                     LEFT JOIN medical_records mr ON p.id = mr.patient_id \
            """

    params = []
    if search_term:
        query += " WHERE p.name LIKE ? OR p.phone LIKE ?"
        params = [f"%{search_term}%", f"%{search_term}%"]

    query += " GROUP BY p.id ORDER BY p.name"

    patients_data, columns = db.execute_query(query, params)

    if patients_data:
        for patient in patients_data:
            with st.expander(f"👤 {patient[1]} - 📞 {patient[2]} - 📋 {patient[6]} visits"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Date of Birth:** {patient[3] or 'Not specified'}")
                    st.write(f"**Gender:** {patient[4] or 'Not specified'}")
                    st.write(f"**Blood Type:** {patient[5] or 'Not specified'}")

                with col2:
                    st.write(f"**Total Visits:** {patient[6]}")
                    st.write(f"**Last Visit:** {patient[7] or 'No visits'}")

                # Display medical records for this patient
                records_query = """
                                SELECT visit_date, diagnosis, symptoms, prescription, tests, doctor_name, notes
                                FROM medical_records
                                WHERE patient_id = ?
                                ORDER BY visit_date DESC \
                                """
                records_data, _ = db.execute_query(records_query, (patient[0],))

                if records_data:
                    for record in records_data:
                        with st.container():
                            st.markdown("---")
                            st.write(f"**📅 Visit Date:** {record[0]}")
                            st.write(f"**👨‍⚕️ Doctor:** {record[5]}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if record[1]:
                                    st.write(f"**🩺 Diagnosis:** {record[1]}")
                                if record[2]:
                                    st.write(f"**🤒 Symptoms:** {record[2]}")
                            with col2:
                                if record[3]:
                                    st.write(f"**💊 Prescription:** {record[3]}")
                                if record[4]:
                                    st.write(f"**🔬 Tests:** {record[4]}")

                            if record[6]:
                                st.write(f"**📝 Notes:** {record[6]}")
                else:
                    st.info("No medical records found for this patient")

                # Button to add new record
                if st.button(f"➕ Add Medical Record", key=f"add_record_{patient[0]}"):
                    st.session_state.selected_patient = patient[0]
                    st.session_state.patient_name = patient[1]
                    st.session_state.show_add_record = True
                    st.rerun()

with tab2:
    st.subheader("➕ Add New Medical Record")

    if st.session_state.get('show_add_record', False):
        patient_id = st.session_state.selected_patient
        patient_name = st.session_state.patient_name

        st.info(f"👤 Adding medical record for: **{patient_name}**")

        with st.form("add_medical_record_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                visit_date = st.date_input("📅 Visit Date *", value=date.today())
                doctor_name = st.text_input("👨‍⚕️ Doctor Name *", placeholder="Enter doctor name")
                diagnosis = st.text_area("🩺 Diagnosis", placeholder="Medical diagnosis...")
                symptoms = st.text_area("🤒 Symptoms", placeholder="Patient symptoms...")

            with col2:
                prescription = st.text_area("💊 Prescription", placeholder="Prescribed medications...")
                tests = st.text_area("🔬 Required Tests", placeholder="Tests and procedures...")
                notes = st.text_area("📝 Additional Notes", placeholder="Any additional notes...")

            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
            with col_btn1:
                submitted = st.form_submit_button("💾 Save Medical Record", use_container_width=True, type="primary")
            with col_btn2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            with col_btn3:
                back = st.form_submit_button("👈 Back", use_container_width=True)

            if submitted:
                if visit_date and doctor_name:
                    query = """
                            INSERT INTO medical_records (patient_id, visit_date, diagnosis, symptoms,
                                                         prescription, tests, notes, doctor_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?) \
                            """
                    result, error = db.execute_query(query, (
                        patient_id, visit_date, diagnosis, symptoms,
                        prescription, tests, notes, doctor_name
                    ))

                    if result:
                        st.success("✅ Medical record added successfully!")
                        st.session_state.show_add_record = False
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {error}")
                else:
                    st.error("❌ Please fill required fields (*)")

            if cancel or back:
                st.session_state.show_add_record = False
                st.rerun()

    else:
        st.info("👈 Please select a patient from the records list to add a new medical record")

with tab3:
    st.subheader("📊 Medical Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_records = db.execute_query("SELECT COUNT(*) FROM medical_records")[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM medical_records")[0] else 0
        st.metric("Total Records", total_records)

    with col2:
        total_patients = db.execute_query("SELECT COUNT(DISTINCT patient_id) FROM medical_records")[0][0][0] if \
        db.execute_query("SELECT COUNT(DISTINCT patient_id) FROM medical_records")[0] else 0
        st.metric("Unique Patients", total_patients)

    with col3:
        monthly_visits = db.execute_query("""
                                          SELECT COUNT(*)
                                          FROM medical_records
                                          WHERE strftime('%Y-%m', visit_date) = strftime('%Y-%m', 'now')
                                          """)[0][0][0] if db.execute_query(
            "SELECT COUNT(*) FROM medical_records WHERE strftime('%Y-%m', visit_date) = strftime('%Y-%m', 'now')")[
            0] else 0
        st.metric("Visits This Month", monthly_visits)

    with col4:
        today_visits = db.execute_query("""
                                        SELECT COUNT(*)
                                        FROM medical_records
                                        WHERE visit_date = date ('now')
                                        """)[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM medical_records WHERE visit_date = date('now')")[0] else 0
        st.metric("Visits Today", today_visits)

    # Detailed statistics
    st.subheader("📈 Detailed Statistics")

    col1, col2 = st.columns(2)

    with col1:
        # Most common diagnoses
        common_diagnoses = db.execute_query("""
                                            SELECT diagnosis, COUNT(*) as count
                                            FROM medical_records
                                            WHERE diagnosis IS NOT NULL AND diagnosis != ''
                                            GROUP BY diagnosis
                                            ORDER BY count DESC
                                                LIMIT 10
                                            """)[0]

        if common_diagnoses:
            st.write("**🩺 Most Common Diagnoses**")
            for diagnosis in common_diagnoses:
                st.write(f"- {diagnosis[0]}: {diagnosis[1]} cases")

    with col2:
        # Monthly trend
        monthly_trend = db.execute_query("""
                                         SELECT strftime('%Y-%m', visit_date) as month, COUNT(*) as count
                                         FROM medical_records
                                         GROUP BY month
                                         ORDER BY month DESC
                                             LIMIT 6
                                         """)[0]

        if monthly_trend:
            trend_df = pd.DataFrame(monthly_trend, columns=["Month", "Count"])
            st.line_chart(trend_df.set_index("Month"))

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")