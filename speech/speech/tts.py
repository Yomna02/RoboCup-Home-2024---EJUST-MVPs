import time
import rclpy
import pyttsx3
from rclpy.action import ActionServer
from rclpy.node import Node
from action_robocup.action import TTS
from std_msgs.msg import String, Bool
from TTS.api import TTS as tts
from playsound import playsound

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
        self.lang_sub = self.create_subscription(String, '/mvp/language', self.lang_callback, 10)
        self.mic = self.create_subscription(Bool, '/mvp/mic', self.mic_callback, 10)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)     # setting up new voice rate
        tts_en = tts(model_name="tts_models/en/blizzard2013/capacitron-t2-c150_v2", progress_bar=True, gpu=False)
        tts_ja = tts(model_name="tts_models/ja/kokoro/tacotron2-DDC", progress_bar=True, gpu=False)
        tts_de = tts(model_name="tts_models/de/thorsten/tacotron2-DCA", progress_bar=True, gpu=False)
        tts_fr = tts(model_name="tts_models/fr/css10/vits", progress_bar=True, gpu=False)
        self.models = {"en": tts_en, "ja": tts_ja, "de": tts_de, "fr": tts_fr}
        self.language = "en"
        self.mic_status = False

    def mic_callback(self, msg):
        self.mic_status = msg.data
        if self.mic_status:
            self.engine.setProperty('volume',0.3)
            self.engine.say("a")
            self.engine.runAndWait()
            
    def lang_callback(self, msg):
        self.language = msg.data

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

        if self.language == "en":
            self.engine.say(speech)
            self.engine.runAndWait()
        else:
            self.models[self.language].tts_to_file(text=speech, file_path="intro.wav")
            playsound("intro.wav")
        
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