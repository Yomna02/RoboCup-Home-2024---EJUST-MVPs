import cv2
import rclpy
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge 
from rclpy.logging import LoggingSeverity
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from ultralytics import YOLO

K_LINEAR = 0.0007
K_ANGULAR = 0.002
DESIRED = 300

class Follower(Node):
    def __init__(self) -> None:
        super().__init__('follower')
        self.following = False
        

        self._subscriber_follow_flag = self.create_subscription(
                                                Bool,
                                                '/mvp/follow',
                                                self.flag_callback,
                                                10)

        # Publisher to pubsish person depth
        self.publisher_cmd = self.create_publisher(
                                                Twist,
                                                '/cmd_vel', 
                                                10)

        self.timer = self.create_timer(0.1, self.detect_pose)

        self.num_to_label = {0.0 : "person"}

        # Initialize YOLO model
        self.model = YOLO('yolov5s.pt')
        self.flag = False

    def flag_callback(self,msg):
        '''
        Receive Bool message
        
        '''
        self.following = msg.data
    
    def detect(self, img):
        """
        Detect empty chairs in an image using YOLO model.

        Args:
            img (numpy.ndarray): Input image.

        Returns:
            list: List of empty chair bounding boxes.
        """
        # Perform YOLO object detection
        results = self.model.predict(source = img, conf = 0.5)
        boxes = results[0].boxes.data.tolist()

        person = None
        w_max = 0
        for box in boxes:
            # Check if the object is a person or a chair
            if self.num_to_label.get(box[5], "unrelated") == "person":
                person_box = box[0:4]
                x = int(person_box[0])
                w = int(person_box[2] - person_box[0])
                y = int(person_box[1])
                h = int(person_box[3] - person_box[1])
                w_max = max(w,w_max)
                if w_max == w:
                    person = box[0:4]
        return person
    
    def draw(self, img, person):
        """
        Draw rectangles and labels for empty chairs on an image.

        Args:
            img (numpy.ndarray): Input image.
            empty_chairs (list): List of empty chair bounding boxes.

        Returns:
            numpy.ndarray: Image with rectangles and labels drawn.
        """
        label_position = (int(person[0]), int(person[1]) - 10)
        label_size, baseline = cv2.getTextSize("Empty Chair", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 3)
        cv2.rectangle(img, (int(person[0]), label_position[1] + baseline - label_size[1] - 10),
                    (label_position[0] + label_size[0], int(person[1])), (0, 255, 0), -1)
        cv2.rectangle(img, (int(person[0]), int(person[1])), (int(person[2]), int(person[3])), (0, 255, 0), 2)
        cv2.putText(img, "person", label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            
        return img


    def detect_pose(self):
        '''
        Returns
        --------
        Windows
        '''
        if self.following:
            if not self.flag:
                self.cap = cv2.VideoCapture(2)
                self.flag = True

            ret, frame = self.cap.read()

            if not ret:
                return
            
            frame = frame[:,672:]
            
            # process the frame for pose detection
            try:
                person_box = self.detect(frame)
                x = int(person_box[0])
                w = int(person_box[2] - person_box[0])
                y = int(person_box[1])
                h = int(person_box[3] - person_box[1])
                frame = self.draw(frame, person_box)
                # depth_frame = self.draw(depth_frame, person_box)
                self.follow(x+20,y+20,w-20,h-20)
                cv2.imshow("color Image", frame)
                # cv2.imshow("depth Image", depth_frame)
                cv2.waitKey(1)
            except:
                cmd = Twist()

                cmd.linear.x = 0.0
                cmd.angular.z = 0.0

                self.publisher_cmd.publish(cmd)

                cv2.imshow("color Image", frame)
                cv2.waitKey(1)
            

    def follow(self, x, y, w, h):
        '''
        Returns
        --------
        Windows
        '''
        
        cmd = Twist()

        cmd.linear.x = (DESIRED - w) * K_LINEAR 
        cmd.angular.z = - K_ANGULAR * ((x + x + w) / 2 - 336)

        if w > 600:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        self.publisher_cmd.publish(cmd)

    def drawww(self,img,vertices):
        vertices = vertices.reshape((-1, 1, 2))
        cv2.polylines(img, [vertices], isClosed=True, color=0, thickness=2)


def main(args=None):

    rclpy.init(args=args)
    follow = Follower()
    rclpy.spin(follow)
    # Destroy the node explicitly  
    follow.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
 