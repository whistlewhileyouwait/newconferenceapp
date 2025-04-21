import streamlit as st
import pandas as pd
import datetime
import qrcode
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
import os

# File to store attendee data
ATTENDEE_FILE = "attendees.csv"

# Function to load data from CSV
def load_data():
    if os.path.exists(ATTENDEE_FILE):
        return pd.read_csv(ATTENDEE_FILE, dtype={'Badge ID': str})  # Ensure Badge ID is treated as a string
    return pd.DataFrame(columns=['Badge ID', 'Name', 'Email', 'Check-in Time', 'Check-out Time'])

# Function to save data to CSV
def save_data(df):
    df.to_csv(ATTENDEE_FILE, index=False)

# Load attendee data
if 'attendees' not in st.session_state:
    st.session_state['attendees'] = load_data()

if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

# Function to generate QR codes
def generate_qr_code(badge_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(badge_id))  # Ensure Badge ID is stored as a string in the QR code
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# Function to scan QR code using OpenCV
def scan_qr_code(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        return str(data).strip() if data else None  # Ensure output is a string
    except Exception as e:
        return None

# Navigation function
def switch_page(page_name):
    st.session_state['page'] = page_name

# Home Page
if st.session_state['page'] == 'home':
    st.title("📋 Conference Check-In System")
    
    st.subheader("Check-In Options")
    uploaded_file = st.file_uploader("📷 Scan QR Code", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        badge_id = scan_qr_code(uploaded_file)
        if badge_id:
            df = st.session_state['attendees']
            if badge_id in df['Badge ID'].values:
                attendee_index = df[df['Badge ID'] == badge_id].index[0]
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if pd.isnull(df.at[attendee_index, 'Check-in Time']):
                    df.at[attendee_index, 'Check-in Time'] = current_time
                    st.success(f"Checked in {df.at[attendee_index, 'Name']} at {current_time}")
                else:
                    df.at[attendee_index, 'Check-out Time'] = current_time
                    st.success(f"Checked out {df.at[attendee_index, 'Name']} at {current_time}")
                save_data(df)
            else:
                st.warning("Badge ID not found. Use manual check-in if needed.")
        else:
            st.warning("No QR code detected. Please try another image.")
    
    badge_input = st.text_input("🔢 Enter Badge Number")
    if st.button("Check-In/Out by Badge ID"):
        df = st.session_state['attendees']
        if badge_input in df['Badge ID'].values:
            attendee_index = df[df['Badge ID'] == badge_input].index[0]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if pd.isnull(df.at[attendee_index, 'Check-in Time']):
                df.at[attendee_index, 'Check-in Time'] = current_time
                st.success(f"Checked in {df.at[attendee_index, 'Name']} at {current_time}")
            else:
                df.at[attendee_index, 'Check-out Time'] = current_time
                st.success(f"Checked out {df.at[attendee_index, 'Name']} at {current_time}")
            save_data(df)
        else:
            st.warning("Badge ID not found. Use manual check-in if needed.")
    
    st.subheader("Manual Check-In/Out")
    if st.session_state['attendees'].empty:
        st.warning("No attendees found. Please register attendees first.")
    else:
        selected_attendee = st.selectbox("Select Attendee", st.session_state['attendees']['Name'].tolist())
        if st.button("Manually Check-In"):
            attendee_index = st.session_state['attendees'][st.session_state['attendees']['Name'] == selected_attendee].index[0]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state['attendees'].at[attendee_index, 'Check-in Time'] = current_time
            save_data(st.session_state['attendees'])
            st.success(f"Manually checked in {selected_attendee} at {current_time}")
        if st.button("Manually Check-Out"):
            attendee_index = st.session_state['attendees'][st.session_state['attendees']['Name'] == selected_attendee].index[0]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state['attendees'].at[attendee_index, 'Check-out Time'] = current_time
            save_data(st.session_state['attendees'])
            st.success(f"Manually checked out {selected_attendee} at {current_time}")
    
    if st.button("🔐 Admin Area"):
        switch_page('admin')

# Admin Page
elif st.session_state['page'] == 'admin':
    st.title("🔐 Admin - Attendance Dashboard")
    st.dataframe(st.session_state['attendees'])
    csv = st.session_state['attendees'].to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Attendance Data", data=csv, file_name="attendance_data.csv", mime="text/csv")
    if st.button("➕ Register Attendee"):
        switch_page('register_attendee')
    if st.button("⬅ Back to Home"):
        switch_page('home')

# Register Attendee Page
elif st.session_state['page'] == 'register_attendee':
    st.title("➕ Register Attendee")
    name = st.text_input("Attendee Name")
    email = st.text_input("Attendee Email")
    badge_id = st.text_input("Assign Badge ID")
    if st.button("Register"):
        if name and email and badge_id:
            new_entry = pd.DataFrame([[badge_id, name, email, None, None]], columns=st.session_state['attendees'].columns)
            st.session_state['attendees'] = pd.concat([st.session_state['attendees'], new_entry], ignore_index=True)
            save_data(st.session_state['attendees'])
            st.success(f"Registered {name} with Badge ID {badge_id}")
            st.image(generate_qr_code(badge_id), caption=f"QR Code for {name}")
        else:
            st.warning("Please enter name, email, and badge ID.")
    if st.button("⬅ Back to Admin"):
        switch_page('admin')
