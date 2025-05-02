import streamlit as st
import qrcode
from io import BytesIO
import base64
from database import get_all_attendees
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image

st.set_page_config(layout="wide")
st.title("🪪 Printable Conference Badges (PDF Download)")

BADGES_PER_ROW = 3
BADGE_WIDTH_INCH = 2.3
BADGE_HEIGHT_INCH = 3.4

def generate_qr_code_img(data):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def create_badge_pdf(attendees):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    x_margin = 0.5 * inch
    y_margin = 0.5 * inch
    x_spacing = (width - 2 * x_margin - BADGES_PER_ROW * BADGE_WIDTH_INCH * inch) / (BADGES_PER_ROW - 1)
    y_spacing = 0.3 * inch

    x_positions = [x_margin + i * (BADGE_WIDTH_INCH * inch + x_spacing) for i in range(BADGES_PER_ROW)]
    y_position = height - y_margin - BADGE_HEIGHT_INCH * inch

    badge_idx = 0

    for attendee in attendees:
        col = badge_idx % BADGES_PER_ROW
        if badge_idx > 0 and col == 0:
            y_position -= BADGE_HEIGHT_INCH * inch + y_spacing
            if y_position < 0:
                c.showPage()
                y_position = height - y_margin - BADGE_HEIGHT_INCH * inch

        # Draw border
        c.rect(x_positions[col], y_position, BADGE_WIDTH_INCH * inch, BADGE_HEIGHT_INCH * inch)

        # Draw text
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x_positions[col] + 0.1*inch, y_position + BADGE_HEIGHT_INCH*inch - 0.4*inch, attendee['name'])

        c.setFont("Helvetica", 10)
        c.drawString(x_positions[col] + 0.1*inch, y_position + BADGE_HEIGHT_INCH*inch - 0.7*inch, attendee['email'])
        c.drawString(x_positions[col] + 0.1*inch, y_position + BADGE_HEIGHT_INCH*inch - 0.9*inch, f"Badge #: {attendee['badge_id']}")

        # Generate QR code
        qr_img = generate_qr_code_img(str(attendee["badge_id"]))
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_reader = Image.open(qr_buffer)

        # Draw QR code
        qr_x = x_positions[col] + BADGE_WIDTH_INCH*inch/2 - 0.4*inch
        qr_y = y_position + 0.2*inch
        c.drawInlineImage(qr_reader, qr_x, qr_y, width=0.8*inch, height=0.8*inch)

        badge_idx += 1

    c.save()
    buffer.seek(0)
    return buffer

# Load attendees
attendees = get_all_attendees()

if st.button("Generate PDF of Badges"):
    pdf_buffer = create_badge_pdf(attendees)
    st.download_button(
        label="📄 Download Badges PDF",
        data=pdf_buffer,
        file_name="conference_badges.pdf",
        mime="application/pdf"
    )
