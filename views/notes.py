"""
pages/notes.py – Personal Notes & Health Diary
Create text/voice notes, search, tag and manage your health diary.
"""

import streamlit as st
from datetime import datetime

from services.notes_service  import add_note, get_notes, get_note, update_note, delete_note
from speech.tts              import speak_in_streamlit
from authentication.auth     import get_current_user_id, get_current_language

NOTE_TYPES = ["general", "health", "personal", "voice"]
NOTE_TYPE_ICONS = {"general":"📌","health":"🏥","personal":"💭","voice":"🎙️"}


def render():
    user_id  = get_current_user_id()
    language = get_current_language()

    st.markdown('<div class="page-title">📝 Notes & Health Diary</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your personal journal — health notes, thoughts, and reminders</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 All Notes", "➕ New Note", "🎙️ Voice Note"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Notes List with Search
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        sc1, sc2 = st.columns([3, 1])
        search    = sc1.text_input("🔍 Search notes…", placeholder="e.g. blood pressure, doctor visit",
                                    key="notes_search", label_visibility="collapsed")
        type_filter = sc2.selectbox("Filter", ["All"] + NOTE_TYPES,
                                    format_func=lambda x: f"{NOTE_TYPE_ICONS.get(x,'📄')} {x.title()}" if x!="All" else "📂 All",
                                    key="notes_type_filter", label_visibility="collapsed")

        notes = get_notes(
            user_id,
            search=search,
            note_type="" if type_filter == "All" else type_filter,
        )

        if not notes:
            st.info("📭 No notes found. Write your first note in the 'New Note' tab!")
        else:
            st.markdown(f"**{len(notes)} note(s)**")
            for note in notes:
                icon      = NOTE_TYPE_ICONS.get(note["note_type"],"📌")
                updated   = str(note.get("updated_at",""))[:16]
                tags_str  = note.get("tags","")
                preview   = note["content"][:150] + ("…" if len(note["content"])>150 else "")

                with st.expander(
                    f"{icon} {note.get('title') or note['content'][:50]} — {updated}",
                    expanded=False,
                ):
                    st.markdown(f"""
                    <div class="info-card" style="padding:0.75rem 1rem">
                        <p style="white-space:pre-wrap;line-height:1.6">{note['content']}</p>
                        {f"<div style='margin-top:0.5rem'>🏷️ <small>{tags_str}</small></div>" if tags_str else ""}
                        <small style="color:#636E72">Type: {note['note_type']} · Created: {str(note['created_at'])[:10]}</small>
                    </div>""", unsafe_allow_html=True)

                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        if ec1.button("✏️ Edit", key=f"edit_note_{note['id']}", use_container_width=True):
                            st.session_state["editing_note"] = note["id"]
                    with ec2:
                        if ec2.button("🔊 Listen", key=f"listen_note_{note['id']}", use_container_width=True):
                            speak_in_streamlit(note["content"], language)
                    with ec3:
                        if ec3.button("🗑️ Delete", key=f"del_note_{note['id']}", use_container_width=True):
                            delete_note(note["id"])
                            st.success("Note deleted.")
                            st.rerun()

                    # Inline edit
                    if st.session_state.get("editing_note") == note["id"]:
                        st.markdown("---")
                        with st.form(key=f"edit_note_form_{note['id']}"):
                            e_title   = st.text_input("Title", value=note.get("title",""))
                            e_content = st.text_area("Content", value=note["content"], height=120)
                            e_tags    = st.text_input("Tags (comma-separated)", value=note.get("tags",""))
                            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                res = update_note(note["id"], e_content, e_title, e_tags)
                                if res["success"]:
                                    st.success(res["message"])
                                    st.session_state.pop("editing_note", None)
                                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – New Note
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### ✍️ Write a New Note")

        # Quick note templates
        st.markdown("**Quick Templates:**")
        templates = {
            "🩺 Doctor Visit":   f"Doctor Visit — {datetime.now().strftime('%d %b %Y')}\n\nDoctor Name:\nDiagnosis:\nPrescription:\nFollow-up Date:\nNotes:",
            "💊 Medicine Change": f"Medicine Update — {datetime.now().strftime('%d %b %Y')}\n\nChanged Medicine:\nOld Dosage:\nNew Dosage:\nReason:",
            "📋 Blood Test":      f"Blood Test — {datetime.now().strftime('%d %b %Y')}\n\nFasting/Non-Fasting:\nResults:\nDoctor Remarks:",
            "😊 Daily Mood":      f"Mood Diary — {datetime.now().strftime('%d %b %Y')}\n\nHow I felt today:\nWhat happened:\nThings I'm grateful for:",
        }
        temp_cols = st.columns(2)
        for i, (tlabel, ttext) in enumerate(templates.items()):
            with temp_cols[i % 2]:
                if st.button(tlabel, key=f"tmpl_{i}", use_container_width=True):
                    st.session_state["note_template"] = ttext
                    st.session_state["note_title"]    = tlabel.split(" ",1)[1]

        st.markdown("---")
        with st.form("new_note_form", clear_on_submit=True):
            n_title   = st.text_input("Title (optional)",
                                       value=st.session_state.pop("note_title",""),
                                       placeholder="e.g. Doctor visit – 15 Jan")
            n_content = st.text_area(
                "Note Content *",
                value=st.session_state.pop("note_template",""),
                height=180,
                placeholder="Write anything — health updates, thoughts, how you feel…",
            )
            fc1, fc2  = st.columns(2)
            n_type    = fc1.selectbox("Category", NOTE_TYPES,
                                       format_func=lambda x: f"{NOTE_TYPE_ICONS[x]} {x.title()}")
            n_tags    = fc2.text_input("Tags", placeholder="e.g. blood pressure, diabetes")

            if st.form_submit_button("💾 Save Note", type="primary", use_container_width=True):
                res = add_note(user_id, n_content, n_title, n_type, n_tags)
                if res["success"]:
                    st.success(res["message"])
                    st.balloons()
                else:
                    st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Voice Note
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🎙️ Record a Voice Note")
        st.markdown("""
        <div class="cc-info-box">
            Speak your note and it will be automatically transcribed and saved.
        </div>""", unsafe_allow_html=True)

        recorded_text = ""
        try:
            from audio_recorder_streamlit import audio_recorder
            from speech.stt import audio_bytes_to_text, is_stt_available

            if is_stt_available():
                audio_bytes = audio_recorder(
                    text="🔴 Click to record",
                    recording_color="#E17055",
                    neutral_color="#6C63FF",
                    icon_name="microphone",
                    icon_size="3x",
                    pause_threshold=3.0,
                    key="voice_note_recorder",
                )
                if audio_bytes and len(audio_bytes) > 1000:
                    with st.spinner("Transcribing…"):
                        result = audio_bytes_to_text(audio_bytes, language)
                    if result["success"]:
                        recorded_text = result["text"]
                        st.markdown(f"""
                        <div class="info-card" style="border-left:4px solid #43C6AC">
                            <strong>Transcribed:</strong> {recorded_text}
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.warning(result["error"])
            else:
                st.warning("SpeechRecognition not available. Using text input below.")
        except ImportError:
            st.info("Voice recording requires `audio-recorder-streamlit`. Using text input.")

        # Text fallback / override
        voice_text = st.text_area(
            "Or type your voice note:",
            value=recorded_text,
            height=100,
            key="voice_note_text",
        )
        v_title = st.text_input("Note Title", value=f"Voice Note – {datetime.now().strftime('%d %b %Y %H:%M')}",
                                 key="voice_note_title")

        if st.button("💾 Save Voice Note", type="primary", use_container_width=True, key="save_voice_note"):
            content = voice_text.strip()
            if not content:
                st.warning("Please record or type something first.")
            else:
                res = add_note(user_id, content, v_title, "voice", "voice")
                if res["success"]:
                    st.success("🎙️ Voice note saved!")
                    st.balloons()
                else:
                    st.error(res["message"])
