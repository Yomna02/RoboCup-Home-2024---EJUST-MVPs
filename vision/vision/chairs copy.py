from ultralytics import YOLO
import cv2

# Mapping of class numbers to labels
num_to_label = {0.0 : "person", 56.0 : "chair"}

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
    results = model.predict(source = img, conf = 0.5)
    boxes = results[0].boxes.data.tolist()
    persons = list()
    occupied_chairs = list()
    empty_chairs = list()
    
    for box in boxes:
        # Check if the object is a person or a chair
        if num_to_label.get(box[5], "person") == "person":
            person_box = box[0:4]
            persons.append(person_box)
        elif num_to_label.get(box[5], "person") == "chair":
            chair_box = box[0:4]
            collision_detected = False
            
            # Check for collisions with persons
            for person in persons:
                if box_collision(person, chair_box):
                    collision_detected = True
                    break

            # Add the chair to the appropriate list
            if collision_detected:
                occupied_chairs.append(chair_box)
            else:
                empty_chairs.append(chair_box)
    return empty_chairs

def draw(img, empty_chairs):
    """
    Draw rectangles and labels for empty chairs on an image.

    Args:
        img (numpy.ndarray): Input image.
        empty_chairs (list): List of empty chair bounding boxes.

    Returns:
        numpy.ndarray: Image with rectangles and labels drawn.
    """
    for chair in empty_chairs:
        label_position = (int(chair[0]), int(chair[1]) - 10)
        label_size, baseline = cv2.getTextSize("Empty Chair", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 3)
        cv2.rectangle(img, (int(chair[0]), label_position[1] + baseline - label_size[1] - 10),
                      (label_position[0] + label_size[0], int(chair[1])), (0, 255, 0), -1)
        cv2.rectangle(img, (int(chair[0]), int(chair[1])), (int(chair[2]), int(chair[3])), (0, 255, 0), 2)
        cv2.putText(img, "Empty Chair", label_position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
    return img

# Test with webcam input
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    empty_chairs = detect(frame)
    frame = draw(frame, empty_chairs)
    cv2.imshow("Empty Chairs", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()