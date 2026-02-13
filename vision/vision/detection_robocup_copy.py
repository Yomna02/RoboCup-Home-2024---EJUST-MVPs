from PIL import Image
import face_recognition
import cv2
import numpy as np
i=0
video_capture = cv2.VideoCapture(0)
ret, frame = video_capture.read()
cv2.imshow("Captured Image", frame)
cv2.imwrite("/home/youmna/captured_image.jpg", frame)
image = face_recognition.load_image_file("/home/youmna/captured_image.jpg")
face_locations = face_recognition.face_locations(image)
print("I found {} face(s) in this photograph.".format(len(face_locations)))
for face_location in face_locations:
    i+=1
    top, right, bottom, left = face_location
    print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))
    face_image = image[top:bottom, left:right]
    pil_image = Image.fromarray(face_image)
    pil_image.show()
    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    cv2.imwrite("/home/youmna/3shra.jpg", opencv_image)
    print("this is person number " +str(i))
