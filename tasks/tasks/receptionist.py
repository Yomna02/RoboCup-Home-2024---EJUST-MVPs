import time
import rclpy
from math import pi
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool
from action_robocup.action import TTS, Recog, Chair, Person, Feat
from rclpy.duration import Duration
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from .navigator import BasicNavigator
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from action_msgs.msg import GoalStatus

LISTENING = 0
SPEAKING = 1
node = None

class Luggage(Node):
    def __init__(self):
        super().__init__("receptionist_script")
        
        self.tts_action_client = ActionClient(self, TTS, 'tts')
        self.sr_action_client = ActionClient(self, Recog, 'whisper')
        self.person_action_client = ActionClient(self, Person, 'person')
        self.chair_action_client = ActionClient(self, Chair, 'chair_select')
        self.feat_action_client = ActionClient(self, Feat, 'face_feat')

        self.speech = "none"
        self.chair = None
        self.person = None
        self.sr_feedback = LISTENING
        self.tts_feedback = LISTENING
        self.tts_result = False
        self.init_flag = 0
        self.init_pose_sub = self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self.home_pose, 1)
        self.poses = {'home':[1.05, 0.03, 3.14], 'chairs':[4.3, -1.0, -1.6],'face_guest':[4.3, -1.0, 0.0]}
        self.chair_loc = {'A': [4.3, -1.0, -0.7],
                          'B': [4.3, -1.0, -1.2],
                          'C': [4.3, -1.0, -1.6],
                          'D': [4.3, -1.0, -1.97], 
                          'E': [4.3, -1.0, -2.4]}
        self.nav = BasicNavigator()
        self.log = open("reception.log","w")
        self.detection_done = False
        self.recog_done = False
    
    def detect_face(self):
        msg = Bool()
        msg.data = True
        for _ in range(5):
            self.detect_pub.publish(msg)
    
    def detect_callback(self,msg):
        self.detection_done = msg.data
        self.destroy_subscription(self.detect_sub)
    
    def recog_face(self):
        msg = Bool()
        msg.data = True
        for _ in range(5):
            self.recog_pub.publish(msg)
    
    def recog_callback(self,msg):
        self.recog_done = msg.data
        self.destroy_subscription(self.recog_sub)

    def home_pose(self,msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        quat = (msg.pose.pose.orientation.x,
                msg.pose.pose.orientation.y,
                msg.pose.pose.orientation.z,
                msg.pose.pose.orientation.w)
        yaw = self.quat_to_euler(quat)
        self.poses["home"] = [x, y, yaw]
        self.poses["chairs"] = [x, y, yaw+pi]
        self.init_flag += 1

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
            # if feedback and i % 5 == 0:
            #     print('Estimated time of arrival: ' + '{0:.0f}'.format(
            #         Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9)
            #         + ' seconds.')

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

    def listen(self):
        # print("request")
        goal_msg = Recog.Goal()
        goal_msg.listen = True

        self.sr_action_client.wait_for_server()

        if self.tts_feedback == LISTENING:
            self.sr_send_goal_future = self.sr_action_client.send_goal_async(goal_msg, feedback_callback=self.sr_feedback_callback)

            self.sr_send_goal_future.add_done_callback(self.sr_goal_response_callback)

    def speak(self, speech):
        self.tts_result = False
        goal_msg = TTS.Goal()
        goal_msg.speech = speech
        self.log.write("pioneer: " + speech + "\n")
        
        self.tts_action_client.wait_for_server()
        self.tts_result = False

        self.tts_send_goal_future = self.tts_action_client.send_goal_async(goal_msg, feedback_callback=self.tts_feedback_callback)
    
        self.tts_send_goal_future.add_done_callback(self.tts_goal_response_callback)
    
    def select_chair(self):
        goal_msg = Chair.Goal()
        goal_msg.choose = True
        
        self.chair_action_client.wait_for_server()

        self.chair_send_goal_future = self.chair_action_client.send_goal_async(goal_msg)
    
        self.chair_send_goal_future.add_done_callback(self.chair_goal_response_callback)

    def detect_person(self):
        goal_msg = Person.Goal()
        goal_msg.choose = True
        
        self.person_action_client.wait_for_server()

        self.person_send_goal_future = self.person_action_client.send_goal_async(goal_msg)
    
        self.person_send_goal_future.add_done_callback(self.person_goal_response_callback)

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
        # self.get_logger().info('Listening')
        # self.speak("a")

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
        # self.get_logger().info('Received feedback: {0}'.format(self.sr_feedback))
    
    def chair_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Selecting Chair...')

        self.chair_get_result_future = goal_handle.get_result_async()
        self.chair_get_result_future.add_done_callback(self.chair_get_result_callback)

    def chair_get_result_callback(self, future):
        self.chair = future.result().result.selected
    
    def person_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Seeing a person...')

        self.person_get_result_future = goal_handle.get_result_async()
        self.person_get_result_future.add_done_callback(self.person_get_result_callback)

    def person_get_result_callback(self, future):
        self.person = future.result().result.person
    
    def tts_goal_response_callback(self, future):
        goal_handle = future.result()
        # self.get_logger().info('Speaking')

        self.tts_get_result_future = goal_handle.get_result_async()
        self.tts_get_result_future.add_done_callback(self.tts_get_result_callback)

    def tts_get_result_callback(self, future):
        self.tts_result = future.result().result.finished
        self.tts_result = True

    def get_feat(self):
        self.get_logger().info('get features')
        self.feat = None
        goal_msg = Feat.Goal()
        goal_msg.capture = True
        
        self.feat_action_client.wait_for_server()
        self.get_logger().info('get features')

        self.feat_send_goal_future = self.feat_action_client.send_goal_async(goal_msg)
    
        self.feat_send_goal_future.add_done_callback(self.feat_goal_response_callback)

    def feat_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Get Features')

        self.feat_get_result_future = goal_handle.get_result_async()
        self.feat_get_result_future.add_done_callback(self.feat_get_result_callback)

    def feat_get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(str(result.values))
        self.feat = result.values

    def say_feat(self, label_text, ind):
        if ind == 0:
            return label_text[-1]
        elif ind == 1:
            label_dict = {}
            label_dict['race'] = label_text[0]
            for i in range(1, len(label_text)-2):
                attr, val = label_text[i].split(":")
                label_dict[attr] = float(val.strip())
                
            if label_dict["Young"] < 0.5:
                youth = "looks old"
            else:
                youth = "looks young"
            
            if label_dict["Male"] > 0.7:
                gender = "male"
            else:
                gender = "female"
                    
            hair = label_text[-2]

        return gender, youth, hair

def main(args=None):

    rclpy.init(args=args)

    task = Luggage()
    names_list = ["sophie", "sofy", "sofi", "sophia", "sofia", 
                "julia", "julie", "jolia", "yulia", 
                "emma", "ema", "emmy", 
                "sara", "sarah", "sarra", "sarea", 
                "laura", "lora", "laurah", "lara", "larah" , "laurra",
                "hayley", "halie", "hailey", "hayly", "haylei", "hyley", "haley",
                "susan", "suzan", "sozan", "sosan", "susann", "susahn", "suzin", "susin", "susen", "susn",
                "fleur", "flure", "floor", "phleur", "fler", "flur", "fleeur",
                "gabrielle", "gabriel", "gabrille", "gabiellee", "gabrielhe",
                "robin", "robben", "rubin", "robinn", "roben",
                "john", "jhon", "johnn", "joen", "jaohn", "johne", "jon",
                "liam", "lyam", "liama", "liame", "liaam",
                "lucas", "locas", "leucas", "locus", "lucahs",
                "william", "wiliam", "wileliam", "willeiam", "welliam", "williahm", "wileiam",
                "kevin", "kevinn", "kvin", "keven", "kevn",
                "jesse", "jessy", "jessi", "jesy", "jese", "jisy", "jasse", "jissy", "jisse",
                "noah", "nooh", "naoh", "noa", "nohh", "noahh", "noeh",
                "harrie", "harry", "hary", "hari", "harri", "harie", "haerie", "harrye",
                "peter", "peteh"]
    drinks_list = ["pepsi", "espresso", "milk", "coffee", "orange", "strawberry", "tea", "lemon", "apple"]
    persons = [{"name": "", "drink":""}, {"name": "", "drink":""}]
    person_id = 0
    x = 0
    hair = ""
    shirt = ""
    gender = ""
    youth = ""

    # see a person or he will come to him
    #######
    # code
    #######
    task.detect_person()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.person != None:
            if task.person:
                break
            else:
                task.person = None
                task.detect_person()
    task.person = False

    task.speak("hi, sir!")
    task.speak("please, come in") 
    task.speak("what is your name my friend?")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.listen()
    while rclpy.ok:
        rclpy.spin_once(task)
        end = False
        for name in names_list:
            if name in task.speech:
                persons[person_id]["name"] = name
                end = True
                break
        if end:
            break
        else:
            task.listen()
    
    task.speak(f'good to see you, {persons[person_id]["name"]}')
    task.speak(f"what is your favourite drink," + persons[person_id]["name"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.listen()
    while rclpy.ok:
        rclpy.spin_once(task)
        end = False
        for drink in drinks_list:
            if drink in task.speech:
                persons[person_id]["drink"] = drink
                end = True
                break
        if end:
            break
        else:
            task.listen()

    task.speak(f'you drink {persons[person_id]["drink"]},   perfect!')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak(f'Please, stand still for a moment')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.get_feat()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.feat == []: 
            task.get_feat()
        if task.feat != None:
            break
    
    shirt = task.say_feat(task.feat, 0)
    task.feat = None

    task.speak(f'Nice shirt my friend!')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.speak(f'Now Please, Put your face in front of the camera and stay still')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.speak(f'Do not Move until I till you so, please!')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.speak(f'Get Ready now!')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.get_feat()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.feat == [] or len(task.feat) < 1: 
            task.get_feat()
        if task.feat != None:
            break
    
    gender, youth, hair = task.say_feat(task.feat, 1)
    task.feat = None    

    task.speak("Great, Walk with me!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.navigate_to(task.poses["chairs"])
    
    task.speak('stand to my left!')
    task.speak("hey guys!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.navigate_to(task.poses["face_guest"])

    task.speak(f"This is "+ persons[person_id]["name"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.navigate_to(task.poses["chairs"])

    task.speak(persons[person_id]["name"] + f"favourite drink is " + persons[person_id]["drink"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.speak('let me see an emtpy chair for you')  
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.select_chair()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.chair != None:
            if task.chair == "":
                task.select_chair()
                task.chair = None
            else:
                break
    
    task.navigate_to(task.chair_loc[task.chair])

    task.speak(f"from the left, chair {task.chair} is empty")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak("please, have a seat!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.chair = None

    person_id += 1

    time.sleep(5)
    task.navigate_to(task.poses["home"])

    # see a person or he will come to him
    #######
    # code
    #######
    task.detect_person()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.person != None:
            if task.person:
                break
            else:
                task.person = None
                task.detect_person()

    task.speak("hi, sir!")
    task.speak("please, come in") 
    task.speak("what is your name my friend?")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.listen()
    while rclpy.ok:
        rclpy.spin_once(task)
        end = False
        for name in names_list:
            if name in task.speech:
                persons[person_id]["name"] = name
                end = True
                break
        if end:
            break
        else:
            task.listen()
    
    task.speak(f'good to see you, {persons[person_id]["name"]}')
    task.speak(f"what is your favourite drink," + persons[person_id]["name"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.listen()
    while rclpy.ok:
        rclpy.spin_once(task)
        end = False
        for drink in drinks_list:
            if drink in task.speech:
                persons[person_id]["drink"] = drink
                end = True
                break
        if end:
            break
        else:
            task.listen()

    task.speak(f'you drink {persons[person_id]["drink"]},   perfect!')
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak("Walk with me!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.navigate_to(task.poses["chairs"])
    
    task.speak('stand to my left!')
    task.speak("hey guys!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.navigate_to(task.poses["face_guest"])

    task.speak(f"This is "+ persons[person_id]["name"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.navigate_to(task.poses["chairs"])

    task.speak(persons[person_id]["name"] + f"favourite drink is " + persons[person_id]["drink"])
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.navigate_to(task.poses["chairs"])
    
    task.speak(f"Please, meet {persons[0]['name']}")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak(f"the one with the {shirt} shirt")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak(f"A {gender} and {youth} person with a nice {hair} hair")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break    

    task.speak('let me see an emtpy chair for you')  
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break

    task.select_chair()
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.chair != None:
            if task.chair == "":
                task.select_chair()
                task.chair = None
            else:
                break
    
    task.navigate_to(task.chair_loc[task.chair])

    task.speak(f"from the left, chair {task.chair} is empty")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.speak("please, have a seat!")
    task.tts_result = False
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            task.tts_result = False
            break
    
    task.log.close()

if __name__ == '__main__':
    main()