"""
app.py – CareCompanion Main Entry Point
Handles authentication, sidebar navigation and page routing.
Run with:  streamlit run app.py
"""

import streamlit as st
from pathlib import Path

# ── Must be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(
    page_title="CareCompanion – AI Elderly Care",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":    "https://github.com/carecompanion",
        "Report a bug": None,
        "About": "CareCompanion – AI-Powered Elderly Care & Emotional Support",
    },
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
from utils.helpers    import setup_logging
from database.schema  import init_db
from authentication.auth import init_session

setup_logging()
init_db()
init_session()


@st.cache_data
def _read_css(css_path: Path) -> str:
    with open(css_path, encoding="utf-8") as f:
        return f.read()

def _load_css() -> None:
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        css_content = _read_css(css_path)
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


_load_css()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH PAGES  (login / register)
# ══════════════════════════════════════════════════════════════════════════════

def _login_page() -> None:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1.5rem">
            <div style="font-size:3.5rem">🏥</div>
            <h1 style="color:#6C63FF;font-size:2rem;font-weight:800;margin:0.25rem 0">CareCompanion</h1>
            <p style="color:#636E72">AI-Powered Elderly Care & Emotional Support</p>
        </div>""", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Register"])

        # ── Login ─────────────────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username or Email", placeholder="your_username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("🔑 Sign In", type="primary",
                                                   use_container_width=True)
                if submitted:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    else:
                        from services.auth_service import login_user
                        from authentication.auth  import login_session
                        res = login_user(username.strip(), password)
                        if res["success"]:
                            login_session(res["user"])
                            st.success(f"Welcome back, {res['user'].get('full_name') or res['user']['username']}! 👋")
                            st.rerun()
                        else:
                            st.error(f"❌ {res['message']}")

        # ── Register ──────────────────────────────────────────────────────────
        with tab_register:
            with st.form("register_form", clear_on_submit=True):
                r_name  = st.text_input("Full Name", placeholder="e.g. Ramesh Kumar")
                rc1, rc2 = st.columns(2)
                r_user  = rc1.text_input("Username *", placeholder="ramesh_k")
                r_email = rc2.text_input("Email *", placeholder="ramesh@email.com")
                r_age   = st.number_input("Age", min_value=0, max_value=120, value=65, step=1)
                r_phone = st.text_input("Phone Number", placeholder="+91 98765 43210")
                pc1, pc2 = st.columns(2)
                r_pw1   = pc1.text_input("Password *", type="password", placeholder="Min 8 chars")
                r_pw2   = pc2.text_input("Confirm Password *", type="password")
                registered = st.form_submit_button("📝 Create Account", type="primary",
                                                    use_container_width=True)
                if registered:
                    if r_pw1 != r_pw2:
                        st.error("Passwords don't match.")
                    elif not r_user or not r_email or not r_pw1:
                        st.error("Please fill in all required fields (*)")
                    else:
                        from services.auth_service import register_user
                        res = register_user(r_user, r_email, r_pw1, r_name, r_age, r_phone)
                        if res["success"]:
                            st.success(f"✅ {res['message']} Please sign in.")
                        else:
                            st.error(f"❌ {res['message']}")

        st.markdown("""
        <div style="text-align:center;margin-top:2rem;color:#636E72;font-size:0.85rem">
            🔒 Your data is encrypted and stored locally.<br>
            CareCompanion is designed with your privacy in mind.
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  (shown when authenticated)
# ══════════════════════════════════════════════════════════════════════════════

NAV_ITEMS = [
    ("home",       "🏠", "Home"),
    ("chat",       "💬", "AI Chat"),
    ("mood",       "🎭", "Mood Tracker"),
    ("medicines",  "💊", "Medicines"),
    ("reminders",  "⏰", "Reminders"),
    ("rag",        "📋", "Medical Q&A"),
    ("voice",      "🎙️", "Voice"),
    ("emergency",  "🚨", "Emergency"),
    ("caregiver",  "👥", "Caregiver"),
    ("analytics",  "📊", "Analytics"),
    ("notes",      "📝", "Notes"),
    ("settings",   "⚙️", "Settings"),
    ("profile",    "👤", "Profile"),
]


def _sidebar() -> None:
    with st.sidebar:
        user     = st.session_state.get("user", {})
        name     = user.get("full_name") or user.get("username","User")
        username = user.get("username","")

        # Logo & user info
        st.markdown(f"""
        <div style="text-align:center;padding:1rem 0 0.5rem">
            <div style="font-size:2.8rem">🏥</div>
            <div style="font-size:1.15rem;font-weight:800;letter-spacing:0.02em">CareCompanion</div>
            <div style="opacity:0.75;font-size:0.82rem;margin-top:0.2rem">AI Elderly Care</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.15);border-radius:12px;padding:0.65rem 0.85rem;margin:0.5rem 0 1rem">
            <div style="font-weight:700;font-size:0.95rem">👋 {name}</div>
            <div style="opacity:0.75;font-size:0.78rem">@{username}</div>
        </div>""", unsafe_allow_html=True)

        # Emergency banner if flag is set
        if st.session_state.get("emergency_flag"):
            st.markdown("""
            <div style="background:#E17055;border-radius:10px;padding:0.5rem 0.75rem;
                        text-align:center;margin-bottom:0.75rem;animation:pulse 1s infinite">
                🚨 EMERGENCY ACTIVE
            </div>""", unsafe_allow_html=True)

        # Navigation
        current = st.session_state.get("page","home")
        for page_key, icon, label in NAV_ITEMS:
            is_active = current == page_key
            btn_style = "" if not is_active else "font-weight:800!important;background:rgba(255,255,255,0.3)!important"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["page"] = page_key
                st.rerun()

        st.markdown("---")
        if st.button("🚪  Logout", use_container_width=True, key="logout_btn"):
            from authentication.auth import logout_session
            logout_session()
            st.rerun()

        # Footer
        st.markdown(f"""
        <div style="position:fixed;bottom:1rem;text-align:center;opacity:0.5;font-size:0.72rem;width:220px">
            CareCompanion v{__import__('config').APP_VERSION}<br>
            Made with ❤️ for elderly care
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def _route() -> None:
    page = st.session_state.get("page", "home")

    if page == "home":
        from views.home          import render; render()
    elif page == "chat":
        from views.chat          import render; render()
    elif page == "mood":
        from views.mood          import render; render()
    elif page == "medicines":
        from views.medicines     import render; render()
    elif page == "reminders":
        from views.reminders     import render; render()
    elif page == "rag":
        from views.rag_assistant import render; render()
    elif page == "voice":
        from views.voice         import render; render()
    elif page == "emergency":
        from views.emergency     import render; render()
    elif page == "caregiver":
        from views.caregiver     import render; render()
    elif page == "analytics":
        from views.analytics     import render; render()
    elif page == "notes":
        from views.notes         import render; render()
    elif page == "settings":
        from views.settings      import render; render()
    elif page == "profile":
        from views.profile       import render; render()
    else:
        st.error(f"Unknown page: {page}")
        st.session_state["page"] = "home"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if not st.session_state.get("authenticated"):
        _login_page()
        return

    # Start background scheduler (once per process)
    try:
        from scheduler.reminder_scheduler import get_scheduler
        get_scheduler()
    except Exception:
        pass

    _sidebar()
    _route()


if __name__ == "__main__":
    main()
else:
    # Streamlit runs the module at import time
    main()
