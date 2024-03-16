import rclpy
import whisper
import sounddevice as sd

from scipy.io.wavfile import write
from rclpy.node import Node
from std_msgs.msg import Int32

class Speech(Node):

    def __init__(self):
        super().__init__('speech_whisper')
        self.subscription = self.create_subscription(
            Int32,
            '/mvp/state',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.freq = 44100
        self.duration = 2


    def listener_callback(self, msg):
        #self.get_logger().info('I heard: "%s"' % msg.data)
        if msg.data == 1:
            self.get_logger().info('Talk')
            self.recording = sd.rec(int(self.duration * self.freq), samplerate=self.freq, channels=2)
            
            sd.wait()
            write("/home/beedo/colcon_ws/src/robocup/speech/recording0.wav", self.freq, self.recording)

            model = whisper.load_model("small.en")
            self.result = model.transcribe("/home/beedo/colcon_ws/src/robocup/speech/recording0.wav", fp16=False)
            self.get_logger().info(self.result["text"])


def main(args=None):
    rclpy.init(args=args)

    speech_whisper = Speech()

    rclpy.spin(speech_whisper)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    speech_whisper.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main() 