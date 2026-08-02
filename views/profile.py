"""
pages/profile.py – User Profile & AI Memory
Edit personal details, manage AI memory, change password.
"""

import streamlit as st

from services.auth_service   import get_user, update_profile, change_password
from services.memory_service import (
    get_all_memories, store_memory, delete_memory,
    MEM_PREFERENCE, MEM_PERSON, MEM_ROUTINE, MEM_MEDICAL,
)
from authentication.auth     import get_current_user_id
import config


MEM_TYPES = {
    MEM_PERSON:     ("👨‍👩‍👧 People", "Add family members, doctors"),
    MEM_PREFERENCE: ("❤️ Preferences", "Add favourite foods, hobbies, music"),
    MEM_MEDICAL:    ("🏥 Medical", "Add conditions, allergies, medications"),
    MEM_ROUTINE:    ("⏰ Routines", "Add daily habits and schedules"),
}


def render():
    user_id = get_current_user_id()
    user    = get_user(user_id) or st.session_state.get("user", {})

    st.markdown('<div class="page-title">👤 My Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your personal information and AI memory</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👤 Personal Info", "🧠 AI Memory", "🔒 Security"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Personal Info
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("#### 📋 Your Details")

        # Avatar placeholder
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:1.5rem">
            <div style="width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,#6C63FF,#FF6584);
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:2.5rem;color:white;font-weight:700;box-shadow:0 4px 20px rgba(108,99,255,0.3)">
                {(user.get('full_name') or user.get('username','?'))[0].upper()}
            </div>
            <p style="margin:0.5rem 0 0;font-weight:700;font-size:1.1rem">{user.get('full_name') or user.get('username','')}</p>
            <p style="color:#636E72;font-size:0.9rem">@{user.get('username','')} · Member since {str(user.get('created_at',''))[:10]}</p>
        </div>""", unsafe_allow_html=True)

        with st.form("profile_form"):
            fc1, fc2 = st.columns(2)
            p_name   = fc1.text_input("Full Name", value=user.get("full_name","") or "")
            p_age    = fc2.number_input("Age", min_value=0, max_value=120,
                                         value=int(user.get("age") or 0), step=1)
            pc1, pc2 = st.columns(2)
            p_phone  = pc1.text_input("Phone Number", value=user.get("phone","") or "")
            p_email  = pc2.text_input("Email", value=user.get("email",""),
                                       disabled=True, help="Email cannot be changed")
            lc1, lc2 = st.columns(2)
            p_lang   = lc1.selectbox("Language", list(config.LANGUAGES.keys()),
                                      format_func=lambda k: config.LANGUAGES[k],
                                      index=list(config.LANGUAGES.keys()).index(
                                          user.get("language","en")))
            p_theme  = lc2.selectbox("Theme", ["light","dark"],
                                      format_func=lambda x: "☀️ Light" if x=="light" else "🌙 Dark",
                                      index=0 if user.get("theme","light")=="light" else 1)

            if st.form_submit_button("💾 Update Profile", type="primary", use_container_width=True):
                res = update_profile(user_id, p_name, p_age, p_phone, p_lang, p_theme)
                if res["success"]:
                    # Refresh session
                    st.session_state["language"] = p_lang
                    st.session_state["theme"]    = p_theme
                    updated = get_user(user_id)
                    if updated:
                        st.session_state["user"] = dict(updated)
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – AI Memory
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 🧠 What CareCompanion Remembers About You")
        st.markdown("""
        <div class="cc-info-box">
            These memories help the AI personalise conversations. Add things like your doctor's name,
            favourite foods, family members, or health conditions.
        </div>""", unsafe_allow_html=True)

        memories  = get_all_memories(user_id)
        mem_by_type: dict[str, list] = {mt: [] for mt in MEM_TYPES}
        for m in memories:
            mt = m.get("memory_type", MEM_PREFERENCE)
            mem_by_type.setdefault(mt, []).append(m)

        for mem_type, (label, hint) in MEM_TYPES.items():
            st.markdown(f"**{label}**")
            type_mems = mem_by_type.get(mem_type, [])

            if not type_mems:
                st.markdown(f"<p style='color:#636E72;font-size:0.9rem'>None added yet. {hint}.</p>",
                            unsafe_allow_html=True)
            else:
                for m in type_mems:
                    mc1, mc2 = st.columns([5, 1])
                    mc1.markdown(f"""
                    <div style="padding:0.4rem 0.75rem;background:#F0EFFF;border-radius:8px;margin:2px 0">
                        <strong>{m['key'].replace('_',' ').title()}:</strong> {m['value']}
                    </div>""", unsafe_allow_html=True)
                    if mc2.button("🗑️", key=f"del_mem_{m['id']}", help="Forget this"):
                        delete_memory(user_id, m["id"])
                        st.rerun()

            # Add memory form
            with st.form(key=f"add_mem_{mem_type}", clear_on_submit=True):
                mc1, mc2, mc3 = st.columns([2, 3, 1])
                m_key = mc1.text_input("Key", placeholder=_placeholder_key(mem_type),
                                        key=f"mkey_{mem_type}", label_visibility="collapsed")
                m_val = mc2.text_input("Value", placeholder=_placeholder_val(mem_type),
                                        key=f"mval_{mem_type}", label_visibility="collapsed")
                if mc3.form_submit_button("➕", use_container_width=True):
                    if m_key and m_val:
                        res = store_memory(user_id, mem_type, m_key, m_val)
                        if res["success"]:
                            st.success(f"Remembered: {m_key} = {m_val}")
                            st.rerun()
                        else:
                            st.error(res["message"])
                    else:
                        st.warning("Please fill both fields.")

            st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Security (Password Change)
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🔒 Change Password")
        with st.form("change_password_form", clear_on_submit=True):
            old_pw  = st.text_input("Current Password", type="password", key="old_pw")
            new_pw  = st.text_input("New Password (min 8 chars)", type="password", key="new_pw")
            conf_pw = st.text_input("Confirm New Password", type="password", key="conf_pw")

            if st.form_submit_button("🔒 Update Password", type="primary", use_container_width=True):
                if new_pw != conf_pw:
                    st.error("New passwords don't match.")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    res = change_password(user_id, old_pw, new_pw)
                    if res["success"]:
                        st.success(res["message"])
                    else:
                        st.error(res["message"])

        st.markdown("---")
        st.markdown("#### 🛡️ Account Security Tips")
        st.markdown("""
        <div class="cc-info-box">
            • Use a <strong>unique, strong password</strong> that you don't use elsewhere<br>
            • Never share your password with anyone<br>
            • Log out when using a shared device<br>
            • Keep your emergency contacts updated
        </div>""", unsafe_allow_html=True)


def _placeholder_key(mem_type: str) -> str:
    return {
        MEM_PERSON:     "e.g. son_name",
        MEM_PREFERENCE: "e.g. favourite_food",
        MEM_MEDICAL:    "e.g. condition",
        MEM_ROUTINE:    "e.g. wake_up_time",
    }.get(mem_type, "Key")


def _placeholder_val(mem_type: str) -> str:
    return {
        MEM_PERSON:     "e.g. Rahul",
        MEM_PREFERENCE: "e.g. Idli and Sambar",
        MEM_MEDICAL:    "e.g. Type 2 Diabetes",
        MEM_ROUTINE:    "e.g. 6:30 AM",
    }.get(mem_type, "Value")
