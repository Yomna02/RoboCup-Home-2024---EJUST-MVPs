import tkinter as tk
from screeninfo import get_monitors
from PIL import Image, ImageTk
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Int32MultiArray, Float32, String

# Language Dictionary
LANGUAGE_DICT = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "ja": "Japanese",
}

LANGUAGE_IND = {
    "en": 0,
    "de": 1,
    "fr": 2,
    "ja": 3,
}

class gui:
    """
    Class to create the GUI for the control room.
    
    Args:
        window(tk.Tk): The main window of the GUI.
        geometry(tuple): The geometry of the screen.
        
    Attributes:
        dir(str): The directory where the images are stored.
        battery_level(int): The battery level of the robot.
        language(int): The language selected.
        greet_judges_bool(bool): The flag to greet the judges.
        go_to_kitchen_bool(bool): The flag to go to the kitchen.
        go_to_living_bool(bool): The flag to go to the living room.
    """
    def __init__(self, window, geometry):
        self.window = window
        self.geometry = geometry
        self.dir = "/home/beedo"                   # Change this to the directory where the images are stored

        # Variables
        self.battery_level = 80
        self.language = 0
        self.greet_judges_bool = False
        self.go_to_kitchen_bool = False
        self.go_to_living_bool = False

        self.create_widgets()

    def create_widgets(self):
        """Method to create the widgets of the GUI."""
        self.screen_width = self.geometry[0]
        self.screen_height = self.geometry[1]
        window_size = f"{self.screen_width}x{self.screen_height}+{self.geometry[2]}+{self.geometry[3]}"
        self.window.geometry(window_size)
        self.window.title("Control Room")

        title_font = ("Garamond", 35, "bold")
        label_font = ("Garamond", 20, "bold")

        # Background Image
        self.bg = Image.open(
            f"{self.dir}/back.jpg"
        )
        self.bg = self.bg.resize((self.screen_width, self.screen_height))
        self.bg = ImageTk.PhotoImage(self.bg)

        self.back_canvas = tk.Canvas(
            self.window, width=self.screen_width, height=self.screen_height
        )
        self.back_canvas.create_image(0, 0, image=self.bg, anchor="nw")
        self.back_canvas.pack(fill="both", expand=True)

        # Title
        self.back_canvas.create_text(self.screen_width // 2, 150, text="Control Room", font=title_font, fill="#000000")


        tk.Frame(self.back_canvas, bg="").grid(
            row=1, column=0, padx=10, pady=100, sticky="ew", columnspan=3
        )

        self.back_canvas.grid_columnconfigure(0, weight=1)
        self.back_canvas.grid_columnconfigure(1, weight=1)
        self.back_canvas.grid_columnconfigure(2, weight=1)

        # Battery
        self.battery_frame = tk.Frame(self.back_canvas, bg="#dbe0ec")
        self.battery_frame.grid(row=0, column=2, padx=10, pady=20, sticky="e")

        self.battery_canvas = tk.Canvas(self.battery_frame, width=200, height=50)
        self.battery_canvas.pack()
        self.battery_rect = self.battery_canvas.create_rectangle(10, 10, 190, 40, outline='black', width=2)
        self.battery_fill = self.battery_canvas.create_rectangle(12, 12, 12, 38, fill='green', width=0)
        self.battery_text = self.battery_canvas.create_text(100, 25, text="0%", fill="black", font=('Arial', 12, 'bold'))

        # Language
        self.language_frame = tk.Frame(self.back_canvas, bg="#dbe0ec")
        self.language_frame.grid(row=2, column=0, padx=50, pady=20, sticky="ew", columnspan=3)

        self.language_frame.grid_columnconfigure(0, weight=1)
        self.language_frame.grid_columnconfigure(1, weight=1)
        self.language_frame.grid_columnconfigure(2, weight=1)
        self.language_frame.grid_columnconfigure(3, weight=1)
        
        self.english_label = tk.Label(self.language_frame, text="English", font=label_font, bg="white")
        self.english_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.german_label = tk.Label(self.language_frame, text="German", font=label_font, bg="white")
        self.german_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.french_label = tk.Label(self.language_frame, text="French", font=label_font, bg="white")
        self.french_label.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.japanese_label = tk.Label(self.language_frame, text="Japanese", font=label_font, bg="white")
        self.japanese_label.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # Tasks
        self.tasks_frame = tk.Frame(self.back_canvas, bg="#dbe0ec")
        self.tasks_frame.grid(row=3, column=0, padx=(self.screen_width // 3, self.screen_width // 3), pady=20, sticky="nsew", columnspan=3)

        self.tasks_frame.grid_rowconfigure(0, weight=1)
        self.tasks_frame.grid_rowconfigure(1, weight=1)
        self.tasks_frame.grid_rowconfigure(2, weight=1)
        self.tasks_frame.grid_columnconfigure(0, weight=1)
        
        self.greet_judges_button = tk.Button(self.tasks_frame, text="Greet Judges", height=2, font=label_font, bg="white", command=self.greet_judges)
        self.greet_judges_button.grid(row=0, column=0, padx=10, pady=30, sticky="nsew")

        self.go_to_kitchen_button = tk.Button(self.tasks_frame, text="Go to Kitchen", height=2, font=label_font, bg="white", command=self.go_to_kitchen)
        self.go_to_kitchen_button.grid(row=1, column=0, padx=10, pady=30, sticky="nsew")

        self.go_to_living_button = tk.Button(self.tasks_frame, text="Go to Living Room", height=2, font=label_font, bg="white", command=self.go_to_living)
        self.go_to_living_button.grid(row=2, column=0, padx=10, pady=30, sticky="nsew")

        # Test usage
        self.set_battery_level(self.battery_level)
        self.set_language(self.language)
        self.pop_txt = ""
        # self.show_popup("This is a test message.")

    def set_battery_level(self, level):
        """
        Method to set the battery level in the GUI.

        Args:
            level(int): The battery level of the robot.
        """
        level = max(0, min(level, 100))
        fill_width = 1.76 * level
        self.battery_canvas.coords(self.battery_fill, 12, 12, 12 + fill_width, 38)
        if level > 20:
            fill = "green"
        elif level > 10:
            fill = "orange"
            self.show_popup("Battery level is getting low!")
        else:
            fill = "red"
            self.show_popup("Battery level is very low!")
            
        self.battery_canvas.itemconfig(self.battery_fill, fill=fill)
        self.battery_canvas.itemconfig(self.battery_text, text=f"{level}%")

    def set_language(self, language):
        """
        Method to set the language in the GUI.
        The selected language will be highlighted in green.

        Args:
            language(int): The language selected.
        """
        for i in range(4):
            if i == language:
                self.language_frame.grid_slaves(row=0, column=i)[0].config(bg="green")
            else:
                self.language_frame.grid_slaves(row=0, column=i)[0].config(bg="white")

    def greet_judges(self):
        """Method to set the flag to greet the judges."""
        self.greet_judges_bool = True

    def go_to_kitchen(self):
        """Method to set the flag to go to the kitchen."""
        self.go_to_kitchen_bool = True

    def go_to_living(self):
        """Method to set the flag to go to the living room."""
        self.go_to_living_bool = True

    def show_popup(self, message):
        """Method to create a popup window with a specific message.

        Args:
            message (str): The message to display in the popup.
        """
        if self.pop_txt == message:
            return
        self.pop_txt = message
        popup = tk.Toplevel(self.window)
        popup.title("Message")
        popup.geometry(f"300x150+{self.window.winfo_screenwidth()//2-150}+{self.window.winfo_screenheight()//2-75}")
        
        label = tk.Label(popup, text=message, font=("Times New Roman", 16))
        label.pack(pady=20)
        
        close_button = tk.Button(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=10)

class guiNode(Node):
    """
    Class to create the ROS2 node for the GUI.
    
    Args:
        gui_obj(gui): The GUI object.
        
    Attributes:
        battery_subscriber(rclpy.subscription): The subscriber to the battery topic.
        language_subscriber(rclpy.subscription): The subscriber to the language topic.
        greet_judges_pub(rclpy.publisher): The publisher to the greet judges topic.
        go_to_kitchen_pub(rclpy.publisher): The publisher to the go to kitchen topic.
        go_to_living_pub(rclpy.publisher): The publisher to the go to living room topic.
        timer(rclpy.timer): The timer to publish the flags.
    """
    def __init__(self, gui_obj: gui):
        super().__init__("GUI_node")
        self.battery_subscriber = self.create_subscription(
            Float32, "/battery_voltage", self.battery_callback, 10
        )
        self.language_subscriber = self.create_subscription(
            String, "/mvp/language", self.language_callback, 10
        )

        self.greet_judges_pub = self.create_publisher(Bool, "/mvp/greet_judges", 10)
        self.go_to_kitchen_pub = self.create_publisher(Bool, "/mvp/go_to_kitchen", 10)
        self.go_to_living_pub = self.create_publisher(Bool, "/mvp/go_to_living", 10)

        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.gui_obj = gui_obj
        self.gui_obj.set_language(0)

    def battery_callback(self, msg):
        """
        Callback function for the battery topic.
        The battery level is updated in the GUI.
        
        Args:
            msg(Int32MultiArray): The message received from the battery topic.
        """
        self.gui_obj.battery_level = int(msg.data / 12.5)
        self.gui_obj.set_battery_level(int(self.gui_obj.battery_level))

    def language_callback(self, msg):
        """
        Callback function for the language topic.
        The language is updated in the GUI.

        Args:
            msg(Int32MultiArray): The message received from the language topic.
        """
        lang = msg.data
        if lang in LANGUAGE_IND.keys():
            self.gui_obj.language = LANGUAGE_IND[lang]
            self.gui_obj.set_language(self.gui_obj.language)

    def timer_callback(self):
        """Method to publish the flags to the respective topics."""
        greet_judges_msg = Bool()
        greet_judges_msg.data = self.gui_obj.greet_judges_bool
        self.greet_judges_pub.publish(greet_judges_msg)
        self.get_logger().info(f"Greet Judges: {greet_judges_msg.data}")

        go_to_kitchen_msg = Bool()
        go_to_kitchen_msg.data = self.gui_obj.go_to_kitchen_bool
        self.go_to_kitchen_pub.publish(go_to_kitchen_msg)
        self.get_logger().info(f"Go to Kitchen: {go_to_kitchen_msg.data}")

        go_to_living_msg = Bool()
        go_to_living_msg.data = self.gui_obj.go_to_living_bool
        self.go_to_living_pub.publish(go_to_living_msg)
        self.get_logger().info(f"Go to Living Room: {go_to_living_msg.data}")

        self.gui_obj.greet_judges_bool = False
        self.gui_obj.go_to_kitchen_bool = False
        self.gui_obj.go_to_living_bool = False

def get_screens_info(screen):
    """
    Function to get the screen information.

    Args:
        screen(int): The screen number.

    Returns:
        tuple: The screen width, screen height, screen x-coordinate, and screen y-coordinate
    """
    monitors = get_monitors()
    first_screen = monitors[screen]
    return first_screen.width, first_screen.height, 0, 0

def ros_init(gui_obj):
    """
    Function to initialize the ROS2 node.

    Args:
        gui_obj(gui): The GUI object.
    """
    rclpy.init(args=None)
    node = guiNode(gui_obj)
    rclpy.spin(node)
    rclpy.shutdown()

def main():
    """Main function to create the GUI and start the ROS2 node."""
    window = tk.Tk()
    copilot_interface = gui(window, get_screens_info(0))

    ros_thread = threading.Thread(target=ros_init, args = (copilot_interface, ))
    ros_thread.start()

    window.mainloop()

if __name__ == "__main__":
    main()
