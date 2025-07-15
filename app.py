from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
app.secret_key = '141520'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_PASSWORD = 'tc2568'

# ✅ Google API setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_FILE = 'credentials.json'

# ✅ เปลี่ยนเป็นเฉพาะ Spreadsheet ID เท่านั้น
SPREADSHEET_ID = '16bncW4hIi6bKp4T0SPOtGTkcELCYM7CF6CJ5w-kjOCc'
FOLDER_ID = '16B_RDC-axKkGBBBtByl7tl81vV7J0iov'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
drive_service = build('drive', 'v3', credentials=creds)

@app.route('/healthz')
def healthz():
    return "ok", 200

@app.route("/")
def home():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    fullname = request.form["fullname"]
    phone = request.form["phone"]
    address = request.form["address"]
    message = request.form["message"]

    image_file = request.files.get("image")
    video_file = request.files.get("video")

    image_link = ""
    video_link = ""

    def upload_to_drive(file, filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        media = MediaFileUpload(filepath, resumable=True)
        file_metadata = {'name': filename, 'parents': [FOLDER_ID]}
        uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = uploaded.get('id')
        drive_service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
        return f"https://drive.google.com/file/d/{file_id}/view"

    if image_file and image_file.filename != "":
        image_filename = secure_filename(image_file.filename)
        image_link = upload_to_drive(image_file, image_filename)

    if video_file and video_file.filename != "":
        video_filename = secure_filename(video_file.filename)
        video_link = upload_to_drive(video_file, video_filename)

    submitted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "รอดำเนินการ"

    sheet.append_row([fullname, phone, address, message, image_link, video_link, submitted_date, status])

    return "ส่งคำร้องเรียบร้อยแล้ว! ขอบคุณครับ"

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for("admin"))
        else:
            error = "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง"
    return render_template("admin_login.html", error=error)

@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    complaints = sheet.get_all_values()[1:]  # ข้ามแถวหัวตาราง
    return render_template("admin.html", complaints=complaints)

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
