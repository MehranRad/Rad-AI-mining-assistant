import streamlit as st
from agent import ask_question, db
from chat_storage import (
    init_chat_tables, create_session, save_message,
    list_sessions, load_messages, delete_session,
    init_user_table, authenticate_user
)
import ast
import os
import html


st.set_page_config(
    page_title="دستیار هوشمند مس",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def _ensure_chat_tables():
    init_chat_tables()
    return True

_ensure_chat_tables()

@st.cache_resource
def _ensure_user_table():
    init_user_table()
    return True

_ensure_user_table()

# ------------------------------------------------------------------
# Login gate — must pass before anything else in the app renders.
# Role comes ONLY from this authenticated login, never from chat text.
# ------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown(
        "<h2 style='text-align:center; direction:rtl;'>ورود به دستیار هوشمند مس</h2>",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            login_username = st.text_input("نام کاربری")
            login_password = st.text_input("رمز عبور", type="password")
            submitted = st.form_submit_button("ورود", use_container_width=True)

        if submitted:
            result = authenticate_user(login_username.strip(), login_password)
            if result is not None:
                st.session_state.user = result
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است.")
    st.stop()

# ------------------------------------------------------------------
# Design system — light premium enterprise SaaS theme
# ------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&display=swap');

:root {
    /* Surfaces */
    --bg-page: #FAF8F5;
    --bg-surface: #FFFFFF;
    --bg-surface-alt: #F5F1EB;
    --bg-sunken: #F7F4EF;

    /* Borders */
    --border-subtle: rgba(15,23,42,0.08);
    --border-default: rgba(181,114,58,0.28);
    --border-strong: rgba(181,114,58,0.55);

    /* Copper accent — selective, never dominant */
    --copper-500: #B5723A;
    --copper-600: #8B4A28;
    --copper-tint: rgba(181,114,58,0.07);

    /* Text */
    --text-primary: #1E2430;
    --text-secondary: #5B6472;
    --text-tertiary: #8A93A3;

    /* Semantic */
    --success: #16A34A;
    --danger: #DC2626;
    --danger-tint: rgba(220,38,38,0.06);

    /* Spacing */
    --space-1: 4px; --space-2: 8px; --space-3: 12px;
    --space-4: 16px; --space-5: 24px; --space-6: 32px; --space-7: 48px;

    /* Radius */
    --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-xl: 18px;

    /* Elevation — soft only */
    --shadow-soft: 0 1px 3px rgba(15,23,42,0.04), 0 1px 2px rgba(15,23,42,0.03);
    --shadow-elevated: 0 4px 16px rgba(15,23,42,0.06);
}

/* ---- Global ---- */
html, body, [class*="css"], .stApp {
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    background: var(--bg-page) !important;
    color: var(--text-primary) !important;
}
.stApp { background: var(--bg-page) !important; }

.main .block-container {
    direction: rtl;
    text-align: right;
    max-width: 980px;
    padding-top: var(--space-5);
    padding-bottom: var(--space-7);
}

#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"] [data-testid="stDeployButton"] { display: none !important; }
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}
/* Keep the sidebar open/close control visible and on-theme */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    color: var(--text-secondary) !important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button {
    color: var(--text-secondary) !important;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
    background: var(--bg-surface) !important;
    border-left: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] > div { background: transparent !important; padding-top: var(--space-4); }
section[data-testid="stSidebar"] hr { border-color: var(--border-subtle) !important; margin: var(--space-5) 0; }

.sidebar-section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-tertiary);
    margin: 0 0 var(--space-3);
}

/* ---- Hero (compact, elegant) ---- */
.hero {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-4) var(--space-5);
    border-radius: var(--radius-xl);
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-soft);
    margin-bottom: var(--space-5);
}
.hero-badge {
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--copper-500);
}
.hero-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
}
.hero-sub {
    margin: var(--space-1) 0 0;
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-weight: 400;
}
.hero-caption {
    margin: var(--space-1) 0 0;
    font-size: 0.72rem;
    color: var(--text-tertiary);
}

