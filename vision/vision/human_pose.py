import cv2
import rclpy
import numpy as np
import mediapipe as mp
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge 
from std_msgs.msg import String
from rclpy.action import ActionServer
from action_robocup.action import Bag


class PoseEstimator(Node):
    def __init__(self) -> None:
        super().__init__('bag_choose')

        self._action_server = ActionServer(
            self,
            Bag,
            'bag_dir',
            self.execute_callback)
        # Publisher to pubsish person depth
        self.publisher_cropped = self.create_publisher(
                                                Image,
                                                '/mvp/cropped_image', 
                                                10)

        self._cvbridge = CvBridge()
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    
    def execute_callback(self, goal_handle):
        self.get_logger().info('Choose which bag...')
        try:
            directions = {"left":0, "right":0, "center":0}
            
            self.cap = cv2.VideoCapture(2)
            
            for i in range(20):
                dir = self.detect_pose()
                directions[dir] += 1

            print(directions)
        except:
            directions = {"left":0, "right":5, "center":0}

        goal_handle.succeed()

        result = Bag.Result()

        result.dir = max(directions, key=directions.get)

        ret, frame = self.cap.read()

        frame = frame[:,672:]

        if result.dir == "right":
            cropped_img = self._cvbridge.cv2_to_imgmsg(frame[:, 0:672//2])
            self.publisher_cropped.publish(cropped_img)
            cropped_img.header.frame_id = "right"
        elif result.dir == "left":
            cropped_img = self._cvbridge.cv2_to_imgmsg(frame[:, 672//2:])
            cropped_img.header.frame_id = "left"
            
            self.publisher_cropped.publish(cropped_img)
        
        cv2.destroyAllWindows()
        self.cap.release()

        
        return result


    def detect_pose(self):

        ret, frame = self.cap.read()

        frame = frame[:,672:]

        mp_drawing = self.mp_drawing
        mp_pose = self.mp_pose
        pose = self.pose

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # process the frame for pose detection
        pose_results = pose.process(frame_rgb)
        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        try:
            left_wrist_x = pose_results.pose_landmarks.landmark[15].x
            left_wrist_y = pose_results.pose_landmarks.landmark[15].y
            right_wrist_x = pose_results.pose_landmarks.landmark[16].x
            right_wrist_y = pose_results.pose_landmarks.landmark[16].y
            left_elbow_x = pose_results.pose_landmarks.landmark[13].x
            left_elbow_y = pose_results.pose_landmarks.landmark[13].y
            right_elbow_x = pose_results.pose_landmarks.landmark[14].x
            right_elbow_y = pose_results.pose_landmarks.landmark[14].y

            left_angle = np.arctan2(left_elbow_x-left_wrist_x, left_elbow_y-left_wrist_y)
            right_angle = np.arctan2(right_elbow_x-right_wrist_x,right_elbow_y-right_wrist_y)

            self.get_logger().info("left angle: " + str(left_angle) + "... right angle: " + str(right_angle))
            
            # dir = String()
            # dir.data = self.choose_side(right_angle,left_angle)
            # self.publisher_direction.publish(dir)

            dir = self.choose_side(right_angle,left_angle)

        except:
            dir = "center"
        # draw skeleton on the frame

        cv2.imshow("Image", frame)
        cv2.waitKey(1)

        return dir

    def choose_side(self, right, left):
        if (abs(right - 3.14) < 0.2 or abs(right + 3.14) < 0.2) and (abs(left - 3.14) < 0.2 or abs(left + 3.14) < 0.2):
            self.get_logger().info("no direction")
            return "center"

        if abs(right - 2.7) < 0.3 or abs(left - 2.4) < 0.3:
            self.get_logger().info("pointing right")
            return "right"

        if abs(right + 2.4) < 0.3 or abs(left + 2.7) < 0.3:
            self.get_logger().info("pointing left")
            return "left"
        
        self.get_logger().info("no direction")
        return "center"

def main(args=None):

    rclpy.init(args=args)
    aruco_detector = PoseEstimator()
    rclpy.spin(aruco_detector)
    # Destroy the node explicitly
    cv2.destroyAllWindows()  
    aruco_detector.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
 