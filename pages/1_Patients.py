import streamlit as st
import pandas as pd
from database import db
from auth import auth

st.set_page_config(page_title="Patients Management", page_icon="👥")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()

st.title("👥 Patients Management")

# Add new patient button
if st.button("➕ Add New Patient", type="primary"):
    st.session_state.show_add_patient = True

# Add patient form
if st.session_state.get('show_add_patient', False):
    with st.form("add_patient_form", clear_on_submit=True):
        st.subheader("Patient Information")

        col1, col2 = st.columns(2)

        with col1:
            national_id = st.text_input("🆔 National ID*")
            name = st.text_input("👤 Full Name*")
            phone = st.text_input("📞 Phone Number*")
            email = st.text_input("📧 Email")

        with col2:
            date_of_birth = st.date_input("📅 Date of Birth")
            gender = st.selectbox("⚧ Gender", ["", "Male", "Female"])
            blood_type = st.selectbox("🩸 Blood Type", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

        address = st.text_area("🏠 Address")
        emergency_contact = st.text_input("🚨 Emergency Contact")
        allergies = st.text_area("⚠️ Allergies")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save Patient", use_container_width=True)
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            if national_id and name and phone:
                query = """
                INSERT INTO patients (national_id, name, phone, email, date_of_birth,
                                      gender, address, emergency_contact, blood_type, allergies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                result, error = db.execute_query(query, (
                    national_id, name, phone, email, date_of_birth,
                    gender, address, emergency_contact, blood_type, allergies
                ))
                if result:
                    st.success("✅ Patient added successfully!")
                    st.session_state.show_add_patient = False
                    st.rerun()
                else:
                    st.error(f"❌ Error: {error}")
            else:
                st.error("❌ Please fill required fields (*)")

        if cancel:
            st.session_state.show_add_patient = False
            st.rerun()

# Search bar
st.subheader("🔍 Search Patients")
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search_term = st.text_input("Search by name or phone", placeholder="Enter patient name or phone number...")
with search_col2:
    if st.button("Search", use_container_width=True):
        st.session_state.patient_search = search_term

# Patients list
st.subheader("📋 Patients List")

# Build query
query = """
SELECT id, national_id, name, phone, email, date_of_birth,
       gender, address, emergency_contact, blood_type, allergies, created_at
FROM patients
"""
params = ()

if st.session_state.get('patient_search'):
    query += " WHERE name LIKE ? OR phone LIKE ? OR national_id LIKE ?"
    params = (f"%{st.session_state.patient_search}%",
              f"%{st.session_state.patient_search}%",
              f"%{st.session_state.patient_search}%")

query += " ORDER BY created_at DESC"

# Fetch data
patients_data, columns = db.execute_query(query, params)

if patients_data:
    # Convert to DataFrame
    patients_df = pd.DataFrame(patients_data, columns=columns)

    # Display data in interactive table
    st.dataframe(
        patients_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "national_id": "National ID",
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
            "date_of_birth": "Date of Birth",
            "gender": "Gender",
            "blood_type": "Blood Type"
        }
    )

    # Statistics
    st.subheader("📊 Patient Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total_patients = len(patients_data)
    male_count = len([p for p in patients_data if p[6] == 'Male'])
    female_count = len([p for p in patients_data if p[6] == 'Female'])

    with col1:
        st.metric("Total Patients", total_patients)
    with col2:
        st.metric("Male", male_count)
    with col3:
        st.metric("Female", female_count)
    with col4:
        from datetime import datetime
        today_count = len([p for p in patients_data if p[11].split()[0] == str(datetime.now().date())])
        st.metric("New Patients Today", today_count)

else:
    st.info("📭 No patient data available")

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")