/* ---- KPI cards ---- */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-3);
    margin-bottom: var(--space-5);
}
.metric-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    box-shadow: var(--shadow-soft);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
}
.metric-card-icon { color: var(--text-tertiary); }
.metric-card-icon svg { width: 17px; height: 17px; }
.metric-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}
.metric-value .accent-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--copper-500);
    margin-left: var(--space-2);
    vertical-align: middle;
}
.metric-label {
    font-size: 0.83rem;
    color: var(--text-secondary);
}

/* ---- Chat messages ---- */
[data-testid="stChatMessage"] {
    direction: rtl;
    text-align: right;
    background: transparent !important;
    padding: var(--space-2) 0 !important;
}
[data-testid="stChatMessage"] > div {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: var(--space-4) !important;
    box-shadow: var(--shadow-soft) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div,
[data-testid="stChatMessage"]:has(img[alt="user"]) > div {
    background: var(--copper-tint) !important;
    border-color: var(--border-default) !important;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
[data-testid="stChatMessage"]:last-of-type { animation: fadeIn 0.25s ease; }

.answer-error {
    border: 1px solid rgba(220,38,38,0.2);
    border-right: 3px solid var(--danger);
    background: var(--danger-tint);
    border-radius: var(--radius-sm);
    padding: var(--space-3) var(--space-4);
    color: var(--text-primary);
    font-size: 0.95rem;
    line-height: 1.7;
    white-space: pre-wrap;
}
.answer-error-label {
    color: var(--danger);
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: var(--space-2);
    display: block;
}

/* ---- Chat input — a strong, premium component ---- */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
.stChatFloatingInputContainer {
    background: var(--bg-page) !important;
    border-top: 1px solid var(--border-subtle) !important;
}
[data-testid="stChatInput"] { background: transparent !important; }
[data-testid="stChatInput"] > div {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-soft) !important;
}
[data-testid="stChatInput"] textarea {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    background: transparent !important;
    color: var(--text-primary) !important;
    caret-color: var(--copper-500) !important;
    min-height: 46px !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-tertiary) !important; }
[data-testid="stChatInput"]:focus-within > div {
    border-color: var(--border-strong) !important;
    box-shadow: var(--shadow-elevated) !important;
}
[data-testid="stChatInput"] button,
[data-testid="stChatInputSubmitButton"] {
    background: var(--copper-500) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: #FFFFFF !important;
}
[data-testid="stChatInput"] button:hover,
[data-testid="stChatInputSubmitButton"]:hover { background: var(--copper-600) !important; }
[data-testid="stChatInput"] button svg,
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor !important; }

/* ---- Buttons ---- */
.stButton button {
    width: 100%;
    text-align: right;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-subtle) !important;
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    font-family: 'Vazirmatn', Tahoma, sans-serif !important;
    font-weight: 500 !important;
    padding: var(--space-3) var(--space-4) !important;
    margin-bottom: var(--space-2) !important;
    transition: border-color 0.15s ease, background 0.15s ease !important;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    box-shadow: none !important;
}
.stButton button:hover {
    border-color: var(--border-default) !important;
    background: var(--copper-tint) !important;
    color: var(--text-primary) !important;
}
.stButton button:active { border-color: var(--border-strong) !important; }

/* Primary new-chat button (first button in sidebar) */
section[data-testid="stSidebar"] .stButton:first-of-type button {
    background: var(--copper-500) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton:first-of-type button:hover { background: var(--copper-600) !important; }

/* Checkbox */
.stCheckbox label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }

/* Expander (technical SQL layer) */
[data-testid="stExpander"] {
    background: var(--bg-sunken) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    margin-top: var(--space-2);
    box-shadow: none !important;
}
[data-testid="stExpander"] summary { color: var(--text-secondary) !important; font-weight: 500 !important; font-size: 0.85rem !important; }
.stCodeBlock, pre { border-radius: var(--radius-sm) !important; border: 1px solid var(--border-subtle) !important; background: var(--bg-sunken) !important; }

