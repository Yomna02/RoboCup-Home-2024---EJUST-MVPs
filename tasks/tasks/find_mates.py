import time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool
from action_robocup.action import TTS, Recog, Bag, Feat
from rclpy.duration import Duration
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from .navigator import BasicNavigator
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from action_msgs.msg import GoalStatus
from action_robocup.action import Person

LISTENING = 0
SPEAKING = 1
node = None

class Luggage(Node):
    def __init__(self):
        super().__init__("find_mates_script")
        self.log = open('/home/beedo/find_mates_script.log', 'w')
        
        self.start = False

        self.trigger_sub = self.create_subscription(Bool, "/mvp/trigger", self.trigger_callback, 10)

        self.tts_action_client = ActionClient(self, TTS, 'tts')
        self.sr_action_client = ActionClient(self, Recog, 'whisper')
        self.feat_action_client = ActionClient(self, Feat, 'face_feat')
        self.person_action_client = ActionClient(self, Person, 'person')

        self.speech = "none"
        self.sr_feedback = LISTENING
        self.tts_feedback = LISTENING
        self.tts_result = False
        self.init_flag = 0
        self.init_pose_sub = self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self.home_pose, 1)
        self.poses = {'home':[-0.12, -0.35, -1.6], 
                      'A':[2.82, -1.85, -2.0], 
                      'B':[3.55, 0.13, 2.0], 
                      'C':[4.4, -2.0, -1.6], 
                      'D':[4.2, 0.12, 1.56], 
                      'E':[6.2, -1.87, -1.1], 
                      'F':[4.75, 0.11, 1.07]}
        self.uni_feat = {'A':'near the small sofa', 'B':'near the dining table', 'C':"on the large sofa", 'D':"behind the dining table", 'E':"behind the far small sofa", 'F':"near the dining table"}
        self.nav = BasicNavigator()
        self.feat = None

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

    def euler_to_quat(self,yaw):
        q = quaternion_from_euler(0,0,yaw)
        return q
    
    def quat_to_euler(self,quat):
        _r,_p_,yaw = euler_from_quaternion((quat[0], quat[1], quat[2], quat[3]))
        return yaw
    
    def trigger_callback(self, msg):
        self.start = msg.data

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

                # # Some navigation timeout to demo cancellation
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
        self.log.write("pioneer: " + speech + "\n")
        self.tts_result = False
        goal_msg = TTS.Goal()
        goal_msg.speech = speech
        
        self.tts_action_client.wait_for_server()
        self.tts_result = False
        self.tts_send_goal_future = self.tts_action_client.send_goal_async(goal_msg, feedback_callback=self.tts_feedback_callback)
    
        self.tts_send_goal_future.add_done_callback(self.tts_goal_response_callback)

    def tts_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Speaking')

        self.tts_get_result_future = goal_handle.get_result_async()
        self.tts_get_result_future.add_done_callback(self.tts_get_result_callback)

    def tts_get_result_callback(self, future):
        self.tts_result = future.result().result.finished
        # node.get_logger().info(f'Finished {result.finished}')
        # rclpy.shutdown()

    def tts_feedback_callback(self, feedback_msg):
        self.tts_feedback = feedback_msg.feedback.state
        self.get_logger().info('Received feedback: {0}'.format(self.tts_feedback))

    def sr_goal_response_callback(self, future):
        self.goal_handle = future.result()
        self.get_logger().info('Listening')
        self.speak("a")

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
        # rclpy.shutdown()

    def detect_person(self):
        goal_msg = Person.Goal()
        goal_msg.choose = True
        
        self.person_action_client.wait_for_server()

        self.person_send_goal_future = self.person_action_client.send_goal_async(goal_msg)
    
        self.person_send_goal_future.add_done_callback(self.person_goal_response_callback)

    def person_goal_response_callback(self, future):
        goal_handle = future.result()
        self.get_logger().info('Seeing a person...')

        self.person_get_result_future = goal_handle.get_result_async()
        self.person_get_result_future.add_done_callback(self.person_get_result_callback)

    def person_get_result_callback(self, future):
        self.person = future.result().result.person

    def say_feat(self, label_text, person_id):
        label_dict = {}
        label_dict['race'] = label_text[0]
        for i in range(1, len(label_text)):
            attr, val = label_text[i].split(":")
            label_dict[attr] = float(val.strip())
        
        if label_dict["No_Beard"] < 0.5:
            beard = "have beard"
        else:
            beard = "have no beard"
            
        if label_dict["Young"] < 0.5:
            youth = "looks old"
        else:
            youth = "looks young"
        
        if label_dict["Male"] > 0.8:
            gender = "male"
        else:
            gender = "female"
        
        if label_dict["Eyeglasses"] > 0.6:
            glass = "wear glasses"
        else:
            glass = "not wearing glasses"

        hair = {"Black_Hair":label_dict["Black_Hair"],
                "Gray_Hair":label_dict["Gray_Hair"],
                "Blond_Hair":label_dict["Blond_Hair"],
                "Brown_Hair":label_dict["Brown_Hair"]}
        
        race = label_dict['race']
        
        if label_dict["Oval_Face"] > 0.4:
            face = "oval face"
        else:
            face = "round face"

        if label_dict["Big_Nose"] > 0.6:
            nose = "big nose"
        else:
            nose = "small nose"       

        if label_dict["Narrow_Eyes"] > 0.6:
            eyes = "narrow eyes"
        else:
            eyes = "wide eyes"               

        if person_id == 0:
            # self.get_logger().info(youth + ", " + beard + ", " + face)
            return str(youth + ", " + beard + ", " + face) 
        elif person_id == 1:
            return str(gender + ", " + glass + ", " + nose)
        elif person_id == 2:
            return str(race+ ", " + max(hair, key=hair.get) + ", " + eyes)
            
