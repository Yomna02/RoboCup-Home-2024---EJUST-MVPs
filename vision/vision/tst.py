# # import cv2
# # import os 
# # import random

# # def main():

# #     cap = cv2.VideoCapture(2)
    
# #     while True:
# #         ret, frame = cap.read()
# #         cv2.imshow('frame', frame)
# #         if cv2.waitKey(1) & 0xFF == ord('q'):
# #             break
# #     cap.release()
# #     cv2.destroyAllWindows()
    
# # if __name__ == '__main__':
# #     main()

# from TTS.api import TTS
# from playsound import playsound

# text = "お元気ですか"
# text = "はい、 げんき です。"
# text = "ça va bien, merci"
# # text = "Hallo, wie geht es dir?"

# tts_en = TTS(model_name="tts_models/en/blizzard2013/capacitron-t2-c150_v2", progress_bar=True, gpu=False)
# tts_ja = TTS(model_name="tts_models/ja/kokoro/tacotron2-DDC", progress_bar=True, gpu=False)
# tts_de = TTS(model_name="tts_models/de/thorsten/tacotron2-DCA", progress_bar=True, gpu=False)
# tts_fr = TTS(model_name="tts_models/fr/css10/vits", progress_bar=True, gpu=False)

# # Run TTS
# tts_fr.tts_to_file(text=text, file_path="intro.wav")
# # Play the audio file
# playsound("intro.wav")
 
# # print(TTS.list_models())

# # import pycountry

# # languages = set()

# # for model_name in TTS.list_models():
# #   country_code = model_name.split("/")[1]
# #   country_language = pycountry.languages.get(alpha_2=country_code)
# #   if country_language is not None:
# #     print("{0}: {1}".format(country_language.name, model_name))
# #     languages.add(country_language.name)

# # print()
# # print("Unique Languages ({0}):".format(len(languages)))
# # print(languages)

# import ctypes
# from ctypes import *

# winmm = windll.winmm
# print 'waveInGetNumDevs=',winmm.waveInGetNumDevs()

from ultralytics import YOLO
import cv2

model = YOLO('yolov8s.pt')

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    results = model(frame, verbose=False)
    print(results)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
cap.release()
cv2.destroyAllWindows()