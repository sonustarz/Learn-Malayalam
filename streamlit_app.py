import streamlit as st
import io
import requests
import base64
import random
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------
# 1. PAGE SETUP & FIREBASE INITIALIZATION
# ---------------------------------------------------------
st.set_page_config(page_title="Malayalam Flashcards", page_icon="📇", layout="centered")

# Initialize Firebase only once
if not firebase_admin._apps:
    try:
        key_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("Firebase setup failed. Check your Streamlit secrets.")

db = firestore.client()

# ---------------------------------------------------------
# 2. SARVAM AI INTEGRATION (Translation & Audio)
# ---------------------------------------------------------
def generate_audio(text, lang='ml-IN'):
    """Calls Sarvam AI TTS API and returns a playable WAV audio file."""
    url = "https://api.sarvam.ai/text-to-speech"
    payload = {
        "text": text,
        "target_language_code": lang,
        "model": "bulbul:v3",
        "speaker": "ritu" # You can change this to "shubh" for a male voice
    }
    headers = {
        "api-subscription-key": st.secrets["sarvam"]["api_key"],
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_base64 = response.json().get("audios", [])[0]
            audio_bytes = base64.b64decode(audio_base64)
            return io.BytesIO(audio_bytes)
        else:
            st.error(f"Sarvam Audio API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error("Failed to connect to Sarvam AI for audio.")
        return None

def translate_to_malayalam(english_text):
    """Calls Sarvam AI API to translate English to modern spoken Malayalam."""
    url = "https://api.sarvam.ai/translate"
    payload = {
        "input": english_text,
        "source_language_code": "en-IN",
        "target_language_code": "ml-IN",
        "speaker_gender": "Female",
        "mode": "modern-colloquial", # Ensures it doesn't sound like a textbook
        "model": "mayura:v1"
    }
    headers = {
        "api-subscription-key": st.secrets["sarvam"]["api_key"],
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("translated_text", "Error extracting text.")
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return "Translation failed. Check connection."

# ---------------------------------------------------------
# 3. BASE FLASHCARD DATA
# ---------------------------------------------------------
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = [
        {"english": "Hello", "malayalam": "Namaskaram", "spoken": "Namaskaram"},
        {"english": "How are you?", "malayalam": "Sukhamaano?", "spoken": "Sukhamaano?"},
        {"english": "I am fine", "malayalam": "Enikku sukhamaanu", "spoken": "Enikku sukhamaanu"},
        {"english": "Where are you going?", "malayalam": "Evidekka pokunne?", "spoken": "Evidekka pokunne?"},
        {"english": "I want water", "malayalam": "Enikku vellam venam", "spoken": "Enikku vellam venam"},
        {"english": "I don't understand", "malayalam": "Manassilayilla", "spoken": "Manassilayilla"},
        {"english": "Speak slowly", "malayalam": "Pathukke parayu", "spoken": "Pathukke parayu"},
        {"english": "How much is this?", "malayalam": "Ithinu ethraya?", "spoken": "Ithinu ethraya?"},
        {"english": "Reduce the price", "malayalam": "Vila kurakku", "spoken": "Vila kurakku"},
        {"english": "Stop here", "malayalam": "Ivide nirthu", "spoken": "Ivide nirthu"},
        {"english": "Auto charge how much?", "malayalam": "Auto charge ethraya?", "spoken": "Auto charge ethraya?"}
        # Note: You can paste the rest of the 100 cards from earlier here!
    ]

# ---------------------------------------------------------
# 4. SESSION STATE & DATABASE HELPERS
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'show_translation' not in st.session_state:
    st.session_state.show_translation = False

def save_progress():
    """Writes the current progress to Firebase for the logged-in user."""
    db.collection("users").document(st.session_state.username).set({
        "history": st.session_state.history,
        "current_step": st.session_state.current_step
    }, merge=True)

# ---------------------------------------------------------
# 5. APP LOGIC: NAVIGATION & SPACED REPETITION
# ---------------------------------------------------------
def next_card():
    st.session_state.show_translation = False
    
    # Moving forward through already visited history
    if st.session_state.current_step < len(st.session_state.history) - 1:
        st.session_state.current_step += 1
    else:
        # User is at the end of history, generate a new or review card
        seen_indices = list(set(st.session_state.history))
        all_indices = list(range(len(st.session_state.flashcards)))
        unseen_indices = [i for i in all_indices if i not in seen_indices]
        
        # Spaced Repetition: Every 4th card, review a random previously seen card
        if len(st.session_state.history) % 4 == 0 and len(seen_indices) > 0:
            next_idx = random.choice(seen_indices)
        else:
            if unseen_indices:
                next_idx = unseen_indices[0] 
            else:
                next_idx = random.choice(seen_indices) 
                
        st.session_state.history.append(next_idx)
        st.session_state.current_step += 1
        
    save_progress() # Sync to database

def prev_card():
    st.session_state.show_translation = False
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1
        save_progress() # Sync to database

def toggle_translation():
    st.session_state.show_translation = not st.session_state.show_translation


# =========================================================
# 6. USER INTERFACE (UI)
# =========================================================

# --- UNAUTHENTICATED VIEW (LOGIN/SIGNUP) ---
if not st.session_state.logged_in:
    st.title("📇 Flash-Learn: Malayalam")
    st.markdown("Learn conversational Malayalam through spaced repetition.")
    
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back")
        login_user = st.text_input("Enter your Username", key="login")
        
        if st.button("Log In", use_container_width=True):
            if login_user == "":
                st.warning("Please enter a username.")
            else:
                user_doc = db.collection("users").document(login_user).get()
                if user_doc.exists:
                    data = user_doc.to_dict()
                    st.session_state.username = login_user
                    st.session_state.history = data.get("history", [0])
                    st.session_state.current_step = data.get("current_step", 0)
                    st.session_state.logged_in = True
                    st.rerun() 
                else:
                    st.error("Username not found. Please check spelling or Sign Up.")

    with tab2:
        st.subheader("Create a New Account")
        new_user = st.text_input("Choose a Username", key="signup")
        
        if st.button("Register", use_container_width=True):
            if new_user == "":
                st.warning("Username cannot be empty.")
            else:
                existing_doc = db.collection("users").document(new_user).get()
                if existing_doc.exists:
                    st.error(f"⚠️ The username '{new_user}' is already taken.")
                else:
                    initial_data = {"history": [0], "current_step": 0}
                    db.collection("users").document(new_user).set(initial_data)
                    st.success(f"Account '{new_user}' created! You can now log in.")

# --- AUTHENTICATED VIEW (THE MAIN APP) ---
else:
    # Header & Logout 
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.title("📇 Learn Malayalam")
    with col_logout:
        st.write("") 
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    st.caption(f"Logged in as: **{st.session_state.username}**")
    st.markdown("---")

    # Determine if current card is New or a Review
    current_card_index = st.session_state.history[st.session_state.current_step]
    is_review = st.session_state.history[:st.session_state.current_step].count(current_card_index) > 0

    if is_review:
        st.warning("🔄 **Review Card:** You have seen this one before!")
    else:
        st.info("🆕 **New Concept**")

    card = st.session_state.flashcards[current_card_index]

    # Display Front (English)
    st.subheader("English:")
    st.markdown(f"## {card['english']}")

    # Flip Button
    if st.button("Flip Card 🔄", use_container_width=True):
        toggle_translation()

    # Display Back (Malayalam + Audio)
    if st.session_state.show_translation:
        st.success(f"## {card['malayalam']}")
        
        # Audio generation using Sarvam API (Format is WAV now)
        audio_file = generate_audio(card['spoken'])
        if audio_file:
            st.audio(audio_file, format='audio/wav')

    st.markdown("---")

    # Navigation Controls
    col_prev, col_next = st.columns(2)
    with col_prev:
        st.button("⬅️ Previous", on_click=prev_card, use_container_width=True, disabled=(st.session_state.current_step == 0))
    with col_next:
        st.button("Next ➡️", on_click=next_card, use_container_width=True)

    # Database-backed Progress Tracking
    unique_seen = len(set(st.session_state.history))
    st.caption(f"Sequence Step: {st.session_state.current_step + 1} | Unique Cards Discovered: {unique_seen}/{len(st.session_state.flashcards)}")

    st.markdown("---")
    
    # Custom Card Generator UI using Sarvam Translate
    with st.expander("➕ Create Custom Flashcard"):
        st.markdown("Type a phrase in English to instantly translate it into colloquial Malayalam and add it to your deck.")
        new_english_phrase = st.text_input("English Phrase:")
        
        if st.button("Generate Card"):
            if new_english_phrase:
                with st.spinner("Translating with Sarvam AI..."):
                    new_malayalam = translate_to_malayalam(new_english_phrase)
                    
                    if "Error" not in new_malayalam and "failed" not in new_malayalam:
                        new_card = {
                            "english": new_english_phrase,
                            "malayalam": new_malayalam,
                            "spoken": new_malayalam
                        }
                        
                        st.session_state.flashcards.append(new_card)
                        st.success(f"Added! **{new_english_phrase}** $\\rightarrow$ **{new_malayalam}**")
                        # Force a rerun to update the total card count display
                        st.rerun()
                    else:
                        st.error("Translation failed. Please check your Sarvam API key.")
            else:
                st.warning("Please enter a phrase first.")
