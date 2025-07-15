from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = '141520'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_PASSWORD = 'tc2568'

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

    image_filename = None
    video_filename = None

    if image_file and image_file.filename != "":
        image_filename = secure_filename(image_file.filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    if video_file and video_file.filename != "":
        video_filename = secure_filename(video_file.filename)
        video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))

    submitted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "รอดำเนินการ"

    with open('complaints.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([fullname, phone, address, message, image_filename, video_filename, submitted_date, status])

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

    complaints = []
    if os.path.exists("complaints.csv"):
        with open("complaints.csv", newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                while len(row) < 8:
                    row.append("")
                complaints.append(row)

    return render_template("admin.html", complaints=complaints)

@app.route("/update_status", methods=["POST"])
def update_status():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    try:
        index = int(request.form.get("index"))
        new_status = request.form.get("status")

        with open("complaints.csv", newline='', encoding='utf-8') as file:
            complaints = list(csv.reader(file))

        if 0 <= index < len(complaints):
            while len(complaints[index]) < 8:
                complaints[index].append("")
            complaints[index][7] = new_status

            with open("complaints.csv", mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(complaints)

    except Exception as e:
        print("Error while updating status:", e)

    return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)