import datetime
import pandas as pd
import streamlit as st
import qrcode
import numpy as np
import cv2
import os
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

from database import (
    register_attendee,
    get_all_attendees,
    log_scan,
    get_scan_log,
)

def switch_page(page_name: str):
    st.session_state.page = page_name
    st.experimental_rerun()
# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Conference session definitions with titles and exact times
conference_sessions = [
    {"title": "Prevention of C.M.", "start": "2025-05-02 08:30", "end": "2025-05-02 10:00"},
    {"title": "The TDCJ SO Treatment Program", "start": "2025-05-02 10:30", "end": "2025-05-02 12:00"},
    {"title": "Taking the High Road - Ethical Challenges (Part 1)", "start": "2025-05-02 13:30", "end": "2025-05-02 15:00"},
    {"title": "Taking the High Road - Ethical Challenges (Part 2)", "start": "2025-05-02 15:30", "end": "2025-05-02 17:00"},
    {"title": "Use of Polygraph Exams in Treatment", "start": "2025-05-03 08:30", "end": "2025-05-03 10:00"},
    {"title": "Challenges, Lessons Learned...", "start": "2025-05-03 10:30", "end": "2025-05-03 12:00"},
    {"title": "Treating Clients with Mild Autism", "start": "2025-05-03 13:30", "end": "2025-05-03 15:00"},
    {"title": "Unpacking the Offense Cycle", "start": "2025-05-03 15:30", "end": "2025-05-03 17:00"},
    {"title": "Risk Assessment Reports", "start": "2025-05-04 08:30", "end": "2025-05-04 10:00"},
    {"title": "Chaperon Training", "start": "2025-05-04 10:30", "end": "2025-05-04 12:00"},
    {"title": "Legal and Strategy Aspects of Deregistration", "start": "2025-05-04 13:30", "end": "2025-05-04 15:00"},
    {"title": "RNR Approach to Adolescent Assessment", "start": "2025-05-04 15:30", "end": "2025-05-04 17:00"},
]
import os
import datetime
import pandas as pd
import streamlit as st
import qrcode
import numpy as np
import cv2
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client

# ─── Load .env & initialize Supabase client ───────────────────────────────
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Import your database helper wrappers ──────────────────────────────────
from database import (
    register_attendee,
    get_all_attendees,
    log_scan,
    get_scan_log,
)

# ─── Page‑swap helper ───────────────────────────────────────────────────────
def switch_page(page_name: str):
    st.session_state.page = page_name

# ─── Conference sessions ───────────────────────────────────────────────────
conference_sessions = [
    {"title": "Prevention of C.M.", "start": "2025-05-02 08:30", "end": "2025-05-02 10:00"},
    {"title": "The TDCJ SO Treatment Program", "start": "2025-05-02 10:30", "end": "2025-05-02 12:00"},
    # …and the rest of your sessions…
]

# ─── Init page state ────────────────────────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state.page = 'home'


# ─── Utility functions ─────────────────────────────────────────────────────
def generate_qr_code(badge_id: int) -> bytes:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=2)
    qr.add_data(str(badge_id))
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def run_qr_scanner():
    st.subheader("📷 Scan QR Code")
    img_file = st.camera_input("Point camera at QR code")
    if not img_file:
        return

    img = Image.open(img_file).convert("RGB")
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(gray)
    if not data:
        st.warning("⚠ QR Code not recognized.")
        return

    badge_id = data.strip()
    log_scan(badge_id)

    people = get_all_attendees()
    person = next((p for p in people if p["badge_id"] == int(badge_id)), None)
    name = person["name"] if person else badge_id
    st.success(f"✅ Scanned and checked in: {name}")


def generate_ce_report() -> pd.DataFrame:
    logs = get_scan_log()
    attendees = get_all_attendees()
    attendee_map = {a["badge_id"]: {"Name": a["name"], "Email": a["email"]} for a in attendees}
    report = {}

    for sess in conference_sessions:
        start = datetime.datetime.strptime(sess["start"], "%Y-%m-%d %H:%M")
        end   = datetime.datetime.strptime(sess["end"],   "%Y-%m-%d %H:%M")
        title = sess["title"]

        for log in logs:
            bid = log["badge_id"]
            ts  = log["timestamp"]
            if bid not in attendee_map or not (start <= ts <= end):
                continue
            report.setdefault(bid, {
                "Name":  attendee_map[bid]["Name"],
                "Email": attendee_map[bid]["Email"]
            })[title] = "✅"

    # fill in blanks
    for badge_data in report.values():
        for sess in conference_sessions:
            badge_data.setdefault(sess["title"], "")

    return pd.DataFrame(report.values())

