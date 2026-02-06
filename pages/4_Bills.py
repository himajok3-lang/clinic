import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import db
from auth import auth

st.set_page_config(page_title="Bills Management", page_icon="💰", layout="wide")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()

st.title("💰 Bills Management")

# Page tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧾 Bills List", "➕ New Bill", "💳 Payments", "📊 Financial Statistics"])

with tab1:
    st.subheader("🧾 Bills List")

    # Bills filtering
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Payment Status", ["All", "Paid", "Unpaid", "Partial"])
    with col2:
        start_date = st.date_input("From Date", value=date.today().replace(day=1))
    with col3:
        end_date = st.date_input("To Date", value=date.today())

    # Build query
    query = """
            SELECT b.id, \
                   p.name, \
                   b.amount, \
                   b.paid_amount, \
                   b.payment_status,
                   b.bill_date, \
                   b.services, \
                   b.payment_method
            FROM bills b
                     JOIN patients p ON b.patient_id = p.id
            WHERE b.bill_date BETWEEN ? AND ? \
            """
    params = [start_date, end_date]

    if filter_status != "All":
        query += " AND b.payment_status = ?"
        params.append(filter_status)

    query += " ORDER BY b.bill_date DESC"

    bills_data, columns = db.execute_query(query, params)

    if bills_data:
        df = pd.DataFrame(bills_data,
                          columns=["ID", "Patient", "Amount", "Paid", "Status", "Date", "Services", "Payment Method"])


        # Color formatting based on status
        def color_status(status):
            if status == "Paid":
                return "background-color: #d4edda; color: #155724;"
            elif status == "Unpaid":
                return "background-color: #f8d7da; color: #721c24;"
            else:
                return "background-color: #fff3cd; color: #856404;"


        styled_df = df.style.applymap(color_status, subset=["Status"])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Total amounts
        total_amount = sum(bill[2] for bill in bills_data)
        total_paid = sum(bill[3] for bill in bills_data)
        remaining = total_amount - total_paid

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Amount", f"${total_amount:,.0f}")
        with col2:
            st.metric("💵 Amount Paid", f"${total_paid:,.0f}")
        with col3:
            st.metric("📋 Amount Due", f"${remaining:,.0f}")

    else:
        st.info("📭 No bills match the search criteria")

with tab2:
    st.subheader("➕ Create New Bill")

    with st.form("add_bill_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            # Select patient
            patients_data, _ = db.execute_query("SELECT id, name, phone FROM patients ORDER BY name")
            patient_options = {f"{p[1]} ({p[2]})": p[0] for p in patients_data} if patients_data else {}
            selected_patient = st.selectbox("👥 Select Patient *",
                                            options=list(patient_options.keys())) if patient_options else st.selectbox(
                "👥 Select Patient *", [])

            # Select appointment (optional)
            appointments_data, _ = db.execute_query("""
                                                    SELECT a.id, p.name, a.appointment_date
                                                    FROM appointments a
                                                             JOIN patients p ON a.patient_id = p.id
                                                    WHERE a.status = 'Completed'
                                                    ORDER BY a.appointment_date DESC
                                                    """)
            appointment_options = {"None": None}
            if appointments_data:
                appointment_options.update({f"{a[1]} - {a[2]}": a[0] for a in appointments_data})
            selected_appointment = st.selectbox("📅 Link to Appointment (Optional)",
                                                options=list(appointment_options.keys()))

            amount = st.number_input("💵 Total Amount *", min_value=0.0, value=0.0, step=1000.0)
            paid_amount = st.number_input("💳 Amount Paid", min_value=0.0, value=0.0, step=1000.0)

        with col2:
            bill_date = st.date_input("📅 Bill Date *", value=date.today())
            payment_status = st.selectbox("🔄 Payment Status *", ["Unpaid", "Paid", "Partial"])
            payment_method = st.selectbox("💳 Payment Method", ["Cash", "Credit Card", "Bank Transfer", "Check"])
            services = st.text_area("🩺 Services Provided *", placeholder="Description of medical services provided...")

        notes = st.text_area("📝 Additional Notes", placeholder="Any additional notes about the bill...")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save Bill", use_container_width=True, type="primary")
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            if selected_patient and amount > 0 and services:
                patient_id = patient_options[selected_patient]
                appointment_id = appointment_options[selected_appointment]

                query = """
                        INSERT INTO bills (patient_id, appointment_id, amount, paid_amount,
                                           payment_status, services, payment_method, bill_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?) \
                        """
                result, error = db.execute_query(query, (
                    patient_id, appointment_id, amount, paid_amount,
                    payment_status, services, payment_method, bill_date
                ))

                if result:
                    st.success("✅ Bill created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {error}")
            else:
                st.error("❌ Please fill all required fields (*)")

with tab3:
    st.subheader("💳 Record Payments")

    # Unpaid bills
    unpaid_bills = db.execute_query("""
                                    SELECT b.id, p.name, b.amount, b.paid_amount, b.bill_date, b.services
                                    FROM bills b
                                             JOIN patients p ON b.patient_id = p.id
                                    WHERE b.payment_status != 'Paid'
                                    ORDER BY b.bill_date
                                    """)[0]

    if unpaid_bills:
        for bill in unpaid_bills:
            with st.expander(f"🧾 Bill for {bill[1]} - Amount: ${bill[2]:,.0f} - Date: {bill[4]}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Patient:** {bill[1]}")
                    st.write(f"**Total Amount:** ${bill[2]:,.0f}")
                    st.write(f"**Amount Paid:** ${bill[3]:,.0f}")
                    st.write(f"**Amount Due:** ${bill[2] - bill[3]:,.0f}")
                    st.write(f"**Services:** {bill[5]}")

                with col2:
                    with st.form(f"payment_form_{bill[0]}"):
                        payment_amount = st.number_input("💳 Payment Amount", min_value=0.0,
                                                         max_value=float(bill[2] - bill[3]),
                                                         value=float(bill[2] - bill[3]), key=f"pay_{bill[0]}")
                        payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Bank Transfer"],
                                                      key=f"method_{bill[0]}")

                        if st.form_submit_button("💳 Record Payment", use_container_width=True):
                            new_paid = bill[3] + payment_amount
                            new_status = "Paid" if new_paid >= bill[2] else "Partial"

                            update_query = """
                                           UPDATE bills
                                           SET paid_amount    = ?, \
                                               payment_status = ?, \
                                               payment_method = ?
                                           WHERE id = ? \
                                           """
                            result, error = db.execute_query(update_query,
                                                             (new_paid, new_status, payment_method, bill[0]))

                            if result:
                                st.success("✅ Payment recorded successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {error}")
    else:
        st.success("✅ No pending bills for payment")