/* ---- Typing indicator ---- */
.typing-wrapper { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-1) 0; }
.typing-dots { display: flex; gap: var(--space-1); }
.typing-dots span {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--copper-500);
    animation: dotPulse 1.4s infinite ease-in-out both;
}
.typing-dots span:nth-child(1) { animation-delay: -0.28s; }
.typing-dots span:nth-child(2) { animation-delay: -0.14s; }
@keyframes dotPulse { 0%, 80%, 100% { opacity: 0.25; } 40% { opacity: 1; } }
.typing-text { color: var(--text-secondary); font-size: 0.85rem; }

.sidebar-note {
    background: var(--bg-sunken);
    border: 1px solid var(--border-subtle);
    border-right: 3px solid var(--copper-500);
    padding: var(--space-4);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: var(--space-2);
    line-height: 1.75;
}
.footer-credit {
    text-align: center;
    font-size: 0.72rem;
    color: var(--text-tertiary);
    margin-top: var(--space-6);
    padding-top: var(--space-4);
    border-top: 1px solid var(--border-subtle);
}

/* ---- Empty state — compact, not a giant void ---- */
.empty-state {
    text-align: center;
    padding: var(--space-5);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-subtle);
    background: var(--bg-surface);
    box-shadow: var(--shadow-soft);
    margin: var(--space-2) 0 var(--space-4);
}
.empty-state-icon { color: var(--copper-500); margin-bottom: var(--space-3); }
.empty-state-icon svg { width: 26px; height: 26px; }
.empty-state-title { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: var(--space-2); }
.empty-state-desc { font-size: 0.85rem; color: var(--text-secondary); max-width: 420px; margin: 0 auto; line-height: 1.7; }
.empty-suggestions-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-tertiary);
    margin: var(--space-5) 0 var(--space-2);
    text-align: center;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 999px; }

.stCaption, [data-testid="stCaptionContainer"] { color: var(--text-tertiary) !important; }

