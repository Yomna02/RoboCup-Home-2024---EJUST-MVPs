import face_recognition
import cv2
i=0
video_capture = cv2.VideoCapture(0)
picture_of_me = face_recognition.load_image_file("/home/beedo/guest1.png")
my_face_encoding = face_recognition.face_encodings(picture_of_me)[0]
while True:
    ret, frame = video_capture.read()
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)
    for face_location in face_locations:
        top, right, bottom, left = face_location
        print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))
        face=face_encodings[i]
        i+=1
        print("this is person number " +str(i))
        results = face_recognition.compare_faces([my_face_encoding], face)
        print(results)
        if results[0] == True:
            print("It's a picture of me!")
            font = cv2.FONT_HERSHEY_DUPLEX
            name="guest number 1"
            cv2.putText(frame, name, (left-10, bottom + 20), font, 1.0, (255, 255, 255), 1)
            cv2.rectangle(frame, (left, bottom), (right, top), (0, 0, 255), thickness=2)
        else:
            print("It's not a picture of me!")
    i=0
    cv2.imwrite("/home/beedo/recognition.png", frame)
    cv2.imshow("Captured Image", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break