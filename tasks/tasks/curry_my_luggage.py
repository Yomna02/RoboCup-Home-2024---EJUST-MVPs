import time
import rclpy
import threading
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool
from action_robocup.action import TTS, Recog, Bag, Queue
from geometry_msgs.msg import Twist
from .navigator import BasicNavigator
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from action_msgs.msg import GoalStatus
from rclpy.duration import Duration
from tf_transformations import euler_from_quaternion, quaternion_from_euler

LISTENING = 0
SPEAKING = 1
node = None

class Luggage(Node):
    def __init__(self):
        super().__init__("carry_luggage_script")

        self.log = open('/home/beedo/carry_luggage_script.log', 'w')
        
        self.start = False

        self.trigger_sub = self.create_subscription(Bool, "/mvp/trigger", self.trigger_callback, 10)
        self.tts_action_client = ActionClient(self, TTS, 'tts')
        self.sr_action_client = ActionClient(self, Recog, 'whisper')
        self.bag_action_client = ActionClient(self, Bag, 'bag_dir')
        self.qu_action_client = ActionClient(self, Queue, 'queue')
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.follow_publish = self.create_publisher(Bool, "/mvp/follow", 10)
        self.nav = BasicNavigator()
        self.init_flag = 0
        self.init_pose_sub = self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self.home_pose, 1)

        self.poses = {'home':[4.0, -1.0, 3.14], 'left':[-1.3689, 1.37035, 0.011], 'right':[3.3174, 1.42052, -3.133]}
        self.speech = "none"
        self.sr_feedback = LISTENING
        self.tts_feedback = LISTENING
        self.tts_result = False
        self.bag_dir = ""
        self.qu_dir = None

    def home_pose(self,msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        quat = (msg.pose.pose.orientation.x,
                msg.pose.pose.orientation.y,
                msg.pose.pose.orientation.z,
                msg.pose.pose.orientation.w)
        yaw = self.quat_to_euler(quat)
        self.poses["home"] = [x, y, yaw]
        self.init_flag += 1

    def trigger_callback(self, msg):
        self.start = msg.data
    
    def euler_to_quat(self,yaw):
        q = quaternion_from_euler(0,0,yaw)
        return q
    
    def quat_to_euler(self,quat):
        _r,_p_,yaw = euler_from_quaternion((quat[0], quat[1], quat[2], quat[3]))
        return yaw
    
    def navigate_to(self, pose):
        self.nav.waitUntilNav2Active()

        navigator = self.nav

        # Go to our demos first goal pose
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = navigator.get_clock().now().to_msg()
        goal_pose.pose.position.x = pose[0]
        goal_pose.pose.position.y = pose[1]
        quat = self.euler_to_quat(pose[2])
        goal_pose.pose.orientation.x = quat[0]
        goal_pose.pose.orientation.y = quat[1]
        goal_pose.pose.orientation.z = quat[2]
        goal_pose.pose.orientation.w = quat[3]

        navigator.goToPose(goal_pose)

        i = 0
        while not navigator.isNavComplete():
            i = i + 1
            feedback = navigator.getFeedback()
            if feedback and i % 5 == 0:
                print('Estimated time of arrival: ' + '{0:.0f}'.format(
                    Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9)
                    + ' seconds.')

                # Some navigation timeout to demo cancellation
                if Duration.from_msg(feedback.navigation_time) > Duration(seconds=600.0):
                    navigator.cancelNav()
        self.get_logger().info(str(goal_pose))

        # Do something depending on the return code
        result = navigator.getResult()
        if result == GoalStatus.STATUS_SUCCEEDED:
            print('Goal succeeded!')
        elif result == GoalStatus.STATUS_CANCELED:
            print('Goal was canceled!')
        elif result == GoalStatus.STATUS_ABORTED:
            print('Goal failed!')
        else:
            print('Goal has an invalid return status!')

    def choose_bag(self):
        # print("request")
        goal_msg = Bag.Goal()
        goal_msg.choose = True

        self.bag_action_client.wait_for_server()

        self.bag_send_goal_future = self.bag_action_client.send_goal_async(goal_msg)

        self.bag_send_goal_future.add_done_callback(self.bag_goal_response_callback)

    def choose_queue(self):
        # print("request")
        goal_msg = Queue.Goal()
        goal_msg.choose = True

        self.qu_action_client.wait_for_server()

        self.qu_send_goal_future = self.qu_action_client.send_goal_async(goal_msg)

        self.qu_send_goal_future.add_done_callback(self.qu_goal_response_callback)

    def listen(self):
        # print("request")
        # time.sleep(4)
        # self.speak("a")
        goal_msg = Recog.Goal()
        goal_msg.listen = True
        self.sr_action_client.wait_for_server()

        if self.tts_feedback == LISTENING:
            self.sr_send_goal_future = self.sr_action_client.send_goal_async(goal_msg, feedback_callback=self.sr_feedback_callback)

            self.sr_send_goal_future.add_done_callback(self.sr_goal_response_callback)

    def not_listen(self):
        # print(self.tts_feedback)
        goal_msg = Recog.Goal()
        goal_msg.listen = False

        self.sr_action_client.wait_for_server()

        self.sr_send_goal_future = self.sr_action_client.send_goal_async(goal_msg, feedback_callback=self.sr_feedback_callback)

        self.sr_send_goal_future.add_done_callback(self.sr_goal_response_callback)

    def speak(self, speech):
        self.log.write("pioneer: " + speech + "\n")
        self.tts_result = False
        goal_msg = TTS.Goal()
        goal_msg.speech = speech
        
        self.tts_action_client.wait_for_server()

        self.tts_send_goal_future = self.tts_action_client.send_goal_async(goal_msg, feedback_callback=self.tts_feedback_callback)
    
        self.tts_send_goal_future.add_done_callback(self.tts_goal_response_callback)

    def tts_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Speaking')

        self.tts_get_result_future = goal_handle.get_result_async()
        self.tts_get_result_future.add_done_callback(self.tts_get_result_callback)

    def tts_get_result_callback(self, future):
        self.tts_result = future.result().result.finished
        self.tts_result = True
        # node.get_logger().info(f'Finished {result.finished}')
        # rclpy.shutdown()

    def tts_feedback_callback(self, feedback_msg):
        self.tts_feedback = feedback_msg.feedback.state
        # self.get_logger().info('Received feedback: {0}'.format(self.tts_feedback))

    def sr_goal_response_callback(self, future):
        self.goal_handle = future.result()
        self.get_logger().info('Listening')

        self.sr_get_result_future = self.goal_handle.get_result_async()
        self.sr_get_result_future.add_done_callback(self.sr_get_result_callback)

    def sr_get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'I heard {result.speech}')
        self.speech = result.speech
        self.log.write("operator: " + self.speech + "\n")
        # rclpy.shutdown()

    def sr_feedback_callback(self, feedback_msg):
        self.tts_feedback = feedback_msg.feedback.state
        self.get_logger().info('Received feedback: {0}'.format(self.sr_feedback))
    
    def bag_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Point to the bag!')

        self.bag_get_result_future = goal_handle.get_result_async()
        self.bag_get_result_future.add_done_callback(self.bag_get_result_callback)

    def bag_get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'you choose the {result.dir} bag')
        self.bag_dir = result.dir
        # rclpy.shutdown()
    
    def qu_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Seeing the Queue!')

        self.qu_get_result_future = goal_handle.get_result_async()
        self.qu_get_result_future.add_done_callback(self.qu_get_result_callback)

    def qu_get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'you choose the {result.dir} queue')
        self.qu_dir = result.dir
        # rclpy.shutdown()
    
    def follow(self, state):
        following = Bool()
        following.data = state
        self.follow_publish.publish(following)

    def move_to_bag(self, dir):
        cmd = Twist()
        if dir == "right":
            wz = 0.1
        else:
            wz = -0.1
        cmd.linear.x = 0.0
        cmd.angular.z = wz
        t = time.perf_counter()
        while time.perf_counter() - t < 3.0:
            self.cmd_pub.publish(cmd)
        t = time.perf_counter()
        cmd.linear.x = 0.08
        cmd.angular.z = 0.0
        while time.perf_counter() - t < 7.0:
            self.cmd_pub.publish(cmd)
        
def main(args=None):

    rclpy.init(args=args)

    task = Luggage()
    
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.start:
            break
        
    task.speak("I will carry your bag, but which one")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break
    
    # time.sleep(5)

    task.choose_bag()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.bag_dir == "right" or task.bag_dir == "left":
            break
        elif task.bag_dir == "center":
            task.choose_bag()

    task.speak(f"Alright, the bag on your {task.bag_dir}")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break
    
    # task.move_to_bag(task.bag_dir)

    #-------------------------------------------------------------#
    # follow sequence
    
    while rclpy.ok:
        task.listen()
        rclpy.spin_once(task)
        if "follow" in task.speech:
            break
        
    task.speak("Okay I will follow you")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break

    while rclpy.ok:
        task.follow(True)
        task.listen()
        rclpy.spin_once(task)
        if "stop" in task.speech or "pause" in task.speech or "go home" in task.speech:
            for _ in range(50):
                task.follow(False)
                task.follow(False)
            break
    
    task.speak("Fine, you seem bored of me, take your bag")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break
    
    #---------------------------------------------------------#
    #back home
        
    task.speak("Let's go back home")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break
    
    task.navigate_to(task.poses["home"])

    task.log.close()
    

    



if __name__ == '__main__':
    main()