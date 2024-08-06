from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
import pandas as pd
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import csv


app = Flask(__name__)

# OTP storage
fac_otp_storage = {}
std_otp_storage = {}

def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(email, otp, late=False):
    sender_email = "krishnaparitala4619@gmail.com"  # Replace with your actual email
    password = "vjbzhowbqarbuvnr"  # Replace with your actual app password
    receiver_email = email

    now = datetime.now()
    date_time_str = now.strftime("%d/%m/%Y at %H:%M:%S")

    subject = "OTP for Attendance Verification"
    late_message = "\nYou are late to the college today." if late else ""
    body = f"Your attendance on {date_time_str}.\nYour OTP for attendance verification is: {otp}{late_message}"
    message = f"Subject: {subject}\n\n{body}"

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    server.quit()


# Database Configuration
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="collegedb"
)
db_cursor = db_connection.cursor()

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/faculty_section')
def faculty_section():
    return render_template('faculty_section.html')

@app.route('/faculty_register', methods=['GET', 'POST'])
def faculty_register():
    if request.method == 'POST':
        name = request.form['name']
        empid = request.form['empid']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']
        db_cursor.execute("INSERT INTO faculty_register (name, empid, email, password, branch) VALUES (%s, %s, %s, %s, %s)",
                          (name, empid, email, password, branch))
        db_connection.commit()
        return redirect(url_for('faculty_section'))
    return render_template('faculty_register.html')

@app.route('/fac_generate_otp', methods=['POST'])
def fac_generate_otp_endpoint():
    content = request.json
    email = content['email']
    empid = content['empid']
    name = content.get('name', '')
    branch = content.get('branch', '')
    late = content.get('late', False)  # Get the late flag
    otp = generate_otp()
    fac_otp_storage[email] = {'otp': str(otp), 'empid': empid, 'timestamp': datetime.now(), 'name': name, 'branch': branch}
    send_otp_email(email, otp, late)  # Pass the late flag to the email function
    return jsonify({'message': 'OTP sent successfully'}), 200


@app.route('/std_generate_otp', methods=['POST'])
def std_generate_otp_endpoint():
    content = request.json
    email = content['email']
    reg_no = content['reg_no']
    name = content.get('name', '')
    branch = content.get('branch', '')
    batch = content.get('batch', '')
    late = content.get('late', False)
    otp = generate_otp()
    std_otp_storage[email] = {
        'otp': str(otp),
        'reg_no': reg_no,
        'timestamp': datetime.now(),
        'name': name,
        'branch': branch,
        'batch': batch
    }
    send_otp_email(email, otp, late)  # Sending the OTP with lateness info
    return jsonify({'message': 'OTP sent successfully'}), 200


@app.route('/fac_verify_otp', methods=['GET', 'POST'])
def fac_verify_otp():
    if request.method == 'POST':
        user_email = request.form['email']
        user_otp = request.form['otp']
        csv_file_path = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_attendance.csv"
        if user_email in fac_otp_storage and fac_otp_storage[user_email]['otp'] == user_otp:
            # Use the additional info stored in otp_storage
            with open(csv_file_path, mode='a', newline='') as file:
                fieldnames = ['Employee ID', 'Name', 'Email', 'Branch', 'Date', 'Time']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writerow({
                    'Employee ID': fac_otp_storage[user_email]['empid'],
                    'Name': fac_otp_storage[user_email]['name'],  # Now includes name
                    'Email': user_email,
                    'Branch': fac_otp_storage[user_email]['branch'],  # And branch
                    'Date': datetime.now().strftime('%Y-%m-%d'),
                    'Time': datetime.now().strftime('%H:%M:%S')
                })
            del fac_otp_storage[user_email]  # Clean up after verification
            return jsonify({'success': True, 'message': 'OTP verified successfully. Attendance logged.'})
        else:
            return jsonify({'success': False, 'message': 'Incorrect OTP or OTP expired.'})
    return render_template('fac_verify_otp.html')


@app.route('/std_verify_otp', methods=['GET', 'POST'])
def std_verify_otp():
    if request.method == 'POST':
        user_email = request.form['email']
        user_otp = request.form['otp']
        csv_file_path = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\student_attendance.csv"
        if user_email in std_otp_storage and std_otp_storage[user_email]['otp'] == user_otp:
            # Use the additional info stored in otp_storage
            with open(csv_file_path, mode='a', newline='') as file:
                fieldnames = ['Register ID', 'Name', 'Email', 'Branch','Batch', 'Date', 'Time']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writerow({
                    'Register ID': std_otp_storage[user_email]['reg_no'],
                    'Name': std_otp_storage[user_email]['name'],  # Now includes name
                    'Email': user_email,
                    'Branch': std_otp_storage[user_email]['branch'],
                    'Batch': std_otp_storage[user_email]['batch'],# And branch
                    'Date': datetime.now().strftime('%Y-%m-%d'),
                    'Time': datetime.now().strftime('%H:%M:%S')
                })
            del std_otp_storage[user_email]  # Clean up after verification
            return jsonify({'success': True, 'message': 'OTP verified successfully. Attendance logged.'})
        else:
            return jsonify({'success': False, 'message': 'Incorrect OTP or OTP expired.'})
    return render_template('std_verify_otp.html')

