import face_recognition
import cv2
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist

K_ANGULAR = 0.005

class FaceRecog(Node):
    def __init__(self) -> None:
        super().__init__("Face_Recognition")
        self.sub_recog = self.create_subscription(Bool, "/mvp/face_recog", self.recog_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.done_pub = self.create_publisher(Bool, "/mvp/recog_done", 10)

    def recog_callback(self, msg):
        done = Bool()
        if msg.data == False:
            done.data = False
            for _ in range(20):
                self.done_pub.publish(done)
            self.sub_recog.destroy()
            rclpy.shutdown()
            return
        i=0
        video_capture = cv2.VideoCapture(2)
        picture_of_me = face_recognition.load_image_file("/home/beedo/guest1.png")
        my_face_encoding = face_recognition.face_encodings(picture_of_me)[0]

        for _ in range(10):
            ret, frame = video_capture.read()

        for _ in range(100):
            _ret, frame = video_capture.read()
            frame = frame[:,:]

            # print("Original frame shape:", frame.shape)  # Print the shape before cropping
            face_locations = face_recognition.face_locations(frame)
            print(face_locations)
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            print("sdasdas"+str(face_encodings))
            cmd_vel = Twist()
            for face_location in face_locations:
                top, right, bottom, left = face_location
                print("A face is located at pixel location Top: {}, Left: {}, Bottom: {}, Right: {}".format(top, left, bottom, right))
                face=face_encodings[i]
                i+=1
                frame_cropped = frame[:,:672]
                #cv2.imwrite("/home/beedo/recognition_cropped.png", frame_cropped)
                print("this is person number " +str(i))
                results = face_recognition.compare_faces([my_face_encoding], face)
                print(results)
                if results[0] == True:
                    print("It's a picture of me!")
                    font = cv2.FONT_HERSHEY_DUPLEX
                    name="guest number 1"
                    cv2.putText(frame_cropped, name, (left-10, bottom + 20), font, 1.0, (255, 255, 255), 1)
                    cv2.rectangle(frame_cropped, (left, bottom), (right, top), (0, 0, 255), thickness=2)
                    cv2.imwrite("/home/beedo/recognition.png", frame_cropped)
                    if abs((right+left)/2 - 400) > 15:
                        cmd_vel.angular.z = -((right+left)/2 - 400) * K_ANGULAR
                        cmd_vel.linear.x = 0.0
                        self.cmd_pub.publish(cmd_vel)
                    else:
                        cmd_vel.angular.z = 0.0
                        cmd_vel.linear.x = 0.0
                        self.cmd_pub.publish(cmd_vel)
                        done.data = True
                        for _ in range(20):
                            self.done_pub.publish(done)
                        video_capture.release()
                        self.sub_recog.destroy()
                        rclpy.shutdown()      
                        return                 
                else:
                    print("It's not a picture of me!")
            i = 0
        done.data = False
        for _ in range(20):
            self.done_pub.publish(done)
        video_capture.release()
        self.sub_recog.destroy()
        rclpy.shutdown()
        return

def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = FaceRecog()

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
