import rclpy
from rclpy.node import Node
import psutil
from std_msgs.msg import Int32


class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Int32, 'battery_lab', 10)
        timer_period = 0.01  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.battery = psutil.sensors_battery()

    def timer_callback(self):
        msg = Int32()
        percent = int(self.battery.percent)
        msg.data = percent
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    try:
        rclpy.spin(minimal_publisher)

    except KeyboardInterrupt:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        minimal_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()