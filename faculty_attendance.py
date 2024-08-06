import cv2
import face_recognition
import pickle
import mysql.connector
import csv
from datetime import datetime,time
import requests  # For making HTTP requests to the Flask app

# Function to get employee details from the database
def get_employee_details(empid):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='collegedb',
            user='root',
            password=''
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT empid, name, branch, email FROM faculty_register WHERE empid = %s"
        cursor.execute(query, (empid,))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as error:
        print(f"Failed to get employee details from MySQL table: {error}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Load face encodings and names
with open(r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_encodings.pkl", 'rb') as f:
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

def is_late():
    current_time = datetime.now().time()
    return current_time > time(9, 20) 

# Capture video from the webcam
video_capture = cv2.VideoCapture(0)

# CSV file setup
csv_file_path = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_attendance.csv"
fieldnames = ['Employee ID', 'Name','Email', 'Branch', 'Date', 'Time']

# Function to request OTP generation
def request_otp_generation(email, empid, name, branch, late):
    url = 'http://localhost:5000/fac_generate_otp'
    data = {'email': email, 'empid': empid, 'name': name, 'branch': branch, 'late': late}
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
    if process_this_frame:
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        current_face_names = []
        current_time = datetime.now()
        new_face_start_times = {}
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                empid = known_face_names[first_match_index]
                if empid not in face_start_times:
                    face_start_times[empid] = current_time
                new_face_start_times[empid] = face_start_times[empid]
                
                if (current_time - face_start_times[empid]).total_seconds() > min_continuous_recognition_duration:
                    if empid not in face_names:
                        employee_details = get_employee_details(empid)
                        if employee_details:
                            late = is_late()  # Determine if the employee is late
                            request_otp_generation(employee_details['email'], empid, employee_details['name'], employee_details['branch'], late)
                            face_names.append(empid)
        face_start_times = new_face_start_times

        # Display the results
        for (top, right, bottom, left), empid in zip(face_locations, face_names):
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, empid, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
