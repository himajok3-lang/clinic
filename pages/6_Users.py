import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
from database import db
from auth import auth

st.set_page_config(page_title="Users Management", page_icon="👤", layout="wide")

if not auth.is_logged_in():
    st.warning("⚠️ Please log in first")
    st.stop()

# Check user permissions
if st.session_state.user['role'] != 'admin':
    st.error("⛔ You don't have permission to access this page")
    st.stop()

st.title("👤 Users Management")

# Page tabs
tab1, tab2, tab3 = st.tabs(["📋 Users List", "➕ New User", "📊 User Permissions"])

with tab1:
    st.subheader("📋 Users List")

    # Fetch users data
    users_data, columns = db.execute_query("""
                                           SELECT id,
                                                  username,
                                                  full_name,
                                                  role,
                                                  email,
                                                  phone,
                                                  is_active,
                                                  created_at
                                           FROM users
                                           ORDER BY created_at DESC
                                           """)

    if users_data:
        df = pd.DataFrame(users_data,
                          columns=["ID", "Username", "Full Name", "Role", "Email", "Phone", "Active", "Created At"])


        # Format user status
        def color_status(status):
            return "background-color: #d4edda; color: #155724;" if status else "background-color: #f8d7da; color: #721c24;"


        styled_df = df.style.applymap(color_status, subset=["Active"])

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # Quick actions
        st.subheader("🛠️ User Management")
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_user = st.selectbox("Select User", [f"{user[1]} - {user[2]}" for user in users_data])
            user_id = [user[0] for user in users_data if f"{user[1]} - {user[2]}" == selected_user][0]

        with col2:
            action = st.selectbox("Action", ["Activate/Deactivate", "Reset Password", "Edit Data"])

        with col3:
            if st.button("Apply Action", use_container_width=True):
                if action == "Activate/Deactivate":
                    current_status = [user[6] for user in users_data if user[0] == user_id][0]
                    new_status = 0 if current_status else 1
                    result, error = db.execute_query("UPDATE users SET is_active = ? WHERE id = ?",
                                                     (new_status, user_id))
                    if result:
                        st.success("✅ User status updated successfully!")
                        st.rerun()

                elif action == "Reset Password":
                    default_password = hashlib.sha256("123456".encode()).hexdigest()
                    result, error = db.execute_query("UPDATE users SET password_hash = ? WHERE id = ?",
                                                     (default_password, user_id))
                    if result:
                        st.success("✅ Password reset to 123456")

                elif action == "Edit Data":
                    st.session_state.edit_user_id = user_id
                    st.session_state.show_edit_form = True
                    st.rerun()

    else:
        st.info("📭 No users registered")

