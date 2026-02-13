import cv2
import numpy as np
import tensorflow_addons as tfa
from tensorflow.keras.models import load_model
from deepface import DeepFace
from threading import Thread
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from cv_bridge import CvBridge 
from action_robocup.action import Feat
from sensor_msgs.msg import Image
from rclpy.action import ActionServer
from transformers import pipeline, AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
from sklearn.cluster import KMeans
import webcolors

def get_dominant_color(image_path, k=1, region_size=0.5):
    # Read the image
    image = cv2.imread(image_path)
    # Convert the image from BGR to RGB format
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get the dimensions of the image
    height, width, _ = image.shape
    
    # Define the central region
    central_height = int(height * region_size)
    central_width = int(width * region_size)
    start_x = (width - central_width) // 2
    start_y = (height - central_height) // 2
    end_x = start_x + central_width
    end_y = start_y + central_height
    
    # Crop the central region
    central_region = image[start_y:end_y, start_x:end_x]
    
    # Reshape the central region to be a list of pixels
    pixels = central_region.reshape((-1, 3))
    
    # Use KMeans to find the most common color
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)
    
    # Get the RGB values of the cluster centers (dominant colors)
    dominant_color = kmeans.cluster_centers_.astype(int)[0]
    
    return dominant_color

def closest_color(requested_color):
    min_colors = {}
    for key, name in webcolors._definitions._CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def get_color_name(requested_color):
    try:
        closest_name = webcolors.rgb_to_name(requested_color)
    except ValueError:
        closest_name = closest_color(requested_color)
    return closest_name

# Define the pipeline
pipe = pipeline("image-classification", model="enzostvs/hair-color")

# Load model and processor directly
hair_image_processor = AutoImageProcessor.from_pretrained("enzostvs/hair-color")
hair_model = AutoModelForImageClassification.from_pretrained("enzostvs/hair-color")


def draw_results(input_image, det, output,objs):
    font = cv2.FONT_HERSHEY_PLAIN

    labels = ['5_o_Clock_Shadow', 'Arched_Eyebrows', 'Attractive',
              'Bags_Under_Eyes', 'Bald', 'Bangs', 'Big_Lips', 'Big_Nose',
              'Black_Hair', 'Blond_Hair', 'Blurry', 'Brown_Hair', 'Bushy_Eyebrows',
              'Chubby', 'Double_Chin', 'Eyeglasses', 'Goatee', 'Gray_Hair',
              'Heavy_Makeup', 'High_Cheekbones', 'Male', 'Mouth_Slightly_Open',
              'Mustache', 'Narrow_Eyes', 'No_Beard', 'Oval_Face', 'Pale_Skin',
              'Pointy_Nose', 'Receding_Hairline', 'Rosy_Cheeks', 'Sideburns',
              'Smiling', 'Straight_Hair', 'Wavy_Hair', 'Wearing_Earrings',
              'Wearing_Hat', 'Wearing_Lipstick', 'Wearing_Necklace',
              'Wearing_Necktie', 'Young']

    position0 = np.where(output[0] > 0)[0]
    # position0 = [3, 4, 6, 7, 9, 10, 11, 15, 17, 20, 22, 23, 24, 25, 26, 31, 32, 33, 34, 35, 36, 37, 39]
    # sorted_indices = np.argsort(output[0][position0])[::-1]
    # position0 = position0[sorted_indices]
    count = 15
    output_list = []
    if objs:
        output_list.append(objs[0]["dominant_race"])
        cv2.putText(input_image, objs[0]["dominant_race"] , (det[2], 15 + count), font, 1, (0, 0, 255), 2, cv2.LINE_AA)
    count +=30
    for i2 in range(len(position0)):
        label_text = f"{labels[position0[i2]]}: {np.round(output[0][position0[i2]], 3)}"
        
        cv2.putText(input_image, label_text, (det[2], 15 + count), font, 1.5, (0, 0, 255), 2, cv2.LINE_AA)
        count += 30
        output_list.append(label_text)
        if labels[i2] == "Male":
            label_text = f"Female: {1 - np.round(output[0][position0[i2]], 3)}"
            output_list.append(label_text)
    return input_image, output_list

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
model = load_model("/home/beedo/colcon_ws/src/robocup/vision/vision/model_inception_facial_keypoints.h5",
                   custom_objects={"Adamw":tfa.optimizers.AdamW},compile=False) # updated the loading function

def output1(model, image_batch):
    return model.predict(image_batch)

def objs1(frame):
    return DeepFace.analyze(img_path = frame,actions = ['race'])
    
