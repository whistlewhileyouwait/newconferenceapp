import qrcode
import os

# Create output folder if it doesn't exist
output_folder = "qr_codes"
os.makedirs(output_folder, exist_ok=True)

# Generate QR codes for badge IDs 01 to 88
for i in range(1, 89):
    badge_id = f"{i:02d}"  # zero-padded: 01, 02, ..., 88
    img = qrcode.make(badge_id)
    img_path = os.path.join(output_folder, f"qr_{badge_id}.png")
    img.save(img_path)

print(f"✅ Done! Saved 88 QR codes in the '{output_folder}' folder.")
