import streamlit as st
import sqlite3
import uuid
import base64
from PIL import Image
import io

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('valentines.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS proposals
                 (id TEXT PRIMARY KEY, sender TEXT, recipient TEXT, image_b64 TEXT, response TEXT)''')
    conn.commit()
    conn.close()

def save_proposal(sender, recipient, image_b64):
    proposal_id = str(uuid.uuid4())
    conn = sqlite3.connect('valentines.db')
    c = conn.cursor()
    c.execute("INSERT INTO proposals (id, sender, recipient, image_b64, response) VALUES (?, ?, ?, ?, ?)",
              (proposal_id, sender, recipient, image_b64, 'pending'))
    conn.commit()
    conn.close()
    return proposal_id

def get_proposal(proposal_id):
    conn = sqlite3.connect('valentines.db')
    c = conn.cursor()
    c.execute("SELECT sender, recipient, image_b64, response FROM proposals WHERE id=?", (proposal_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_response(proposal_id, response):
    conn = sqlite3.connect('valentines.db')
    c = conn.cursor()
    c.execute("UPDATE proposals SET response=? WHERE id=?", (response, proposal_id))
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

# --- UI STYLING ---
def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&family=Poppins:wght@300;400;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle, #fff5f5 0%, #fed7e2 100%);
    }

    h1 {
        font-family: 'Pacifico', cursive;
        color: #ff2d55;
        font-size: 3.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 30px;
        text-align: center;
    }

    h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: #d63384;
        text-align: center;
        font-weight: 600;
    }

    .stButton>button {
        width: 100%;
        border-radius: 50px !important;
        background: linear-gradient(90deg, #ff4d6d, #ff758f) !important;
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(255, 77, 109, 0.4);
        transition: transform 0.2s !important;
    }

    .stButton>button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 6px 20px rgba(255, 77, 109, 0.6) !important;
    }

    .proposal-card {
        background: rgba(255, 255, 255, 0.7);
        padding: 40px;
        border-radius: 40px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.1);
        text-align: center;
        backdrop-filter: blur(15px);
        border: 2px solid rgba(255,255,255,0.5);
    }

    .heart {
        position: fixed;
        color: #ff4d6d;
        font-size: 20px;
        animation: float 6s infinite ease-in;
        z-index: -1;
        user-select: none;
        pointer-events: none;
    }

    @keyframes float {
        0% { transform: translateY(100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(-10vh) rotate(360deg); opacity: 0; }
    }
    </style>
    
    <div class="hearts-container">
        <div class="heart" style="left: 10%; animation-delay: 0s;">❤️</div>
        <div class="heart" style="left: 20%; animation-delay: 2s; font-size: 30px;">💖</div>
        <div class="heart" style="left: 35%; animation-delay: 4s;">💗</div>
        <div class="heart" style="left: 50%; animation-delay: 1s; font-size: 25px;">💓</div>
        <div class="heart" style="left: 65%; animation-delay: 3s;">💝</div>
        <div class="heart" style="left: 80%; animation-delay: 5s;">❤️</div>
        <div class="heart" style="left: 90%; animation-delay: 2s; font-size: 35px;">💘</div>
    </div>
    """, unsafe_allow_html=True)

def get_all_proposals():
    conn = sqlite3.connect('valentines.db')
    c = conn.cursor()
    c.execute("SELECT sender, recipient, response, id FROM proposals")
    rows = c.fetchall()
    conn.close()
    return rows

# --- PAGES ---
def creator_page():
    st.markdown("<h1>Valentine's Proposal Maker</h1>", unsafe_allow_html=True)
    
    # JavaScript to auto-detect the public URL
    st.markdown("""
        <script>
        const currentUrl = window.location.origin;
        const urlInput = window.parent.document.querySelector('input[aria-label="Public App URL"]');
        if (urlInput && !urlInput.value.includes('streamlit.app')) {
            // This is a bit hacky as Streamlit fields are tricky to target, 
            // but we'll use session state instead.
        }
        </script>
    """, unsafe_allow_html=True)

    # Use session state to store the base URL
    if 'base_url' not in st.session_state:
        st.session_state['base_url'] = "http://localhost:8501"

    tabs = st.tabs(["✨ Create New", "📜 Sent Requests", "⚙️ Settings"])
    
    with tabs[2]:
        st.markdown("<h3>App Settings</h3>", unsafe_allow_html=True)
        new_url = st.text_input("Public App URL", value=st.session_state['base_url'], 
                               help="Paste your live URL here (e.g., https://your-app.streamlit.app)")
        if new_url != st.session_state['base_url']:
            st.session_state['base_url'] = new_url
            st.success("URL Updated!")
        st.info("💡 This is used to make sure the links you send to people actually work on their devices.")

    with tabs[0]:
        st.markdown('<div class="proposal-card">', unsafe_allow_html=True)
        
        # Super clear warning if URL is still localhost
        if "localhost" in st.session_state['base_url']:
            st.warning("⚠️ **Wait!** You are still using a 'localhost' link. People won't be able to open this on their phones.")
            st.info("Please go to the **⚙️ Settings** tab and paste your public Streamlit URL first!")
        
        sender = st.text_input("From (Your Name)", placeholder="e.g. your secret admirer")
        recipient = st.text_input("To (Their Name)", placeholder="e.g. the person of your dreams")
        uploaded_file = st.file_uploader("Upload a beautiful memory 📸", type=["jpg", "png", "jpeg"])
        
        if st.button("Create Valentine's Magic ✨"):
            if sender and recipient and uploaded_file:
                img_b64 = get_image_base64(uploaded_file)
                proposal_id = save_proposal(sender, recipient, img_b64)
                
                current_base = st.session_state['base_url'].rstrip('/')
                valentine_link = f"{current_base}/?proposal_id={proposal_id}"
                
                st.success("Proposal Created! Share the love:")
                st.code(valentine_link, language=None)
                st.balloons()
            else:
                st.error("Fill in the names and upload a picture! 💖")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("<h3>Track Your Requests 💘</h3>", unsafe_allow_html=True)
        proposals = get_all_proposals()
        if not proposals:
            st.info("You haven't sent any requests yet. Start your journey in the 'Create New' tab!")
        else:
            current_base = st.session_state['base_url'].rstrip('/')
            for s, r, response, pid in proposals:
                status_emoji = "💖" if response == 'yes' else "⏳"
                with st.expander(f"To: {r} {status_emoji}"):
                    st.write(f"**From:** {s}")
                    st.write(f"**Status:** {response.upper()}")
                    st.write(f"**Link:** `{current_base}/?proposal_id={pid}`")

def recipient_page(proposal_id):
    data = get_proposal(proposal_id)
    if not data:
        st.error("Oops! This proposal doesn't exist.")
        return

    sender, recipient, img_b64, status = data
    
    if status == 'yes':
        st.balloons()
        st.markdown("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            var duration = 15 * 1000;
            var animationEnd = Date.now() + duration;
            var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

            function randomInRange(min, max) {
              return Math.random() * (max - min) + min;
            }

            var interval = setInterval(function() {
              var timeLeft = animationEnd - Date.now();

              if (timeLeft <= 0) {
                return clearInterval(interval);
              }

              var particleCount = 50 * (timeLeft / duration);
              // since particles fall down, start a bit higher than random
              confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
              confetti(Object.assign({}, defaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
            }, 250);
        </script>
        """, unsafe_allow_html=True)
        st.markdown(f"<h1>YES! ❤️</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3>Best Valentine's ever! {sender} is so happy!</h3>", unsafe_allow_html=True)
        if img_b64:
            st.image(f"data:image/png;base64,{img_b64}", use_column_width=True)
        return

    st.markdown(f"<h1>Hi {recipient}! 👋</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3>{sender} has a question for you...</h3>", unsafe_allow_html=True)
    
    if img_b64:
        st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 20px;">', unsafe_allow_html=True)
        st.image(f"data:image/png;base64,{img_b64}", width=400)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<h2 style='font-size: 2.5rem; color: #ff2d55;'>Will you be my Valentine? 🌹</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("YES! 😍", key="yes_btn"):
            update_response(proposal_id, 'yes')
            st.rerun()

    with col2:
        st.markdown("""
        <div id="no-container" style="position: relative; width: 100%; height: 50px;">
            <button id="no-btn" style="position: absolute; left: 0; top: 0; width: 100%; border-radius: 50px; border: none; padding: 15px 30px; background: #6c757d; color: white; font-weight: bold; font-size: 1.2rem; cursor: pointer; transition: all 0.2s;">
                No... 🥺
            </button>
        </div>
        <script>
            const noBtn = document.getElementById('no-btn');
            noBtn.addEventListener('mouseover', () => {
                const x = Math.random() * (window.innerWidth - 150);
                const y = Math.random() * (window.innerHeight - 50);
                noBtn.style.position = 'fixed';
                noBtn.style.left = x + 'px';
                noBtn.style.top = y + 'px';
                noBtn.style.zIndex = '10000';
            });
            noBtn.addEventListener('click', (e) => {
                e.preventDefault();
                alert("Incorrect answer! Try again! ❤️");
            });
        </script>
        """, unsafe_allow_html=True)

# --- MAIN ---
def main():
    st.set_page_config(page_title="Valentine's Request", page_icon="💖", layout="centered")
    init_db()
    apply_custom_css()

    # Get query params
    params = st.query_params
    proposal_id = params.get("proposal_id")

    if proposal_id:
        recipient_page(proposal_id)
    else:
        creator_page()

if __name__ == "__main__":
    main()
