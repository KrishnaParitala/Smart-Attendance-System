import face_recognition
import os
import pickle

def pre_process_and_save_encodings(faculty_directory, output_file):
    known_face_encodings = []
    known_face_names = []
    for faculty_name in os.listdir(faculty_directory):
        subfolder_path = os.path.join(faculty_directory, faculty_name)
        if os.path.isdir(subfolder_path):
            for image_name in os.listdir(subfolder_path):
                if image_name.endswith('.jpg') and not image_name.endswith('_0.jpg') and not image_name.endswith('_1.jpg'):
                    image_path = os.path.join(subfolder_path, image_name)
                    image = face_recognition.load_image_file(image_path)
                    face_encoding = face_recognition.face_encodings(image)
                    if face_encoding:
                        known_face_encodings.append(face_encoding[0])
                        known_face_names.append(faculty_name)
    
    # Save encodings and names to a file
    with open(output_file, 'wb') as f:
        pickle.dump({'encodings': known_face_encodings, 'names': known_face_names}, f)

faculty_directory = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_images"
output_file = r"C:\Users\rakes\OneDrive\Desktop\Smart attendance\faculty_encodings.pkl"
pre_process_and_save_encodings(faculty_directory, output_file)