import datetime  # make sure this is imported at the top

import datetime
import pandas as pd

def generate_flattened_log():
    # 1) Fetch registered attendees
    attendees = get_all_attendees()   # list of dicts: { badge_id, name, email, … }
    attendee_map = { int(a["badge_id"]): a for a in attendees }

    # 2) Fetch raw scans
    raw_scans = get_scan_log()        # list of { badge_id, name, email, timestamp }

    # 3) Group scans by badge_id (earliest → latest)
    scans_by = {}
    for entry in sorted(raw_scans, key=lambda x: x["timestamp"]):
        bid = int(entry["badge_id"])
        scans_by.setdefault(bid, []).append(entry["timestamp"])

    # 4) Build a row for every scanned badge
    rows = []
    for bid, times in scans_by.items():
        # look up registration info if it exists
        info = attendee_map.get(bid, {})
        row = {
            "Badge ID": bid,
            "Name":      info.get("name", f"<unregistered {bid}>"),
            "Email":     info.get("email", ""),
        }
        # fill Scan 1…Scan 10
        for i in range(1, 11):
            if i <= len(times):
                row[f"Scan {i}"] = times[i-1].strftime("%Y-%m-%d %H:%M:%S")
            else:
                row[f"Scan {i}"] = ""
        rows.append(row)

    # 5) Sort numerically by badge and return
    rows = sorted(rows, key=lambda r: r["Badge ID"])
    return pd.DataFrame(rows)
# ─── Page layouts ────────────────────────────────────────────────────────────
if st.session_state.page == 'home':
    st.title("📋 Conference Check‑In System")

    # QR scanner
    run_qr_scanner()

    # Manual badge ID
    st.subheader("🔢 Manual Check‑In by Badge ID")
    badge_input = st.text_input("Enter Badge ID", key="manual_badge")
    if st.button("Check In", key="checkin_manual"):
        if badge_input:
            log_scan(badge_input)
            st.success(f"✅ Checked in: {badge_input}")
        else:
            st.warning("Please enter a valid badge ID.")

    # Manual name lookup
    st.subheader("👤 Manual Check‑In by Name")
    people = get_all_attendees()
    names  = [f"{p['name']} ({p['badge_id']})" for p in people]
    selection = st.selectbox("Select Attendee", names, index=0)
    if st.button("Check In Selected", key="checkin_select"):
        bid = int(selection.split("(")[-1].rstrip(")"))
        log_scan(bid)
        name = next(p["name"] for p in people if p["badge_id"] == bid)
        st.success(f"✅ Checked in: {name} ({bid})")

    # Go to Admin
    if st.button("🔐 Admin Area"):
        switch_page('admin')


elif st.session_state.page == 'admin':
    st.title("🔐 Admin – Attendance Dashboard")

    df_all = generate_flattened_log()

    st.subheader("👥 All Registered Attendees")
    st.write(f"Showing {len(df_all)} attendees in numeric order")
    st.dataframe(df_all)
    st.download_button(
    "📥 Download Full Attendee List",
    df_all.to_csv(index=False).encode("utf-8"),
    file_name="all_attendees.csv"
)

    st.markdown("---")

    # CE Credit report
    st.subheader("📜 CE Credit Attendance Report")
    df_ce = generate_ce_report()
    st.dataframe(df_ce)
    st.download_button("📥 Download CE Credit Report",
                       df_ce.to_csv(index=False).encode("utf-8"),
                       file_name="ce_credits.csv")

    st.markdown("---")

    
    st.subheader("📊 Raw Attendance Log")
    raw = get_scan_log()
    df_raw = pd.DataFrame(raw)
    st.dataframe(df_raw)
    st.download_button(
    "📥 Download Raw Attendance Log",
    df_raw.to_csv(index=False).encode("utf-8"),
    file_name="raw_attendance.csv"
)



    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Register New Attendee"):
            switch_page('register')
    with col2:
        if st.button("⬅ Back to Home"):
            switch_page('home')


elif st.session_state.page == 'register':
    st.title("➕ Register New Attendee")

    name     = st.text_input("Full Name")
    email    = st.text_input("Email")
    badge_id = st.number_input("Assign a Unique Badge ID", min_value=1, step=1)

    if st.button("Register"):
        if name and email and badge_id:
            register_attendee(badge_id, name, email)
            st.success(f"🎉 Registered {name}")
            qr = generate_qr_code(badge_id)
            st.image(qr, caption=f"QR Code for {name}")
        else:
            st.warning("Please fill in all fields.")

    if st.button("⬅ Back to Admin"):
        switch_page('admin')