@app.route('/facereg')
def register_cam():
    return render_template('facereg.html')

@app.route('/save_images', methods=['POST'])
def save_images():
    empid = request.form['empid']
    folder_path = os.path.join(r'C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_images', empid)
    os.makedirs(folder_path, exist_ok=True)

    files = request.files.getlist('images')
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(folder_path, filename))

    return jsonify({'success': True})

@app.route('/encode_faculty_images', methods=['GET', 'POST'])
def encode_faculty_images():
    import encode_faculty_faces
    return render_template("faculty_encode_successful.html")

@app.route('/faculty_login', methods=['GET', 'POST'])
def faculty_login():
    if request.method == 'POST':
        empid = request.form['name']
        password = request.form['password']
        db_cursor.execute("SELECT * FROM faculty_register WHERE empid = %s AND password = %s", (empid, password))
        user = db_cursor.fetchone()
        if user:
            return redirect(url_for('faculty_attendance'))
        else:
            print("Invalid Credentials")
    return render_template('faculty_login.html')


@app.route('/faculty_attendance')
def faculty_attendance():
    return render_template('faculty_attendance.html')


@app.route('/start_faculty_attendance', methods=['GET', 'POST'])
def start_faculty_attendance():
    print('hi')
    import faculty_attendance
    return render_template('faculty_attendance.html')


    

@app.route('/student_section')
def student_section():
    return render_template('student_section.html')



@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        reg_no = request.form['reg_no']
        email = request.form['email']
        branch = request.form['branch']
        batch = request.form['batch']
        db_cursor.execute("INSERT INTO student_register (name, reg_no, email, branch, batch) VALUES (%s, %s,%s, %s, %s)", (name, reg_no, email, branch, batch))
        db_connection.commit()
        return redirect(url_for('student_section'))
    return render_template('student_register.html')


@app.route('/std_facereg')
def std_register_cam():
    return render_template('std_facereg.html')

@app.route('/std_save_image', methods=['POST'])
def std_save_image():
    reg_no = request.form['reg_no']
    folder_path = os.path.join(r'C:\Users\rakes\OneDrive\Desktop\Smart attendance\student_images', reg_no)
    os.makedirs(folder_path, exist_ok=True)

    files = request.files.getlist('images')
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(folder_path, filename))

    return jsonify({'success': True})

@app.route('/encode_student_images', methods=['GET', 'POST'])
def encode_student_images():
    import encode_student_faces
    return render_template("student_encode_successful.html")


@app.route('/faculty_login_student', methods=['GET', 'POST'])
def faculty_login_student():
    if request.method == 'POST':
        empid = request.form['name']
        password = request.form['password']
        db_cursor.execute("SELECT * FROM faculty_register WHERE empid = %s AND password = %s", (empid, password))
        user = db_cursor.fetchone()
        if user:
            return redirect(url_for('student_attendance'))
        else:
            print("Invalid Credentials")
    return render_template('faculty_login_student.html')

@app.route('/student_attendance')
def student_attendance():
    return render_template('student_attendance.html')

@app.route('/start_student_attendance', methods=['GET', 'POST'])
def start_student_attendnace():
    print('hi')
    import student_attendance
    return render_template('student_attendance.html')
    

@app.route('/faculty_recog')
def faculty_recog():
    pass

@app.route('/view_attendance')
def view_attendance():
    return render_template('view_attendance.html')

@app.route('/viewfaculty_attendance')
def viewfaculty_attendance():
    return render_template('view_faculty_attendance.html')

@app.route('/view_faculty_attendance', methods=['POST'])
def view_faculty_attendance():
    if request.method=="POST":
        branch = request.form['branch']
        date = request.form['date']
        df = pd.read_csv('faculty_attendance.csv')
        print(df.columns)
        print(branch)
        print(date)
        df['Date'] = df['Date'].astype(str)
        if 'Branch' in df.columns:
            filtered_df = df[
    (df['Branch'].str.strip().str.lower() == branch.strip().lower()) &
    (df['Date'].str.strip() == date.strip())
    ].to_dict(orient='records')
            return render_template('filtered_faculty_attendance.html', data=filtered_df)

@app.route('/viewstudent_attendance')
def viewstudent_attendance():
    return render_template('view_student_attendance.html')

@app.route('/view_student_attendance', methods=['POST'])
def view_student_attendance():
    branch = request.form['branch']
    batch = request.form['batch']
    date = request.form['date']

    df = pd.read_csv('student_attendance.csv')
    df['Date'] = df['Date'].astype(str)  # Ensure the 'Date' column is string for comparison

    student_filtered_df = df[
        (df['Branch'].str.strip().str.lower() == branch.strip().lower()) &
        (df['Batch'].astype(str).str.strip() == str(batch).strip()) &  # Ensuring Batch is compared as string
        (df['Date'].str.strip() == date.strip())
    ].to_dict(orient='records')

    if not student_filtered_df:
        print("No matching records found.")

    return render_template('filtered_student_attendance.html', data=student_filtered_df)



if __name__ == '__main__':
    app.run(debug=True)
