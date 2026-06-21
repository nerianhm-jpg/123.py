import streamlit as st
import os
import time
import io
import requests
import re
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError

# הגדרת עמוד רחב ומראה מודרני מינימליסטי לקצה
st.set_page_config(page_title="SummarizeAI Pro", page_icon="🎙️", layout="wide")

# ==========================================
# 1. הגדרות קישור ל-Firebase
# ==========================================
FIREBASE_WEB_API_KEY = st.secrets["api_keys"]["firebase"]
FIREBASE_PROJECT_ID = st.secrets["api_keys"].get("firebase_project_id", "summarizeai-pro")

# ==========================================
# 2. עיצוב פרימיום ו-CSS מיושר מימין לשמאל (סיידבר משמאל)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');

    /* הגדרת כיוון גלובלי מימין לשמאל לכל האפליקציה */
    html, body {
        font-family: 'Heebo', sans-serif !important;
        background-color: #F8F9FA !important;
        direction: rtl !important;
    }

    /* העברת הסיידבר לצד שמאל על ידי הפיכת כיוון המכולה הראשית */
    [data-testid="stAppViewContainer"] {
        flex-direction: row-reverse !important;
    }

    /* הגבלת רוחב מדויקת ומירכוז הממשק למראה יוקרתי */
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
        color: #1A1D20;
        direction: rtl !important;
        text-align: right !important;
        padding-top: 60px !important;
        max-width: 860px !important; 
        margin: 0 auto !important;
    }

    /* עיצוב סיידבר נקי ומקצועי בצד שמאל */
    [data-testid="stSidebar"] {
        font-family: 'Heebo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
        background-color: #FFFFFF !important;
        border-right: 1px solid #ECEFF1 !important;
        border-left: none !important;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02) !important;
    }

    [data-testid="stSidebarUserContent"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* כותרות פרימיום */
    h1 {
        text-align: center !important;
        color: #101828;
        font-weight: 700 !important;
        font-size: 40px !important;
        letter-spacing: -0.8px;
        margin-bottom: 8px !important;
        direction: rtl !important;
    }

    .subtitle {
        text-align: center !important;
        color: #667085;
        font-size: 16px;
        font-weight: 400;
        margin-bottom: 50px;
        direction: rtl !important;
    }

    /* עיצוב כפתורים מעוגלים ויוקרתיים */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 48px; 
        background-color: #0052FF;
        color: white;
        font-weight: 500;
        font-size: 15px; 
        border: none;
        cursor: pointer;
        box-shadow: 0px 1px 2px rgba(16, 24, 40, 0.05);
        transition: all 0.2s ease-in-out;
        direction: rtl !important;
    }
    .stButton>button:hover {
        background-color: #0045D8;
        box-shadow: 0px 4px 8px rgba(0, 82, 255, 0.15);
        transform: translateY(-1px);
    }

    div[data-testid="stDownloadButton"] > button {
        width: 100%;
        border-radius: 12px;
        height: 48px; 
        background-color: #FFFFFF !important;
        color: #344054 !important;
        font-weight: 500;
        font-size: 15px; 
        border: 1px solid #D0D5DD !important;
        box-shadow: 0px 1px 2px rgba(16, 24, 40, 0.05);
        transition: all 0.2s ease-in-out;
        direction: rtl !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #F9FAFB !important;
        border-color: #C7CCD6 !important;
    }

    /* תיבות מידע ונתונים */
    .metric-card {
        background: #FFFFFF;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0px 1px 3px rgba(16, 24, 40, 0.05);
        border: 1px solid #E4E7EC;
        text-align: right;
        margin-bottom: 15px;
        direction: rtl !important;
    }
    .metric-label {
        font-size: 12px;
        color: #667085;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 15px;
        color: #101828;
        font-weight: 600;
    }

    /* תיבת הדו"ח והסיכום המרכזית */
    .summary-card {
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0px 2px 12px rgba(16, 24, 40, 0.03);
        width: 100%;
        margin: 15px auto;
        text-align: right;
        font-size: 16px;
        color: #344054;
        line-height: 1.8;
        border: 1px solid #EAECF0;
        direction: rtl !important;
    }

    /* בועות צ'אט מעוצבות בסגנון מודרני */
    .chat-bubble-user {
        background-color: #0052FF;
        color: white;
        padding: 12px 18px;
        border-radius: 16px 16px 0px 16px;
        margin-bottom: 14px;
        max-width: 80%;
        margin-right: auto;
        text-align: right;
        box-shadow: 0px 2px 4px rgba(0, 52, 255, 0.1);
        direction: rtl !important;
    }
    .chat-bubble-ai {
        background-color: #FFFFFF;
        color: #1D2939;
        padding: 12px 18px;
        border-radius: 16px 16px 16px 0px;
        margin-bottom: 14px;
        max-width: 80%;
        margin-left: auto;
        text-align: right;
        border: 1px solid #EAECF0;
        box-shadow: 0px 1px 2px rgba(16, 24, 40, 0.03);
        direction: rtl !important;
    }

    /* היסטוריית שיחות */
    .history-card {
        background-color: #F9FAFB;
        padding: 12px 14px;
        border-radius: 8px;
        font-size: 14px;
        direction: rtl !important;
        text-align: right !important;
        margin-bottom: 8px;
        border: 1px solid #F2F4F7;
    }

    .sidebar-title {
        font-size: 15px;
        font-weight: 600;
        color: #344054;
        margin-bottom: 15px;
        border-bottom: 1px solid #F2F4F7;
        padding-bottom: 8px;
        margin-top: 25px;
        direction: rtl !important;
        text-align: center !important;
    }

    /* אזור העלאת קבצים */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #EAECF0 !important;
        border-radius: 14px !important;
        padding: 20px !important;
        box-shadow: 0px 1px 2px rgba(16, 24, 40, 0.02);
        direction: rtl !important;
    }

    .status-text-custom {
        color: #475467 !important; 
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 10px;
        text-align: center;
        direction: rtl !important;
    }

    /* עיצוב שדות קלט ותיבות בחירה מיושרים לימין */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] select, div[data-testid="stTextArea"] textarea {
        border-radius: 10px !important;
        border: 1px solid #D0D5DD !important;
        background-color: #FFFFFF !important;
        direction: rtl !important;
        text-align: right !important;
        font-size: 15px !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        direction: rtl !important;
        text-align: right !important;
    }

    div[data-baseweb="popover"] ul, div[data-baseweb="menu"] li, [role="listbox"] li {
        direction: rtl !important;
        text-align: right !important;
    }

    div[data-testid="stTextInput"] input:focus, div[data-testid="stSelectbox"] select:focus, div[data-testid="stTextArea"] textarea:focus {
        border-color: #0052FF !important;
        box-shadow: 0px 0px 0px 4px rgba(0, 82, 255, 0.1) !important;
    }

    /* התאמות לטאבים מרכזיים */
    div[data-testid="stTabs"] {
        direction: rtl !important;
        border-bottom: 1px solid #EAECF0 !important;
    }
    div[data-testid="stTabs"] button {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #667085;
        direction: rtl !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #0052FF !important;
    }

    div[data-testid="stProgress"] > div > div {
        background-color: #0052FF !important;
        height: 6px !important;
        border-radius: 4px;
    }

    div[data-testid="stNotification"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* קלאסים מותאמים אישית למרכוס מלא */
    .center-text {
        text-align: center !important;
        direction: rtl !important;
        width: 100%;
        display: block;
    }
    .center-bold-title {
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 24px !important;
        margin-top: 20px !important;
        margin-bottom: 15px !important;
        color: #101828;
        direction: rtl !important;
        width: 100%;
        display: block;
    }

    /* מכולה ייעודית למרכוס מוחלט של אזור המשוב */
    .feedback-center-container {
        direction: rtl !important;
        text-align: center !important;
        max-width: 600px !important;
        margin: 0 auto !important;
        padding-top: 20px;
    }
    /* קלאס חדש למרכז את הכפתור */
    .centered-button-container {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. פונקציות עזר ואימות (Firebase & Sanitization)
# ==========================================
def clean_ai_markdown_tags(text):
    """מנקה תגיות מרקדאון מיותרות שה-AI לפעמים מחזיר בטעות בתחילת הטקסט"""
    if not text:
        return ""
    cleaned = re.sub(r"^```markdown\s*", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned)
    cleaned = re.sub(r"^\s*#\s*.*?\n", "", cleaned)
    return cleaned.strip()

def send_verification_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
    payload = {"requestType": "VERIFY_EMAIL", "idToken": id_token}
    try:
        requests.post(url, json=payload, timeout=7)
    except:
        pass

def check_user_details(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_WEB_API_KEY}"
    payload = {"idToken": id_token}
    try:
        response = requests.post(url, json=payload, timeout=7)
        if response.status_code == 200:
            users = response.json().get('users', [])
            if users: return users[0]
    except:
        pass
    return None

def firebase_sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        response = requests.post(url, json=payload, timeout=7)
        if response.status_code == 200:
            res_data = response.json()
            user_details = check_user_details(res_data["idToken"])
            if user_details and not user_details.get("emailVerified", False):
                send_verification_email(res_data["idToken"])
                raise Exception("החשבון שלך טרם אומת. שלחנו לך קישור אימות חדש לתיבת המייל, אנא אשר אותו והתחבר שוב.")
            return res_data
        else:
            error_msg = response.json().get('error', {}).get('message', '')
            if error_msg in ["INVALID_PASSWORD", "EMAIL_NOT_FOUND", "INVALID_EMAIL"]:
                raise Exception("כתובת האימייל או הסיסמה שהזנת אינם נכונים.")
            raise Exception("לא הצלחנו לחבר אותך לחשבון, אנא ודא שהפרטים נכונים ונסה שוב.")
    except Exception as e:
        raise Exception(str(e))

def firebase_sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        response = requests.post(url, json=payload, timeout=7)
        if response.status_code == 200:
            res_data = response.json()
            send_verification_email(res_data["idToken"])
            return res_data
        else:
            error_msg = response.json().get('error', {}).get('message', '')
            if error_msg == "EMAIL_EXISTS":
                raise Exception("כתובת האימייל הזו כבר רשומה במערכת.")
            raise Exception("ההרשמה נכשלה. אנא ודא שהאימייל תקין והסיסמה מכילה לפחות 6 תווים.")
    except Exception as e:
        raise Exception(str(e))

def save_to_firestore(user_id, filename, transcript, summary):
    doc_id = str(int(time.time() * 1000))
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/calls/{doc_id}"

    # שליפת ה-token של המשתמש המחובר
    id_token = st.session_state.get("user", {}).get("idToken", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }

    payload = {
        "fields": {
            "id": {"stringValue": doc_id},
            "user_id": {"stringValue": user_id},
            "date": {"stringValue": datetime.now().strftime("%d/%m/%Y %H:%M")},
            "filename": {"stringValue": filename},
            "transcript": {"stringValue": transcript},
            "summary": {"stringValue": summary}
        }
    }
    try:
        requests.patch(url, json=payload, headers=headers, timeout=10)
    except:
        pass

def save_feedback_to_firestore(email, rating, feedback_text):
    """
    *** התיקון המרכזי ***
    הוספנו Authorization header עם ה-idToken של המשתמש המחובר.
    בלי זה Firebase דחה את הבקשה בשקט ולכן המשוב לא נשמר.
    """
    doc_id = str(int(time.time() * 1000))
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/feedbacks/{doc_id}"

    # שליפת ה-token של המשתמש המחובר
    id_token = st.session_state.get("user", {}).get("idToken", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }

    payload = {
        "fields": {
            "id": {"stringValue": doc_id},
            "email": {"stringValue": email},
            "date": {"stringValue": datetime.now().strftime("%d/%m/%Y %H:%M")},
            "rating": {"stringValue": rating},
            "text": {"stringValue": feedback_text}
        }
    }
    try:
        response = requests.patch(url, json=payload, headers=headers, timeout=10)
        # בדיקת תגובה מפורטת לאיתור שגיאות
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"שגיאת Firebase: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"שגיאת רשת: {str(e)}")
        return False

def load_history_from_firestore(user_id):
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents:runQuery"

    id_token = st.session_state.get("user", {}).get("idToken", "")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }

    query = {
        "structuredQuery": {
            "from": [{"collectionId": "calls"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "user_id"},
                    "op": "EQUAL",
                    "value": {"stringValue": user_id}
                }
            }
        }
    }
    try:
        response = requests.post(url, json=query, headers=headers, timeout=10)
        if response.status_code == 200:
            results = response.json()
            history = []
            for item in results:
                if "document" in item:
                    fields = item["document"]["fields"]
                    history.append({
                        "id": fields["id"]["stringValue"],
                        "user_id": fields["user_id"]["stringValue"],
                        "date": fields["date"]["stringValue"],
                        "filename": fields["filename"]["stringValue"],
                        "transcript": fields["transcript"]["stringValue"],
                        "summary": fields["summary"]["stringValue"]
                    })
            history.sort(key=lambda x: x['id'], reverse=True)
            return history
    except:
        return []
    return []