@media (max-width: 900px) { .metrics-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 520px) {
    .metrics-row { grid-template-columns: 1fr; }
    .hero { flex-direction: column; text-align: center; }
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Icon marks (inline SVG, currentColor)
# ------------------------------------------------------------------
ICON_USERS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 20v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="6" r="3.5"/><path d="M21 20v-2a3.5 3.5 0 0 0-2.5-3.35"/><path d="M15.5 3.15a3.5 3.5 0 0 1 0 6.7"/></svg>'
ICON_GEAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 13a7.5 7.5 0 0 0 0-2l2-1.5-2-3.4-2.4 1a7.6 7.6 0 0 0-1.7-1L15 3h-4l-.3 2.6a7.6 7.6 0 0 0-1.7 1l-2.4-1-2 3.4L6.6 11a7.5 7.5 0 0 0 0 2l-2 1.5 2 3.4 2.4-1a7.6 7.6 0 0 0 1.7 1L11 21h4l.3-2.6a7.6 7.6 0 0 0 1.7-1l2.4 1 2-3.4-2-1.5z"/></svg>'
ICON_PULSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M8 12h2l1.5 4L14 8l1.5 4H16"/></svg>'
ICON_CHART = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20V10M12 20V4M20 20v-7"/></svg>'
ICON_MINE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l8 6-8 6-8-6 8-6z"/><path d="M4 15l8 6 8-6"/></svg>'


# ------------------------------------------------------------------
# Hero header — compact, elegant
# ------------------------------------------------------------------
LOGO_PATH = "assets/logo.png"

BADGE_SVG = """
<svg width="22" height="22" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <text x="50" y="62" font-size="46" font-weight="700" fill="#FFFFFF" text-anchor="middle"
        font-family="Georgia, 'Times New Roman', serif">Cu</text>
</svg>
"""

st.markdown(f"""
<div class="hero">
    <div class="hero-badge">{BADGE_SVG}</div>
    <div>
        <p class="hero-title">دستیار هوشمند تحلیل داده معدن مس</p>
        <p class="hero-sub">پرسش و پاسخ هوشمند درباره تولید، تجهیزات و نیروی انسانی</p>
        <p class="hero-caption">اجرای محلی · Llama 3.1 · بدون اتصال به اینترنت</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Live snapshot metrics
# ------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_snapshot_stats():
    def _first_value(raw):
        try:
            parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
            return parsed[0][0]
        except Exception:
            return None

    return {
        "employees": _first_value(db.run("SELECT COUNT(*) FROM Employees")),
        "equipment": _first_value(db.run("SELECT COUNT(*) FROM Equipment")),
        "running": _first_value(db.run("SELECT COUNT(*) FROM Equipment WHERE Status='Running'")),
        "recovery": _first_value(db.run("SELECT AVG(RecoveryRate) FROM Production")),
    }

try:
    snapshot = get_snapshot_stats()
    recovery_display = f"{float(snapshot['recovery']):.1f}%" if snapshot['recovery'] is not None else "—"
    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-card">
            <div class="metric-card-icon">{ICON_USERS}</div>
            <div class="metric-value">{snapshot['employees'] if snapshot['employees'] is not None else "—"}<span class="accent-dot"></span></div>
            <div class="metric-label">کل کارکنان</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">{ICON_GEAR}</div>
            <div class="metric-value">{snapshot['equipment'] if snapshot['equipment'] is not None else "—"}<span class="accent-dot"></span></div>
            <div class="metric-label">کل تجهیزات</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">{ICON_PULSE}</div>
            <div class="metric-value">{snapshot['running'] if snapshot['running'] is not None else "—"}<span class="accent-dot"></span></div>
            <div class="metric-label">تجهیزات فعال</div>
        </div>
        <div class="metric-card">
            <div class="metric-card-icon">{ICON_CHART}</div>
            <div class="metric-value">{recovery_display}<span class="accent-dot"></span></div>
            <div class="metric-label">میانگین نرخ بازیابی</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    pass


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None


# ------------------------------------------------------------------
# Error-state detection (presentation only — does not alter backend logic)
# ------------------------------------------------------------------
_ERROR_PREFIXES = ("خطا", "متاسفانه")

def is_error_answer(answer: str) -> bool:
    return isinstance(answer, str) and answer.strip().startswith(_ERROR_PREFIXES)

def render_answer(answer: str):
    if is_error_answer(answer):
        st.markdown(
            f'<div class="answer-error"><span class="answer-error-label">خطا در پردازش</span>'
            f'{html.escape(answer)}</div>',
            unsafe_allow_html=True
        )
    else:
        st.write(answer)

def render_steps(steps):
    if not steps:
        return
    with st.expander("جزئیات فنی"):
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}. {step['label']}**")
            st.code(step["sql"], language="sql")
            st.text(step["result"][:1000])


example_questions = [
    "چند نفر کارمند در مجموعه داریم؟",
    "کدام معدن بیشترین تجهیزات را دارد؟",
    "میانگین حقوق در بخش تولید چقدر است؟",
    "چرا معدن سونگون نرخ بازیابی پایین‌تری دارد؟",
    "وضعیت تجهیزات هر معدن را مقایسه کن",
]


# ------------------------------------------------------------------
# Sidebar — primary action → workspace → settings/context
# ------------------------------------------------------------------
with st.sidebar:
    # Zone 0: logged-in user info
    role_labels = {"staff": "کارمند", "supervisor": "سرپرست", "manager": "مدیر"}
    st.markdown(
        f"<div class='sidebar-note'>کاربر: <b>{st.session_state.user['username']}</b>"
        f"<br>نقش: <b>{role_labels.get(st.session_state.user['role'], st.session_state.user['role'])}</b></div>",
        unsafe_allow_html=True
    )
    if st.button("خروج", use_container_width=True):
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
    st.markdown("---")

    # Zone 1: primary action
    if st.button("+  گفتگوی جدید", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    # Zone 2: workspace (sessions)
    st.markdown('<p class="sidebar-section-title">گفتگوها</p>', unsafe_allow_html=True)
    past_sessions = list_sessions(user_id=st.session_state.user["user_id"])
    sidebar_selected_example = None
    if past_sessions:
        for sess in past_sessions:
            is_current = st.session_state.session_id == sess["session_id"]
            col_a, col_b = st.columns([5, 1])
            with col_a:
                label = ("● " if is_current else "") + sess["title"]
                if st.button(label, key=f"load_{sess['session_id']}", use_container_width=True):
                    st.session_state.session_id = sess["session_id"]
                    st.session_state.messages = load_messages(
                        sess["session_id"], user_id=st.session_state.user["user_id"]
                    )
                    st.rerun()
            with col_b:
                if st.button("×", key=f"del_{sess['session_id']}"):
                    delete_session(sess["session_id"], user_id=st.session_state.user["user_id"])
                    if is_current:
                        st.session_state.session_id = None
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.caption("هنوز گفتگویی ثبت نشده")

    st.markdown("---")

    # Zone 3: settings / context
    show_technical = st.checkbox("نمایش جزئیات فنی (SQL)", value=False)

    st.markdown('<p class="sidebar-section-title">نمونه سوالات</p>', unsafe_allow_html=True)
    for q in example_questions:
        if st.button(q, key=f"ex_{q}"):
            sidebar_selected_example = q

    st.markdown(
        "<div class='sidebar-note'>"
        "نسخه Prototype — کاملاً محلی، بدون ارسال داده به اینترنت.<br>"
        "تاریخچه گفتگوها خودکار ذخیره می‌شود."
        "</div>",
        unsafe_allow_html=True
    )


# ------------------------------------------------------------------
# Empty state when no messages — compact, with suggested-question chips
# ------------------------------------------------------------------
main_selected_example = None
if not st.session_state.messages:
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{ICON_MINE}</div>
        <div class="empty-state-title">آماده تحلیل داده‌های معدن</div>
        <div class="empty-state-desc">
            سوال خود را بنویسید یا از نمونه سوالات زیر استفاده کنید.
            پاسخ‌ها بر اساس داده‌های واقعی تولید، تجهیزات و نیروی انسانی ساخته می‌شوند.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<p class="empty-suggestions-label">نمونه سوالات</p>', unsafe_allow_html=True)
    cols = st.columns(len(example_questions))
    for col, q in zip(cols, example_questions):
        with col:
            if st.button(q, key=f"empty_ex_{q}", use_container_width=True):
                main_selected_example = q


# ------------------------------------------------------------------
# Chat history
# ------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⛏️"):
        if msg["role"] == "assistant":
            render_answer(msg["content"])
            if show_technical:
                render_steps(msg.get("steps"))
        else:
            st.write(msg["content"])


# ------------------------------------------------------------------
# New question
# ------------------------------------------------------------------
typed_question = st.chat_input("سوال خود را درباره معدن بنویسید...")
question = main_selected_example or sidebar_selected_example or typed_question

if question:
    with st.chat_message("user", avatar="👤"):
        st.write(question)
    st.session_state.messages.append({"role": "user", "content": question, "steps": []})

    with st.chat_message("assistant", avatar="⛏️"):
        placeholder = st.empty()
        placeholder.markdown("""
            <div class="typing-wrapper">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                <span class="typing-text">در حال تحلیل داده‌ها...</span>
            </div>
        """, unsafe_allow_html=True)

        try:
            result = ask_question(
                question,
                role=st.session_state.user["role"],
                username=st.session_state.user["username"],
            )
            answer = result["answer"]
            steps = result.get("steps", [])
            is_confidential = result.get("is_confidential", False)
        except Exception as e:
            answer = f"خطای غیرمنتظره رخ داد: {str(e)}"
            steps = []
            is_confidential = False

        placeholder.empty()
        render_answer(answer)
        if show_technical:
            render_steps(steps)
        if is_confidential:
            st.caption("🔒 این گفتگو شامل اطلاعات محرمانه است و در تاریخچه ذخیره نمی‌شود.")

    st.session_state.messages.append({"role": "assistant", "content": answer, "steps": steps})

    if not is_confidential:
        if st.session_state.session_id is None:
            st.session_state.session_id = create_session(question, user_id=st.session_state.user["user_id"])
        save_message(st.session_state.session_id, "user", question)
        save_message(st.session_state.session_id, "assistant", answer, steps)

st.markdown(
    "<div class='footer-credit'>اجرا شده به‌صورت محلی با Llama 3.1 · بدون اتصال به اینترنت · Prototype</div>",
    unsafe_allow_html=True
)