def main(args=None):

    rclpy.init(args=args)

    task = Luggage()

    loc = ['A', 'B', 'C', 'D', 'E', 'F']
    
    names_list = ["sophie", "sofy", "sofi", "sophia", "sofia", 
                  "julia", "julie", "jolia", "yulia", 
                  "emma", "ema", "emmy", 
                  "sara", "sarah", "sarra", "sarea", 
                  "laura", "lora", "laurah", "lara", "larah" , "laurra"
                  "hayley", "halie", "hailey", "hayly", "haylei", "hyley", "haley"
                  "susan", "suzan", "sozan", "sosan", "susann", "susahn", "suzin", "susin", "susen", "susn",
                  "fleur", "flure", "floor", "phleur", "fler", "flur", "fleeur"
                  "gabrielle", "gabriel", "gabrille", "gabiellee", "gabrielhe"
                  "robin", "robben", "rubin", "robinn", "roben"
                  "john", "jhon", "johnn", "joen", "jaohn", "johne", "jon"
                  "liam", "lyam", "liama", "liame", "liaam"
                  "lucas", "locas", "leucas", "locus", "lucahs"
                  "william", "wiliam", "wileliam", "willeiam", "welliam", "williahm", "wileiam"
                  "kevin", "kevinn", "kvin", "keven", "kevn"
                  "jesse", "jessy", "jessi", "jesy", "jese", "jisy", "jasse", "jissy", "jisse"
                  "noah", "nooh", "naoh", "noa", "nohh", "noahh", "noeh"
                  "harrie", "harry", "hary", "hari", "harri", "harie", "haerie", "harrye"
                  "peter", "peteh"]
    persons = [{"name": "", "feat":""}, {"name": "", "feat":""}, {"name": "", "feat":""}]
    person_id = 0
    
    ############################
    #TODO
    # 1. edit names list 
    # 2. edit poses 
    ############################

    while rclpy.ok:
        rclpy.spin_once(task)
        if task.start:
            break
    
    task.speak("Looking for a new guest")
    while rclpy.ok:
        rclpy.spin_once(task)
        if task.tts_result:
            break

    for place in loc:
        
        task.navigate_to(task.poses[place])

        task.person = None
        task.detect_person()
        cnt = 0
        while rclpy.ok:
            rclpy.spin_once(task)
            if task.person != None:
                if task.person:
                    break
                else:
                    if cnt < 3:
                        task.detect_person()
                        task.person = None
                        cnt += 1
                    else:
                        break
                
        if not task.person:
            
            task.speak("No one here")
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            task.speak("Searching Another Place")
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            continue

        if task.person:
            task.speak("I found a new guest")
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
        
            task.speak("Can you please tell me your name?")
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
    
            while rclpy.ok:
                task.listen()
                rclpy.spin_once(task)
                end = False
                for name in names_list:
                    if name in task.speech:
                        persons[person_id]["name"] = name
                        end = True
                        break
                if end:
                    break

            task.speak(f'{persons[person_id]["name"]},   what a beautiful name!')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break

            task.speak(f'hey, {persons[person_id]["name"]},   could you please put your face close to the camera! stay steady and do not move please!')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
    
            task.speak('ready!')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            task.speak('3 2 1')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
    
            task.get_feat()
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.feat == []: 
                    task.get_feat()
                if task.feat != None:
                    break
    
            face_feat = task.say_feat(task.feat,person_id)
            task.get_logger().info(face_feat)
            persons[person_id]["feat"] = face_feat

            task.speak('going back to home')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            task.navigate_to(task.poses["home"])

            task.speak(f'the guest name is {persons[person_id]["name"]}')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            task.speak(f'{task.uni_feat[place]}')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            task.speak(f'{persons[person_id]["feat"]}')
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break
            
            person_id += 1

            if person_id == 3:
                break

            task.speak("Looking for a new guest")
            while rclpy.ok:
                rclpy.spin_once(task)
                if task.tts_result:
                    break



    task.log.close()
    


if __name__ == '__main__':
    main()