def delete_from_firestore(doc_id):
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/calls/{doc_id}"

    id_token = st.session_state.get("user", {}).get("idToken", "")
    headers = {"Authorization": f"Bearer {id_token}"}

    try:
        requests.delete(url, headers=headers, timeout=10)
    except:
        pass

def generate_word_html(title, markdown_text):
    clean_text = markdown_text.replace("\n", "<br>").replace("###", "<h3>").replace("**", "<b>")
    return f"""
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial; direction: rtl; text-align: right;">{clean_text}</body>
    </html>
    """

# ==========================================
# 4. מנגנון כניסה והרשמה
# ==========================================
if "user" not in st.session_state:
    st.session_state["user"] = None

# הגדר את המקסימום של גודל הקובץ ל-1GB
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB בייטים

# פונקציה לבדוק את גודל הקובץ לפני שמעלים
def handle_file_upload(uploaded_file):
    # קריאת כל הקובץ ל-binary כדי לבדוק את הגודל
    file_bytes = uploaded_file.read()
    # החזרת מיקום קריאה חזרה ל־`uploaded_file` כדי שתוכל להשתמש בו בהמשך
    uploaded_file.seek(0)
    if len(file_bytes) > MAX_FILE_SIZE:
        st.error("הקובץ גדול מידי! המקסימום הוא 1GB.")
        return False
    return True

