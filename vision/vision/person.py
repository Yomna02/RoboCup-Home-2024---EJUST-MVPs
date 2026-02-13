from ultralytics import YOLO
import cv2
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from action_robocup.action import Person

# Mapping of class numbers to labels
num_to_label = {0.0 : "person"}

# Initialize YOLO model
model = YOLO('yolov8s.pt')

def box_collision(box1, box2):
    """
    Check if there is a collision between two bounding boxes.

    Args:
        box1 (list): Coordinates of the first bounding box in the format [x_min, y_min, x_max, y_max].
        box2 (list): Coordinates of the second bounding box in the format [x_min, y_min, x_max, y_max].

    Returns:
        bool: True if there is a collision, False otherwise.
    """
    return not (box1[2] < box2[0] or
                box1[0] > box2[2] or
                box1[3] < box2[1] or
                box1[1] > box2[3])

def detect(img):
    """
    Detect empty chairs in an image using YOLO model.

    Args:
        img (numpy.ndarray): Input image.

    Returns:
        list: List of empty chair bounding boxes.
    """
    # Perform YOLO object detection
    results = model.predict(source = img, conf = 0.3)
    boxes = results[0].boxes.data.tolist()

    person = None
    w_max = 0
    for box in boxes:
        # Check if the object is a person or a chair
        if num_to_label.get(box[5], "unrelated") == "person":
            person_box = box[0:4]
            x = int(person_box[0])
            w = int(person_box[2] - person_box[0])
            y = int(person_box[1])
            h = int(person_box[3] - person_box[1])
            if w > 50:
                person = box[0:4]
    return person

def draw(img, person):
    """
    Draw rectangles and labels for empty chairs on an image.

    Args:
        img (numpy.ndarray): Input image.
        persons (list): List of persons bounding boxes.

    Returns:
        numpy.ndarray: Image with rectangles and labels drawn.

            """
    if person == None:
        return img
    label_position = (int(person[0]), int(person[1]) - 10)
    label_size, baseline = cv2.getTextSize("Person", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 3)
    cv2.rectangle(img, (int(person[0]), label_position[1] + baseline - label_size[1] - 10),
                    (label_position[0] + label_size[0], int(person[1])), (0, 255, 0), -1)
    cv2.rectangle(img, (int(person[0]), int(person[1])), (int(person[2]), int(person[3])), (0, 255, 0), 2)
    cv2.putText(img, "Person", label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    return img

class PersonDetect(Node):
    def __init__(self) -> None:
        super().__init__('bag_choose')
        self._action_server = ActionServer(
            self,
            Person,
            'person',
            self.execute_callback)
        
        self.index = 1
            
    def execute_callback(self, goal_handle):
        self.get_logger().info('Waiting for guests...')
        out = False
        cap = cv2.VideoCapture(2)
        for i in range(60):
            ret, frame = cap.read()
            frame = frame[:,:672]
            person = detect(frame)
            frame = draw(frame, person)
            cv2.imshow("dfs", frame)
            cv2.waitKey(1)
            if person != None:
                out = True
                break

        cap.release()
        cv2.destroyAllWindows()

        goal_handle.succeed()

        result = Person.Result()

        result.person = out
        
        return result 

def main(args=None):

    rclpy.init(args=args)
    aruco_detector = PersonDetect()
    rclpy.spin(aruco_detector)
    # Destroy the node explicitly
    cv2.destroyAllWindows()  
    aruco_detector.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

