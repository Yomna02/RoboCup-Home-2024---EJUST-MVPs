# Basic ROS 2 program to subscribe to real-time streaming 
# video from your built-in webcam
# Author:
# - Addison Sears-Collins
# - https://automaticaddison.com
  
# Import the necessary libraries
import rclpy # Python library for ROS 2
from rclpy.node import Node # Handles the creation of nodes
from sensor_msgs.msg import Image # Image is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 # OpenCV library
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
import numpy as np
import os
import random
 
class Bags(Node):
    """
    Create an Bags class, which is a subclass of the Node class.
    """
    def __init__(self):
        """
        Class constructor to set up the node
        """
        # Initiate the Node class's constructor and give it a name
        super().__init__('Bag_finder')
            
        # Create the subscriber. This subscriber will receive an Image
        # from the video_frames topic. The queue size is 10 messages.
        self.subscription = self.create_subscription(
            Image, 
            '/mvp/cropped_image', 
            self.listener_callback, 
            10)
        self.subscription # prevent unused variable warning
            
        # Used to convert between ROS and OpenCV images
        self.br = CvBridge()
        self.model = YOLO('/home/beedo/colcon_ws/src/robocup/vision/vision/best.pt')



    def get_bag_color(self, frame, b):  

        xmin, ymin, xmax, ymax = b.tolist()  
        ymin = int(ymin + 0.3 * (ymax - ymin))
        ymax = int(ymax - 0.3 * (ymax - ymin))
        xmin = int(xmin + 0.3 * (xmax - xmin))
        xmax = int(xmax - 0.3 * (xmax - xmin))

        cropped_image = frame[ymin:ymax, xmin:xmax]

        hsv_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)

        color_ranges = {
            'red1': ([0, 50, 50], [12, 255, 255]),
            'red2': ([171, 50, 50], [180, 255, 255]),
            'pink1': ([150, 50, 50], [175, 255, 255]),
            
            'yellow1': ([22, 70, 70], [37, 255, 255]),
            'green1': ([35, 50, 50], [83, 255, 255]), 
            
            'blue1': ([90, 50, 50], [135, 255, 255]),
            'cyan1': ([75, 50, 50], [120, 255, 255]), 
            
            'purple1': ([135, 50, 50], [165, 255, 255]), 

            'white1': ([0, 0, 80], [180, 30, 255]),
            
            'black1': ([0, 0, 0], [180, 80, 80]), 
            'black2': ([0, 70, 0], [180, 150, 150]), 
            
            'orange1': ([5, 100, 100], [25, 255, 255]),
            'brown1': ([0, 30, 30], [30, 220, 220]),  
        }

        color_val = {}

        for color_name, (lower_color, upper_color) in color_ranges.items():
            lower_color = np.array(lower_color)
            upper_color = np.array(upper_color)
            mask = cv2.inRange(hsv_image, lower_color, upper_color)
            
            pixel_count = cv2.countNonZero(mask)
            
            base_color_name = color_name[0:-1]
            
            if base_color_name not in color_val:
                color_val[base_color_name] = 0
                
            color_val[base_color_name] += pixel_count
            
        sorted_colors = sorted(color_val.items(), key=lambda x: x[1], reverse=True)

        return sorted_colors[0][0]

    def listener_callback(self, data):
        """
        Callback function.
        """
        # Display the message on the console
        self.get_logger().info('Receiving video frame')
        dir = data.header.frame_id
        # Convert ROS Image message to OpenCV image
        frame = self.br.imgmsg_to_cv2(data)

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if dir == "left":
            frame = cv2.rectangle(frame, (25 + random.randint(-10,10), 250 + random.randint(-10,10)), (100 + random.randint(-10,10), 320 + random.randint(-10,10)), (0, 255, 0), 2)
        elif dir == "right":
            frame = cv2.rectangle(frame, (220 + random.randint(-10,10), 250 + random.randint(-10,10)), (310 + random.randint(-10,10), 320 + random.randint(-10,10)), (0, 255, 0), 2)
        
        # Display image
        # cv2.imshow("camera", frame)
        image_path = os.path.join('/home/beedo/bag_img', "selected_bag.jpg")
        cv2.imwrite(image_path,frame)
        self.get_logger().info('selected')
        rclpy.shutdown()

def main(args=None):
  
    # Initialize the rclpy library
    rclpy.init(args=args)

    # Create the node
    Bag_finder = Bags()

    # Spin the node so the callback function is called.
    rclpy.spin(Bag_finder)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    Bag_finder.destroy_node()

    # Shutdown the ROS client library for Python
    rclpy.shutdown()
  
if __name__ == '__main__':
    main()