with tab4:
    st.subheader("📊 Financial Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_bills = db.execute_query("SELECT COUNT(*) FROM bills")[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM bills")[0] else 0
        st.metric("Total Bills", total_bills)

    with col2:
        total_revenue = db.execute_query("SELECT COALESCE(SUM(amount), 0) FROM bills")[0][0][0] if \
        db.execute_query("SELECT COALESCE(SUM(amount), 0) FROM bills")[0] else 0
        st.metric("Total Revenue", f"${total_revenue:,.0f}")

    with col3:
        paid_revenue = db.execute_query("SELECT COALESCE(SUM(paid_amount), 0) FROM bills")[0][0][0] if \
        db.execute_query("SELECT COALESCE(SUM(paid_amount), 0) FROM bills")[0] else 0
        st.metric("Collected Revenue", f"${paid_revenue:,.0f}")

    with col4:
        pending_revenue = \
        db.execute_query("SELECT COALESCE(SUM(amount - paid_amount), 0) FROM bills WHERE payment_status != 'Paid'")[0][
            0][0] if \
        db.execute_query("SELECT COALESCE(SUM(amount - paid_amount), 0) FROM bills WHERE payment_status != 'Paid'")[
            0] else 0
        st.metric("Pending Amount", f"${pending_revenue:,.0f}")

    # Revenue analysis
    st.subheader("📈 Revenue Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Monthly revenue
        monthly_revenue = db.execute_query("""
                                           SELECT strftime('%Y-%m', bill_date) as month, 
                   SUM(amount) as total, 
                   SUM(paid_amount) as paid
                                           FROM bills
                                           GROUP BY month
                                           ORDER BY month DESC
                                               LIMIT 6
                                           """)[0]

        if monthly_revenue:
            revenue_df = pd.DataFrame(monthly_revenue, columns=["Month", "Total", "Collected"])
            st.bar_chart(revenue_df.set_index("Month")[["Total", "Collected"]])

    with col2:
        # Payment methods distribution
        payment_methods = db.execute_query("""
                                           SELECT payment_method, COUNT(*) as count, SUM(amount) as total
                                           FROM bills
                                           WHERE payment_method IS NOT NULL
                                           GROUP BY payment_method
                                           """)[0]

        if payment_methods:
            st.write("**💳 Payment Methods Distribution**")
            for method in payment_methods:
                st.write(f"- {method[0]}: {method[1]} bills (${method[2]:,.0f})")

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")