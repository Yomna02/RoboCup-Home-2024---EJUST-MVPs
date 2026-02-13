from typing import List
from PIL import Image
import face_recognition
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

class Face_detect(Node):
    def __init__(self) -> None:
        super().__init__("Face_detect")
        self.detect_sub = self.create_subscription(Bool, "/mvp/detect_face", self.detection_callback, 10)
        self.pub_finish = self.create_publisher(Bool, "/mvp/detected", 10)

    def detection_callback(self, msg):
        select = msg.data
        i=0
        video_capture = cv2.VideoCapture(2)
        for _ in range(15):
            ret, frame = video_capture.read()
            pass
        ret, frame = video_capture.read()
        frame = frame[:,:672]
        # cv2.imshow("Captured Image", frame)
        cv2.imwrite("/home/beedo/captured_image.png", frame)
        image = face_recognition.load_image_file("/home/beedo/captured_image.png")
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
            cv2.imwrite("/home/beedo/guest1.png", opencv_image)
            print("this is person number " +str(i))
        if len(face_locations) == 0:        
            finish = Bool()
            finish.data = False
        else:
            finish = Bool()
            finish.data = True
        for _ in range(20):
            self.pub_finish.publish(finish)
        video_capture.release()
        self.detect_sub.destroy()
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = Face_detect()

    try:
        rclpy.spin(minimal_subscriber)

    except KeyboardInterrupt:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        minimal_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

