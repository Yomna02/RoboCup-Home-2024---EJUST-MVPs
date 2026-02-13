import rclpy
import time
import random
import whisper
import sounddevice as sd
import threading
import multiprocessing as mp
from rclpy.node import Node
from rclpy.action import ActionServer
from action_robocup.action import Recog
from scipy.io.wavfile import write

LISTENING = 0
SPEAKING = 1
talk = ""
class FibonacciActionServer(Node):

    def __init__(self):
        global talk
        super().__init__('whisper')
        self._action_server = ActionServer(
            self,
            Recog,
            'whisper',
            self.execute_callback)
        self.freq = 44100
        self.duration = 2
        self.model = whisper.load_model("base.en")
        talk = ""
        

    def execute_callback(self, goal_handle):
        # self.get_logger().info('Listining...')
        global talk

        listen = goal_handle.request.listen

        feedback_msg = Recog.Feedback()

        if listen:
            feedback_msg.state = LISTENING
            
            # self.get_logger().info(f'Feedback: {feedback_msg.state}')
            goal_handle.publish_feedback(feedback_msg)
        
            feedback_msg.state = SPEAKING
            # self.get_logger().info(f'Feedback: {feedback_msg.state}')
            goal_handle.publish_feedback(feedback_msg)
        
            goal_handle.succeed()

            result = Recog.Result()

            result.speech = talk
            self.get_logger().info(f'I recognized: {result.speech}')

            time.sleep(0.2)
            
            return result
        
        goal_handle.abort()

        feedback_msg.state = SPEAKING
        self.get_logger().info(f'Feedback: {feedback_msg.state}')
        goal_handle.publish_feedback(feedback_msg)

        result = Recog.Result()

        result.speech = ""


        return result

    def listener(self):
        global talk

        # self.get_logger().info('I heard: "%s"' % msg.data)
        while True:
            self.get_logger().info('Talk and I am Listening...')
            self.recording = sd.rec(int(self.duration * self.freq), samplerate=self.freq, channels=2)
            
            sd.wait()
            write("/home/beedo/colcon_ws/src/robocup/speech/recording0.wav", self.freq, self.recording)

            self.result = self.model.transcribe("/home/beedo/colcon_ws/src/robocup/speech/recording0.wav", fp16=False)
            self.get_logger().info(self.result["text"].lower())
            talk =  self.result["text"].lower()

def main(args=None):
    rclpy.init(args=args)

    fibonacci_action_server = FibonacciActionServer()

    def ros_spin():
        rclpy.spin(fibonacci_action_server)

    t1 = threading.Thread(target=ros_spin)
    t2 = threading.Thread(target=fibonacci_action_server.listener)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

if __name__ == '__main__':
    main()