def process_frame(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        face_roi = frame[y:y + h, x:x + w]
        image_batch = np.expand_dims(cv2.resize(face_roi, (128, 128)) / 256, axis=0)

        # Run output1 in a separate thread
        output_thread = Thread(target=output_thread_worker, args=(model, image_batch))
        output_thread.start()

        try:
            # Run objs1 in the main thread
            objs = objs1(frame)
        except Exception as e:
            print(f"Error in objs1: {e}")
            objs = []

        # Wait for the output1 thread to finish
        output_thread.join()

        # Get the result from the output1 thread
        output_result = output_thread_worker.result

        # frame, label_text = draw_results(frame, (x, y, x + w, y + h), output_result, objs)
        # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # os.chdir(r"/home/beedo/face_feat_img")
        # cv2.imwrite("face_feat.png", frame)
        
        return frame, x, y, x + w, y + h, output_result, objs

def output_thread_worker(model, image_batch):
    result = output1(model, image_batch)
    output_thread_worker.result = result


def get_face_feat(index):
    image_path = r"/home/beedo/face_feat_img/face{index}_{id}.png"
    # image_path = r"/home/beedo/test.jpg"
    total_result = np.zeros(40)
    race = {}
    captures = 35
    count = 0

    hair = {}
    shirt = {}

    for i in range(5,captures):
        try:

            try:
                frame = cv2.imread(image_path.format(id=i, index=index))
                
                _, xmin, ymin, xmax, ymax, output_result, objs = process_frame(frame)
                output_result = np.array(output_result[0])
                try:
                    race[objs[0]["dominant_race"]] += 1
                except:
                    race[objs[0]["dominant_race"]] = 1
                total_result += output_result
                count += 1

                image = Image.open(image_path.format(id=i, index=index))
                image.crop((xmin, ymin-35, xmax, ymax))
                inputs = hair_image_processor(image, return_tensors="pt")

                # Perform the classification
                with torch.no_grad():  # Disable gradient calculation for inference
                    hair_color = hair_model(**inputs)
                    predicted_label = hair_color.logits.argmax(-1).item()

                try:
                    hair[hair_model.config.id2label[predicted_label]] += 1
                except:
                    hair[hair_model.config.id2label[predicted_label]] = 1
            except:
                pass

            dominant_color = get_dominant_color(image_path.format(id=i, index=index))
            color_name = get_color_name(dominant_color)

            try:
                shirt[color_name] += 1
            except:
                shirt[color_name] = 1
            
        except:
            continue
    try:
        total_result /= count
        total_result = [total_result]
        dominant_race = max(race, key=race.get)
        dominant_race = [{"dominant_race":dominant_race}]
        frame, label_text = draw_results(frame, (xmin, ymin, xmax, ymax), total_result, dominant_race)
        cv2.rectangle(frame, (xmin, ymin-35), (xmax, ymax), (0, 255, 0), 2)
    except:
        label_text = []

    os.chdir(r"/home/beedo/face_feat_img")
    cv2.imwrite(f"face_feat_final{index}.png", frame)
    print("results done")

    try:
        hair_color = max(hair, key=hair.get)
        label_text.append(f"{hair_color}")
    except:
        pass

    shirt_color = max(shirt, key=shirt.get)
    label_text.append(f"{shirt_color}")

    print(label_text)

    return label_text

# x = get_face_feat()
class FaceFeat(Node):
    def __init__(self) -> None:
        super().__init__('face_feat')
        self._action_server = ActionServer(
            self,
            Feat,
            'face_feat',
            self.execute_callback)
        
        self.index = 1
        self._cvbridge = CvBridge()
        self.frame = None
    
    def execute_callback(self, goal_handle):
        self.get_logger().info('getting face features...')
        # try:
        cap = cv2.VideoCapture(2)
        for i in range(35):
            # rclpy.spin_once(self)
            try:    
                ret, frame = cap.read()
                frame = frame[:,200:472]
                self.get_logger().info('Capture')
                os.chdir(r"/home/beedo/face_feat_img")
                cv2.imwrite("face{index}_{id}.png".format(id=i, index=self.index), frame)
            except:
                self.get_logger().info('SKIP')
                continue
        cap.release()
        features = get_face_feat(self.index)
        self.index += 1
        # except:
        #     features = []

        goal_handle.succeed()

        result = Feat.Result()

        result.values = features
        
        return result 
        
def main(args=None):

    rclpy.init(args=args)
    aruco_detector = FaceFeat()
    rclpy.spin(aruco_detector)
    # Destroy the node explicitly
    cv2.destroyAllWindows()  
    aruco_detector.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()