import time
import rclpy
import pyttsx3
from rclpy.action import ActionServer
from rclpy.node import Node
from action_robocup.action import TTS

LISTENING = 0
SPEAKING = 1

class FibonacciActionServer(Node):

    def __init__(self):
        super().__init__('tts')
        self._action_server = ActionServer(
            self,
            TTS,
            'tts',
            self.execute_callback)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 140)     # setting up new voice rate


    def execute_callback(self, goal_handle):


        feedback_msg = TTS.Feedback()

        feedback_msg.state = SPEAKING


        speech = goal_handle.request.speech
        if speech == "a":
            self.engine.setProperty('volume',0.3)
        else:
            self.engine.setProperty('volume',1)

        self.get_logger().info(f'Feedback: {feedback_msg.state}')
        goal_handle.publish_feedback(feedback_msg)
        

        self.get_logger().info('I am Speaking...')
        self.engine.say(speech)
        self.engine.runAndWait()
        
        feedback_msg.state = LISTENING
        self.get_logger().info(f'Feedback: {feedback_msg.state}')
        goal_handle.publish_feedback(feedback_msg)


        goal_handle.succeed()

        result = TTS.Result()

        result.finished = True

        return result


def main(args=None):
    rclpy.init(args=args)

    fibonacci_action_server = FibonacciActionServer()

    rclpy.spin(fibonacci_action_server)


if __name__ == '__main__':
    main()