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
        {"english": "What is your name?", "malayalam": "Pera entha?", "spoken": "Per entha?"},
        {"english": "My name is...", "malayalam": "Ente peru...", "spoken": "Ente peru..."},
        {"english": "Yes", "malayalam": "Athe", "spoken": "Athe"},
        {"english": "No", "malayalam": "Alla", "spoken": "Alla"},
        {"english": "Please", "malayalam": "Dhayavayi", "spoken": "Dhayavayi"},
        {"english": "Thank you", "malayalam": "Nanni", "spoken": "Nanni"},
        {"english": "Sorry", "malayalam": "Kshamikkannam", "spoken": "Kshamikkannam"},
        {"english": "Where are you going?", "malayalam": "Evidekka pokunne?", "spoken": "Evidekka pokunne?"},
        {"english": "I am going home", "malayalam": "Njan veettil pokuva", "spoken": "Njan veettil pokuva"},
        {"english": "Come here", "malayalam": "Ivide vaa", "spoken": "Ivide vaa"},
        {"english": "Go there", "malayalam": "Avide po", "spoken": "Avide po"},
        {"english": "What are you doing?", "malayalam": "Entha cheyyunne?", "spoken": "Entha cheyyunne?"},
        {"english": "Have you eaten?", "malayalam": "Kazhicho?", "spoken": "Kazhicho?"},
        {"english": "I have eaten", "malayalam": "Njan kazhichu", "spoken": "Njan kazhichu"},
        {"english": "I want water", "malayalam": "Enikku vellam venam", "spoken": "Enikku vellam venam"},
        {"english": "Give me", "malayalam": "Enikku tharu", "spoken": "Enikku tharu"},
        {"english": "Take it", "malayalam": "Edukku", "spoken": "Edukku"},
        {"english": "I don't know", "malayalam": "Enikku ariyilla", "spoken": "Enikku ariyilla"},
        {"english": "I know", "malayalam": "Enikku ariyam", "spoken": "Enikku ariyam"},
        {"english": "Do you understand?", "malayalam": "Manassilayo?", "spoken": "Manassilayo?"},
        {"english": "I understand", "malayalam": "Manassilayi", "spoken": "Manassilayi"},
        {"english": "I don't understand", "malayalam": "Manassilayilla", "spoken": "Manassilayilla"},
        {"english": "Speak slowly", "malayalam": "Pathukke parayu", "spoken": "Pathukke parayu"},
        {"english": "What is this?", "malayalam": "Ithu entha?", "spoken": "Ithu entha?"},
        {"english": "What is that?", "malayalam": "Athu entha?", "spoken": "Athu entha?"},
        {"english": "Who is that?", "malayalam": "Athu aara?", "spoken": "Athu aara?"},
        {"english": "Why?", "malayalam": "Enthina?", "spoken": "Enthina?"},
        {"english": "When?", "malayalam": "Eppozha?", "spoken": "Eppozha?"},
        {"english": "How?", "malayalam": "Engane?", "spoken": "Engane?"},
        {"english": "How much is this?", "malayalam": "Ithinu ethraya?", "spoken": "Ithinu ethraya?"},
        {"english": "It is expensive", "malayalam": "Valare vilayaanu", "spoken": "Valare vilayaanu"},
        {"english": "Reduce the price", "malayalam": "Vila kurakku", "spoken": "Vila kurakku"},
        {"english": "I want to buy this", "malayalam": "Enikku ithu vanganam", "spoken": "Enikku ithu vanganam"},
        {"english": "Where is the shop?", "malayalam": "Kada evideya?", "spoken": "Kada evideya?"},
        {"english": "Open the door", "malayalam": "Vathil thurakku", "spoken": "Vathil thurakku"},
        {"english": "Close the door", "malayalam": "Vathil adakku", "spoken": "Vathil adakku"},
        {"english": "Come inside", "malayalam": "Akathekku vaa", "spoken": "Akathekku vaa"},
        {"english": "Sit down", "malayalam": "Irikku", "spoken": "Irikku"},
        {"english": "Stand up", "malayalam": "Ezhunnelkku", "spoken": "Ezhunnelkku"},
        {"english": "Look here", "malayalam": "Ivide nokku", "spoken": "Ivide nokku"},
        {"english": "Listen", "malayalam": "Kelkku", "spoken": "Kelkku"},
        {"english": "Tell me", "malayalam": "Parayu", "spoken": "Parayu"},
        {"english": "Wait a minute", "malayalam": "Oru nimisham nikkamo", "spoken": "Oru nimisham nikkamo"},
        {"english": "Stop here", "malayalam": "Ivide nirthu", "spoken": "Ivide nirthu"},
        {"english": "Let's go", "malayalam": "Namukku pokam", "spoken": "Namukku pokam"},
        {"english": "See you later", "malayalam": "Pinne kanam", "spoken": "Pinne kanam"},
        {"english": "Good morning", "malayalam": "Suprabhatham", "spoken": "Suprabhatham"},
        {"english": "Good night", "malayalam": "Shubharathri", "spoken": "Shubharathri"},
        {"english": "Today", "malayalam": "Innu", "spoken": "Innu"},
        {"english": "Tomorrow", "malayalam": "Nale", "spoken": "Nale"},
        {"english": "Yesterday", "malayalam": "Innele", "spoken": "Innele"},
        {"english": "Morning", "malayalam": "Ravile", "spoken": "Ravile"},
        {"english": "Evening", "malayalam": "Vaikunneram", "spoken": "Vaikunneram"},
        {"english": "Night", "malayalam": "Rathri", "spoken": "Rathri"},
        {"english": "Time is up", "malayalam": "Samayam kazhinju", "spoken": "Samayam kazhinju"},
        {"english": "What is the time?", "malayalam": "Samayam ethraya?", "spoken": "Samayam ethraya?"},
        {"english": "It is raining", "malayalam": "Mazha peyyunnu", "spoken": "Mazha peyyunnu"},
        {"english": "It is hot", "malayalam": "Nalla choodaanu", "spoken": "Nalla choodaanu"},
        {"english": "It is cold", "malayalam": "Nalla thanuppaanu", "spoken": "Nalla thanuppaanu"},
        {"english": "I am tired", "malayalam": "Enikku ksheenamundu", "spoken": "Enikku ksheenamundu"},
        {"english": "I am sleepy", "malayalam": "Enikku urakkam varunnu", "spoken": "Enikku urakkam varunnu"},
        {"english": "I am hungry", "malayalam": "Enikku vishakkunnu", "spoken": "Enikku vishakkunnu"},
        {"english": "I am thirsty", "malayalam": "Enikku dāhikkunnu", "spoken": "Enikku dāhikkunnu"},
        {"english": "Are you ready?", "malayalam": "Ready aano?", "spoken": "Ready aano?"},
        {"english": "Help me", "malayalam": "Enne sahayikkamo", "spoken": "Enne sahayikkamo"},
        {"english": "Call the police", "malayalam": "Police-ne vilikku", "spoken": "Police-ne vilikku"},
        {"english": "Call a doctor", "malayalam": "Doctor-e vilikku", "spoken": "Doctor-e vilikku"},
        {"english": "I am sick", "malayalam": "Enikku vayya", "spoken": "Enikku vayya"},
        {"english": "Where is the hospital?", "malayalam": "Hospital evideya?", "spoken": "Hospital evideya?"},
        {"english": "I need a room", "malayalam": "Enikku oru room venam", "spoken": "Enikku oru room venam"},
        {"english": "Where is the toilet?", "malayalam": "Toilet evideya?", "spoken": "Toilet evideya?"},
        {"english": "Straight ahead", "malayalam": "Nere po", "spoken": "Nere po"},
        {"english": "Turn left", "malayalam": "Idathottu thiriyu", "spoken": "Idathottu thiriyu"},
        {"english": "Turn right", "malayalam": "Valathottu thiriyu", "spoken": "Valathottu thiriyu"},
        {"english": "Stop the bus", "malayalam": "Bus nirthu", "spoken": "Bus nirthu"},
        {"english": "Auto charge how much?", "malayalam": "Auto charge ethraya?", "spoken": "Auto charge ethraya?"},
        {"english": "Meter please", "malayalam": "Meter idamo?", "spoken": "Meter idamo?"},
        {"english": "Don't want", "malayalam": "Venda", "spoken": "Venda"},
        {"english": "Enough", "malayalam": "Mathi", "spoken": "Mathi"},
        {"english": "Is it good?", "malayalam": "Kollamo?", "spoken": "Kollamo?"},
        {"english": "It is good", "malayalam": "Nallathaanu", "spoken": "Nallathaanu"},
        {"english": "It is bad", "malayalam": "Moshamanu", "spoken": "Moshamanu"},
        {"english": "Big", "malayalam": "Valiya", "spoken": "Valiya"},
        {"english": "Small", "malayalam": "Cheriya", "spoken": "Cheriya"},
        {"english": "New", "malayalam": "Puthiya", "spoken": "Puthiya"},
        {"english": "Old", "malayalam": "Pazhaya", "spoken": "Pazhaya"},
        {"english": "Fast", "malayalam": "Vegam", "spoken": "Vegam"},
        {"english": "Slow", "malayalam": "Pathukke", "spoken": "Pathukke"},
        {"english": "Here", "malayalam": "Ivide", "spoken": "Ivide"},
        {"english": "There", "malayalam": "Avide", "spoken": "Avide"},
        {"english": "Where?", "malayalam": "Evide?", "spoken": "Evide?"},
        {"english": "Beautiful", "malayalam": "Sundaramaanu", "spoken": "Sundaramaanu"},
        {"english": "Delicious", "malayalam": "Ruchi aayittundu", "spoken": "Ruchi aayittundu"},
        {"english": "Easy", "malayalam": "Eluppamanu", "spoken": "Eluppamanu"},
        {"english": "Difficult", "malayalam": "Budhimuttanu", "spoken": "Budhimuttanu"},
        {"english": "I like it", "malayalam": "Enikku ishtamayi", "spoken": "Enikku ishtamayi"},
        {"english": "I don't like it", "malayalam": "Enikku ishtamayilla", "spoken": "Enikku ishtamayilla"}
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