with tab2:
    st.subheader("➕ Add New User")

    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("👤 Username *", placeholder="Enter unique username")
            full_name = st.text_input("📛 Full Name *", placeholder="User's full name")
            email = st.text_input("📧 Email", placeholder="user@example.com")
            phone = st.text_input("📞 Phone", placeholder="Phone number")

        with col2:
            role = st.selectbox("🎭 Role *", ["admin", "doctor", "reception", "nurse"])
            password = st.text_input("🔒 Password *", type="password", placeholder="Password")
            confirm_password = st.text_input("🔒 Confirm Password *", type="password", placeholder="Confirm password")
            is_active = st.checkbox("✅ Active Account", value=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save User", use_container_width=True, type="primary")
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            if username and full_name and role and password:
                if password == confirm_password:
                    # Check if username already exists
                    existing_user = db.execute_query("SELECT id FROM users WHERE username = ?", (username,))
                    if existing_user and existing_user[0]:
                        st.error("❌ Username already exists, please choose another")
                    else:
                        password_hash = hashlib.sha256(password.encode()).hexdigest()

                        query = """
                                INSERT INTO users (username, password_hash, full_name, role, email, phone, is_active)
                                VALUES (?, ?, ?, ?, ?, ?, ?) \
                                """
                        result, error = db.execute_query(query, (
                            username, password_hash, full_name, role, email, phone, 1 if is_active else 0
                        ))

                        if result:
                            st.success("✅ User added successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {error}")
                else:
                    st.error("❌ Passwords do not match")
            else:
                st.error("❌ Please fill all required fields (*)")

with tab3:
    st.subheader("📊 User Permissions")

    # Define roles and permissions
    st.write("**🎭 Roles and Permissions Definition:**")

    roles_permissions = {
        "admin": {
            "description": "System Administrator - Full permissions",
            "permissions": ["Manage users", "Manage all data", "Reports and analytics", "System settings"]
        },
        "doctor": {
            "description": "Doctor - Medical permissions",
            "permissions": ["Manage patients", "Medical records", "Appointments", "Medical reports"]
        },
        "reception": {
            "description": "Receptionist - Limited permissions",
            "permissions": ["Manage patients", "Appointments", "Bills", "Basic reports"]
        },
        "nurse": {
            "description": "Nurse - Assistant permissions",
            "permissions": ["View patients", "Medical records (read only)", "Assist with appointments"]
        }
    }

    col1, col2 = st.columns(2)

    with col1:
        selected_role = st.selectbox("Select Role", list(roles_permissions.keys()))

        st.write(f"**Role Description:** {roles_permissions[selected_role]['description']}")
        st.write("**Permissions:**")
        for permission in roles_permissions[selected_role]['permissions']:
            st.write(f"✅ {permission}")

    with col2:
        st.write("**📈 User Distribution by Role:**")
        role_distribution = db.execute_query("""
                                             SELECT role, COUNT(*) as count
                                             FROM users
                                             WHERE is_active = 1
                                             GROUP BY role
                                             """)[0]

        if role_distribution:
            role_df = pd.DataFrame(role_distribution, columns=["Role", "Count"])
            st.bar_chart(role_df.set_index("Role"))

    # User activity statistics
    st.subheader("📈 User Activity")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_users = db.execute_query("SELECT COUNT(*) FROM users")[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM users")[0] else 0
        st.metric("Total Users", total_users)

    with col2:
        active_users = db.execute_query("SELECT COUNT(*) FROM users WHERE is_active = 1")[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM users WHERE is_active = 1")[0] else 0
        st.metric("Active Users", active_users)

    with col3:
        new_users_month = db.execute_query("""
                                           SELECT COUNT(*)
                                           FROM users
                                           WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
                                           """)[0][0][0] if \
        db.execute_query("SELECT COUNT(*) FROM users WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')")[
            0] else 0
        st.metric("New Users This Month", new_users_month)

# Edit user form
if st.session_state.get('show_edit_form', False):
    st.subheader("✏️ Edit User Data")

    user_id = st.session_state.edit_user_id
    user_data = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))[0][0]

    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("👤 Username", value=user_data[1])
            full_name = st.text_input("📛 Full Name", value=user_data[3])
            email = st.text_input("📧 Email", value=user_data[5] or "")

        with col2:
            phone = st.text_input("📞 Phone", value=user_data[6] or "")
            role = st.selectbox("🎭 Role", ["admin", "doctor", "reception", "nurse"],
                                index=["admin", "doctor", "reception", "nurse"].index(user_data[4]))
            is_active = st.checkbox("✅ Active Account", value=bool(user_data[7]))

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        with col_btn2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            query = """
                    UPDATE users
                    SET username  = ?, \
                        full_name = ?, \
                        role      = ?, \
                        email     = ?, \
                        phone     = ?, \
                        is_active = ?
                    WHERE id = ? \
                    """
            result, error = db.execute_query(query,
                                             (username, full_name, role, email, phone, 1 if is_active else 0, user_id))

            if result:
                st.success("✅ User data updated successfully!")
                st.session_state.show_edit_form = False
                st.rerun()

        if cancel:
            st.session_state.show_edit_form = False
            st.rerun()

# Back to dashboard button
if st.button("🏠 Back to Dashboard"):
    st.switch_page("app.py")