import hashlib
import streamlit as st
from database import db


class AuthManager:
    def __init__(self):
        self.current_user = None

    def hash_password(self, password):
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        """User login"""
        try:
            query = "SELECT * FROM users WHERE username = ? AND is_active = 1"
            result = db.execute_query(query, (username,))

            if result and len(result[0]) > 0:
                user_data = result[0][0]
                columns = result[1]
                user_dict = dict(zip(columns, user_data))

                if user_dict['password_hash'] == self.hash_password(password):
                    self.current_user = user_dict

                    # Save to session state
                    st.session_state.user = user_dict
                    st.session_state.logged_in = True

                    return True, "Login successful"

            return False, "Invalid username or password"

        except Exception as e:
            return False, f"System error: {str(e)}"

    def logout(self):
        """User logout"""
        self.current_user = None
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.clear()

    def is_logged_in(self):
        """Check login status"""
        return st.session_state.get('logged_in', False)

    def get_current_user(self):
        """Get current user data"""
        return st.session_state.get('user', None)


# Global instance of auth manager
auth = AuthManager()