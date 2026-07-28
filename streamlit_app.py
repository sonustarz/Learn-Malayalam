import streamlit as st

# 1. Mock Database (In a real app, this would be Firebase, SQL, etc.)
# It currently contains one user: "Learner123"
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "Learner123": {"history": [0, 1, 2], "current_step": 3}
    }

st.title("Welcome to Flash-Learn 📇")

# 2. Create Tabs for Login vs. Sign Up
tab1, tab2 = st.tabs(["Login", "Sign Up"])

# --- SIGN UP PATH ---
with tab2:
    st.subheader("Create a New Account")
    new_username = st.text_input("Choose a Username", key="new_user")
    
    if st.button("Register"):
        if new_username == "":
            st.warning("Username cannot be empty.")
        # THE CHECK: Does the username already exist in the database?
        elif new_username in st.session_state.user_db:
            # THE PROMPT: Force them to choose another
            st.error(f"⚠️ The username '{new_username}' is already taken. Please choose a different one.")
        else:
            # THE CREATION: Save the new unique user to the database
            st.session_state.user_db[new_username] = {"history": [0], "current_step": 0}
            st.success(f"Account '{new_username}' created successfully! You can now log in.")

# --- LOGIN PATH ---
with tab1:
    st.subheader("Welcome Back")
    login_username = st.text_input("Enter your Username", key="login_user")
    
    if st.button("Log In"):
        if login_username in st.session_state.user_db:
            st.success(f"Logged in as {login_username}. Loading your progress...")
            # Here you would load their specific history array into the session state
        else:
            st.error("Username not found. Please check your spelling or sign up.")
