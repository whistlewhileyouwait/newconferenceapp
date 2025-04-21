import streamlit as st
from database import register_attendee, get_all_attendees, log_scan, get_scan_log
import qrcode
from io import BytesIO
import datetime
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np
import cv2

# --------------------------
# ✅ CE Session Schedule
# --------------------------
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

# --------------------------
# ✅ Session Setup
# --------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --------------------------
# ✅ Helper Functions
# --------------------------
def switch_page(page_name):
    st.session_state.page = page_name

def generate_qr_code(badge_id):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(str(badge_id))
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def run_qr_scanner():
    st.subheader("📷 Scan QR Code")
    img_file = st.camera_input("Point camera at QR code")

    if img_file:
        img = Image.open(img_file)
        img = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        decoded = decode(gray)

        if decoded:
            qr_data = decoded[0].data.decode("utf-8")
            log_scan(qr_data)
            st.success(f"✅ Scanned and checked in: {qr_data}")
        else:
            st.warning("⚠ QR Code not recognized.")

def generate_ce_report():
    logs = get_scan_log()
    attendees = get_all_attendees()
    attendee_map = {a.badge_id: {"Name": a.name, "Email": a.email} for a in attendees}
    report = {}

    for session in conference_sessions:
        session_start = datetime.datetime.strptime(session["start"], "%Y-%m-%d %H:%M")
        session_end = datetime.datetime.strptime(session["end"], "%Y-%m-%d %H:%M")
        session_title = session["title"]

        for log in logs:
            badge = log.badge_id
            if badge not in attendee_map:
                continue
            if session_start <= log.timestamp <= session_end:
                if badge not in report:
                    report[badge] = {
                        "Name": attendee_map[badge]["Name"],
                        "Email": attendee_map[badge]["Email"]
                    }
                report[badge][session_title] = "✅"

    for badge in report:
        for session in conference_sessions:
            title = session["title"]
            if title not in report[badge]:
                report[badge][title] = ""

    return pd.DataFrame(report.values())
def generate_flattened_log():
    attendees = get_all_attendees()
    rows = []
    for a in attendees:
        # only include folks who have at least one scan
        scans = [getattr(a, f"scan{i}") for i in range(1, 11)]
        if not any(scans):
            continue

        row = {
            "Badge ID": a.badge_id,
            "Name":     a.name,
            "Email":    a.email,
        }
        for i, ts in enumerate(scans, start=1):
            row[f"Scan {i}"] = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
        rows.append(row)

    return pd.DataFrame(rows)


# --------------------------
# ✅ Pages
# --------------------------
if st.session_state.page == 'home':
    st.title("📋 Conference Check-In System")
    run_qr_scanner()

    st.subheader("🔢 Manual Check-In by Badge ID")
    badge_input = st.text_input("Enter Badge ID", key="manual_badge")
    if st.button("Check In", key="checkin_manual"):
        if badge_input:
            log_scan(badge_input)
            st.success(f"✅ Checked in: {badge_input}")
        else:
            st.warning("Please enter a valid badge ID.")

    st.subheader("👤 Manual Check-In by Name")
    attendees = get_all_attendees()
    names = [f"{a.name} ({a.badge_id})" for a in attendees]
    selection = st.selectbox("Select Attendee", names, index=None, placeholder="Choose attendee")
    if st.button("Check In Selected", key="checkin_select"):
        if selection:
            badge_id = selection.split("(")[-1].rstrip(")")
            log_scan(badge_id)
            st.success(f"✅ Checked in: {badge_id}")
        else:
            st.warning("Please select a name.")

    if st.button("🔐 Admin Area"):
        switch_page('admin')

elif st.session_state.page == 'admin':
    st.title("🔐 Admin – Attendance Dashboard")

    # 👥 All Registered Attendees (one row per person, scan1…scan10)
    st.subheader("👥 All Registered Attendees")
    attendees = get_all_attendees()
    rows = []
    for a in attendees:
        row = {
            "Badge ID": a.badge_id,
            "Name":     a.name,
            "Email":    a.email,
        }
        # pull in scan1…scan10 (they may be None)
        for i in range(1, 11):
            ts = getattr(a, f"scan{i}")
            row[f"Scan {i}"] = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else ""
        rows.append(row)

    df_all = pd.DataFrame(rows)
    st.dataframe(df_all)
    st.download_button(
        "📥 Download Full Attendee List",
        data=df_all.to_csv(index=False).encode("utf-8"),
        file_name="all_attendees.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # …then your CE report, raw/log sections, and nav buttons below…


    # -- CE Credit Report Section --
    st.subheader("📜 CE Credit Attendance Report")
    ce_report_df = generate_ce_report()
    st.dataframe(ce_report_df)

    st.download_button(
        label="📥 Download CE Credit Report",
        data=ce_report_df.to_csv(index=False).encode("utf-8"),
        file_name="ce_credits.csv",
        mime="text/csv"
    )

    st.markdown("---")  # Divider

    # -- Raw Attendance Log Section (flattened) --
    st.subheader("📊 Raw Attendance Log")
    df_log = generate_flattened_log()
    st.dataframe(df_log)

    st.download_button(
        label="📥 Download Raw Attendance Log",
        data=df_log.to_csv(index=False).encode("utf-8"),
        file_name="raw_attendance.csv",
        mime="text/csv"
    )


    st.markdown("---")  # Divider

    # -- Navigation Buttons --
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Register New Attendee"):
            switch_page('register')
    with col2:
        if st.button("⬅ Back to Home"):
            switch_page('home')
elif st.session_state.page == 'register':
    st.title("➕ Register New Attendee")

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    badge_id = st.text_input("Assign a Unique Badge ID")

    if st.button("Register"):
        if name and email and badge_id:
            try:
                register_attendee(badge_id, name, email)
                st.success(f"🎉 Registered {name}")
                st.image(generate_qr_code(badge_id), caption=f"QR Code for {name}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Please fill in all fields.")

    if st.button("⬅ Back to Admin"):
        switch_page('admin')
