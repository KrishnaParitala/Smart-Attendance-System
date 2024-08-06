import cv2
import face_recognition
import pickle
import mysql.connector
import csv
from datetime import datetime,time
import requests  # For making HTTP requests to the Flask app

def is_late():
    current_time = datetime.now().time()
    return current_time > time(9, 20)  # Time threshold for being late

# Function to get student details from the database
def get_student_details(reg_no):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='collegedb',
            user='root',
            password=''
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT reg_no, name, branch, batch, email FROM student_register WHERE reg_no = %s"
        cursor.execute(query, (reg_no,))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as error:
        print(f"Failed to get student details from MySQL table: {error}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Load face encodings and names
with open(r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\student_encodings.pkl", 'rb') as f:
    data = pickle.load(f)
known_face_encodings = data['encodings']
known_face_names = data['names']

# Initialize variables
face_locations = []
face_encodings = []
face_names = []
face_start_times = {}  # Track when each face is first seen
min_continuous_recognition_duration = 5  # seconds
process_this_frame = True

# Capture video from the webcam
video_capture = cv2.VideoCapture(0)

# CSV file setup
csv_file_path = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\student_attendance.csv"
fieldnames = ['student ID', 'Name','Email', 'Branch', 'Batch' 'Date', 'Time']

# Function to request OTP generation
def request_otp_generation(email, reg_no, name, branch, batch, late):
    url = 'http://localhost:5000/std_generate_otp'
    data = {
        'email': email,
        'reg_no': reg_no,
        'name': name,
        'branch': branch,
        'batch': batch,
        'late': late
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("OTP generation and email dispatch initiated.")
    else:
        print(f"Failed to initiate OTP generation and dispatch. Status code: {response.status_code}")


# Create or open the CSV file and write the headers if it's empty
with open(csv_file_path, mode='a', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    if file.tell() == 0:
        writer.writeheader()

while True:
    ret, frame = video_capture.read()
    if not ret:
        break  # If there's an error in capturing the frame, exit the loop

    # Reduce frequency of frame processing if desired with process_this_frame
    if process_this_frame:
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        current_face_names = []  # Reset the current face names for this frame
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if True in matches:
                first_match_index = matches.index(True)
                reg_no = known_face_names[first_match_index]
                
                if reg_no not in face_start_times:
                    face_start_times[reg_no] = datetime.now()
                else:
                    if (datetime.now() - face_start_times[reg_no]).total_seconds() > min_continuous_recognition_duration:
                        if reg_no not in face_names:
                            student_details = get_student_details(reg_no)
                            if student_details:
                                late = is_late()  # Determine if the student is late
                                request_otp_generation(student_details['email'], reg_no, student_details['name'], student_details['branch'], student_details['batch'], late)
                                face_names.append(reg_no)

    # Reset face_names to only include faces from the current frame
    face_names = current_face_names

    # Display the results
    for (top, right, bottom, left), reg_no in zip(face_locations, face_names):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, reg_no, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()