# כאן נבצע בדיקת חיבור במקום בכל פעם מחדש
# אם המשתמש לא מחובר, נציג את מסך ההתחברות והרשמה
if st.session_state["user"] is None:
    st.write("")
    st.markdown("<h1>🎙️ SummarizeAI Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>מערכת בינה מלאכותית לניתוח, תמלול וסיכום פגישות אוטומטי</p>", unsafe_allow_html=True)

    col_lock, col_tabs, col_lock2 = st.columns([0.3, 3.4, 0.3])
    with col_tabs:
        tab_login, tab_register = st.tabs(["🔐 כניסה למערכת", "✨ הרשמת משתמש חדש"])

        with tab_login:
            st.write("")
            login_email = st.text_input("כתובת אימייל", key="login_email")
            login_password = st.text_input("סיסמה", type="password", key="login_password")
            st.write("")
            if st.button("התחבר לחשבון", key="btn_execute_login", use_container_width=True):
                if not login_email or not login_password:
                    st.error("אנא מלא את כל השדות המבוקשים.")
                else:
                    with st.spinner("מתחבר לחשבון, אנא המתן..."):
                        try:
                            user_data = firebase_sign_in(login_email, login_password)
                            st.session_state["user"] = user_data
                            st.success("התחברת בהצלחה!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"{str(e)}")

        with tab_register:
            st.write("")
            reg_email = st.text_input("כתובת אימייל חדשה", key="reg_email")
            reg_password = st.text_input("סיסמה מאובטחת (לפחות 6 תווים)", type="password", key="reg_password")
            st.write("")
            if st.button("צור חשבון חדש והתחל", key="btn_execute_register", use_container_width=True):
                if not reg_email:
                    st.error("אנא מלא את כל השדות המבוקשים.")
                elif len(reg_password) < 6:
                    st.error("הסיסמה חייבת להכיל 6 תווים לפחות.")
                else:
                    with st.spinner("מקים את החשבון החדש שלך..."):
                        try:
                            firebase_sign_up(reg_email, reg_password)
                            st.info("החשבון נוצר בהצלחה! שלחנו לך קישור אימות לתיבת המייל. אנא כנס להודעה, לחץ על הקישור ולאחר מכן חזור לכאן כדי להתחבר.")
                        except Exception as e:
                            st.error(f"{str(e)}")
    st.stop()

# אם המשתמש מחובר, נשמור את ה-ID שלו למשתנה
current_user_id = st.session_state["user"]["localId"]
current_user_email = st.session_state["user"]["email"]

# =========================
# 6. היסטוריית שיחות ונתוני חשבון בסיידבר (בצד שמאל)
# ==========================
with st.sidebar:
    st.markdown(
        f'<p style="font-size:13px; color:#475467; text-align:center; font-weight:500; margin-top:10px; direction: rtl !important;">👤 {current_user_email}</p>',
        unsafe_allow_html=True)
    if st.button("🚪 התנתק מהחשבון", use_container_width=True):
        st.session_state["user"] = None
        if 'chat_history' in st.session_state: del st.session_state['chat_history']
        st.rerun()

    st.write("")
    st.markdown('<p class="sidebar-title">🕒 היסטוריית השיחות שלך</p>', unsafe_allow_html=True)
    user_history = load_history_from_firestore(current_user_id)

    if not user_history:
        st.markdown('<p style="text-align: center;">אין עדיין שיחות שמורות בחשבון זה.</p>', unsafe_allow_html=True)

    for entry in user_history:
        st.markdown(f"""
        <div class="history-card">
            <strong>📅 {entry['date']}</strong><br>
            <small>📄 {entry['filename'][:18]}...</small>
        </div>
        """, unsafe_allow_html=True)

        col_view, col_del = st.columns([3, 1])
        with col_view:
            if st.button("פתח שיחה", key=f"btn_view_{entry['id']}", use_container_width=True):
                st.session_state['view_entry'] = entry
                if 'chat_history' in st.session_state: del st.session_state['chat_history']
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"btn_del_{entry['id']}", use_container_width=True):
                delete_from_firestore(entry['id'])
                if 'view_entry' in st.session_state and st.session_state['view_entry']['id'] == entry['id']:
                    del st.session_state['view_entry']
                    if 'chat_history' in st.session_state: del st.session_state['chat_history']
                st.success("השיחה נמחקה.")
                time.sleep(0.5)
                st.rerun()

# =========================
# 7. המסך המרכזי
# ==========================
st.markdown('<h1>🎙️ SummarizeAI Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">הופכים קבצי קול ווידאו לסיכומים מדויקים ומשימות בשניות</p>', unsafe_allow_html=True)

main_tabs = st.tabs(["🚀 ניתוח קובץ חדש", "💬 שליחת משוב והצעות"])

with main_tabs[0]:
    if 'view_entry' in st.session_state:
        entry = st.session_state['view_entry']

        if st.button("⬅️ חזרה להעלאת קובץ חדש"):
            del st.session_state['view_entry']
            if 'chat_history' in st.session_state: del st.session_state['chat_history']
            st.rerun()

        st.write("")

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">📄 שם הקובץ</div><div class="metric-value">{entry["filename"][:18]}...</div></div>',
                unsafe_allow_html=True)
        with m_col2:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">📅 תאריך הניתוח</div><div class="metric-value">{entry["date"]}</div></div>',
                unsafe_allow_html=True)
        with m_col3:
            st.markdown(
                '<div class="metric-card"><div class="metric-label">🤖 מנוע בינה מלאכותית</div><div class="metric-value">Gemini 2.5 Flash</div></div>',
                unsafe_allow_html=True)

        tab_summary, tab_transcript, tab_chat = st.tabs(
            ['📊 דו"ח סיכום ומנהלים', '📄 תמלול מלא של המילים', '💬 שאלות ותשובות על השיחה'])

        with tab_summary:
            st.markdown(
                '<p class="center-bold-title">דו"ח סיכום מנהלים</p>',
                unsafe_allow_html=True)

            clean_summary = clean_ai_markdown_tags(entry["summary"])
            st.markdown(f'<div class="summary-card">{clean_summary}</div>', unsafe_allow_html=True)
            st.write("")

            c1, c2 = st.columns(2)
            with c1:
                word_doc = generate_word_html(entry['filename'], clean_summary)
                st.download_button('📥 הורד את הדו"ח כקובץ Word', word_doc, file_name=f"Summary_{entry['id']}.doc",
                                   mime="application/msword", use_container_width=True)
            with c2:
                if st.button('🖨️ הדפס דו"ח או שמור כ-PDF', use_container_width=True):
                    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

        with tab_transcript:
            st.text_area("", entry['transcript'], height=450)

        with tab_chat:
            st.markdown('<p class="center-bold-title">💬 התייעצות חכמה על תוכן השיחה</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="center-text">כאן תוכל לשאול את הבינה המלאכותית שאלות ספציפיות על מה שנאמר בפגישה.</p>',
                unsafe_allow_html=True)
            st.write("")

            if 'chat_history' not in st.session_state:
                st.session_state['chat_history'] = []

            for msg in st.session_state['chat_history']:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-bubble-user">{msg["text"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-ai">{msg["text"]}</div>', unsafe_allow_html=True)

            chat_input = st.text_input("הקלד את השאלה שלך כאן:", key="chat_input_field")

            if st.button("שלח שאלה", key="btn_send_chat"):
                if chat_input:
                    st.session_state['chat_history'].append({'role': 'user', 'text': chat_input})

                    history_context = ""
                    for prev_msg in st.session_state['chat_history'][:-1]:
                        speaker = "משתמש" if prev_msg['role'] == 'user' else "עוזר AI"
                        history_context += f"{speaker}: {prev_msg['text']}\n"

                    chat_prompt = f"""
                    אתה עוזר משרדי אינטליגנטי. המשתמש מנהל איתך שיחה מתמשכת על פגישה שהתרחשה.
                    להלן התמלול המלא של הפגישה:
                    ---
                    {entry['transcript']}
                    ---
                    להלן היסטוריית הדו-שיח הקודם ביניכם:
                    {history_context}
                    ---
                    השאלה החדשה של המשתמש: {chat_input}
                    ענה לו בעברית בצורה ישירה על בסיס נתוני השיחה.
                    """

                    with st.spinner("מנסח תשובה..."):
                        try:
                            chat_response = client.models.generate_content(model=MODEL_NAME, contents=chat_prompt)
                            st.session_state['chat_history'].append(
                                {'role': 'ai', 'text': clean_ai_markdown_tags(chat_response.text)})
                            st.rerun()
                        except Exception as e:
                            st.error("לא הצלחנו לקבל תשובה מהצ'אט, אנא נסה שוב.")

    else:
        # בחירת סגנון סיכום
        summary_style = st.selectbox(
            "📋 בחר את סגנון הסיכום הרצוי:",
            [
                "📊 סיכום מנהלים מלא (כולל נקודות מפתח ומשימות)",
                "📋 רשימת משימות ויעדים (Action Items) בלבד",
                "⚖️ פרוטוקול פגישה רשמי ומורחב"
            ]
        )

        st.write("")
        uploaded_file = st.file_uploader(
            "גרור או בחר קובץ שמע או וידאו של השיחה",
            type=["mp3", "wav", "m4a", "mp4", "mpeg", "mkv", "avi"]
        )

        # בודק את גודל הקובץ לפני שממשיך
        if uploaded_file is not None and handle_file_upload(uploaded_file):
            st.write("")
            start_analysis = st.button("🚀 התחל ניתוח שיחה אוטומטי")
            st.write("")

            if start_analysis:
                text_placeholder = st.empty()
                progress_bar = st.progress(0)

                text_placeholder.markdown('<p class="status-text-custom">⏳ טוען את קובץ השמע למערכת... (0%)</p>',
                                          unsafe_allow_html=True)
                file_bytes = uploaded_file.read()
                file_io = io.BytesIO(file_bytes)

                text_placeholder.markdown('<p class="status-text-custom">🎧 מעלה את הקובץ לעיבוד מאובטח... (25%)</p>',
                                          unsafe_allow_html=True)
                progress_bar.progress(25)

                _, ext = os.path.splitext(uploaded_file.name)
                # ניקוי שם הקובץ לפני ההעלאה
                clean_api_name = f"audio_input{ext}"

                try:
                    audio_file = client.files.upload(
                        file=file_io,
                        config=types.UploadFileConfig(mime_type=uploaded_file.type, display_name=clean_api_name)
                    )
                except Exception as e:
                    st.error("העלאת הקובץ נכשלה, אנא ודא שהקובץ תקין ונסה שוב.")
                    st.stop()

                # מעקב אחר מצב הקובץ
                current_pct = 25
                while audio_file.state.name == "PROCESSING":
                    if current_pct < 60:
                        current_pct += 5
                    text_placeholder.markdown(
                        f'<p class="status-text-custom">🔄 מנוע הבינה המלאכותית מפענח ומנתח את השיחה... ({current_pct}%)</p>',
                        unsafe_allow_html=True)
                    progress_bar.progress(current_pct)
                    time.sleep(4)
                    audio_file = client.files.get(name=audio_file.name)

                if audio_file.state.name == "FAILED":
                    st.error("עיבוד קובץ המדיה נכשל על ידי השרת.")
                    st.stop()

                # המשך תהליך התמלול והסיכום כפי שהיה
                text_placeholder.markdown('<p class="status-text-custom">📝 מתמלל ומקליד את המילים לעברית... (70%)</p>',
                                          unsafe_allow_html=True)
                progress_bar.progress(70)

                diarization_prompt = """
                תמלל את קובץ השמע הזה מילה במילה לעברית בצורה נקייה ומלאה.
                נתח את קובץ השמע. אם אתה מזהה בבירור שיש שני דוברים או יותר שמנהלים דיאלוג, פצל את התמלול לפי שורות והוסף תגיות בולטות של דוברים בתחילת כל קטע בצורה הבאה:
                **דובר א':** [מה שהוא אמר]
                **דובר ב':** [מה שהוא ענה]
                לעומת זאת, אם מדובר באדם אחד בלבד שמדבר, אל תוסיף תגיות דוברים כלל, וכתוב את התמליל כטקסט רציף המחולק לפסקאות הגיוניות.
                אין להוסיף שום סיכומים או הערות אישיות, רק את התמליל הגולמי המדויק.
                """

                transcript = None
                for attempt in range(4):
                    try:
                        transcript_response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=[audio_file, diarization_prompt]
                        )
                        transcript = transcript_response.text
                        if transcript: break
                    except Exception as e:
                        if attempt < 3:
                            time.sleep((attempt + 1) * 4)
                        else:
                            st.error("תהליך התמלול נכשל זמנית, אנא נסה שוב.")
                            st.stop()

                if transcript:
                    text_placeholder.markdown(
                        '<p class="status-text-custom">🧠 מנסח ומפיק את דו"ח הסיכום המבוקש... (90%)</p>',
                        unsafe_allow_html=True)
                    progress_bar.progress(90)

                    style_instruction = ""
                    if "רשימת משימות" in summary_style:
                        style_instruction = "התמקד אך ורק בחלק של טבלת המשימות (Action Items). אל תציג סיכומים ארוכים, אלא טבלה מפורטת במיוחד של מי עושה מה ומתי."
                    elif "פרוטוקול פגישה" in summary_style:
                        style_instruction = "עליך להפיק פרוטוקול משפטי/עסקי רשמי ומפורט. תעד כל נושא שעלה בהרחבה, מי העלה אותו, מה היו הטיעונים ומה הוחלט בסעיף זה."
                    else:
                        style_instruction = "הפק דו\"ח סיכום מנהלים קלאסי ומאוזן הכולל תעודת זהות של השיחה, תקציר, נקודות מפתח וטבלת משימות."

                    prompt = f"""
                    תפקידך הוא אנליסט עסקי ומנהל פרויקטים בכיר (PMO). 
                    לפניך טקסט שהופק מתמלול אוטומטי של פגישה בעברית.
                    ההנחיה הספציפית לסגנון הדו"ח המבוקש היא: {style_instruction}
                    השתמש בפורמט Markdown עשיר ומאורגן היטב, כולל כותרות בולטות ואימוג'ים מתאימים.
                    ---
                    טקסט התמלול הגולמי לעיבוד:
                    {transcript}
                    """

                    summary = None
                    for attempt in range(4):
                        try:
                            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                            summary = response.text
                            if summary: break
                        except Exception as e:
                            if attempt < 3:
                                time.sleep((attempt + 1) * 4)
                            else:
                                st.error("בניית הסיכום נכשלה, אנא נסה שוב.")
                                st.stop()

                    text_placeholder.markdown('<p class="status-text-custom">✨ הניתוח הושלם בהצלחה! (100%)</p>',
                                              unsafe_allow_html=True)
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    text_placeholder.empty()
                    progress_bar.empty()

                    if summary:
                        clean_summary = clean_ai_markdown_tags(summary)
                        save_to_firestore(current_user_id, uploaded_file.name, transcript, clean_summary)
                        st.session_state['view_entry'] = {
                            "id": str(int(time.time() * 1000)),
                            "filename": uploaded_file.name,
                            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "summary": clean_summary,
                            "transcript": transcript
                        }
                        st.rerun()

                try:
                    client.files.delete(name=audio_file.name)
                except:
                    pass

# =========================
# 8. חלק המשוב והקישור
# ==========================
with main_tabs[1]:
    # החלף את חלק המשוב עם קישור
    st.markdown('<div class="feedback-center-container">', unsafe_allow_html=True)
    st.markdown('<p class="center-bold-title">נשמח לשמוע את דעתך על המערכת</p>', unsafe_allow_html=True)
    # הכפתור במרכז באמצעות קלאס חדש
    st.markdown(
        '<div class="centered-button-container">'
        '<a href="https://docs.google.com/forms/d/e/1FAIpQLSe-ORjIfre2hNfsI7u8INywzG1w1QLY3x-1jeRz6zZnqnQ_lg/viewform?usp=dialog" '
        'target="_blank" '
        'style="display:inline-block;padding:10px 20px;background-color:#0052FF;color:white;border-radius:12px;text-decoration:none;font-weight:500;font-size:16px;">לחץ כאן למילוי המשוב</a>'
        '</div>',
        unsafe_allow_html=True)
    st.markdown('<p class="center-text">המשוב שלך מגיע ישירות אלינו ועוזר לנו לשפר ולפתח את האפליקציה.</p>', unsafe_allow_html=True)
    st.write("")
