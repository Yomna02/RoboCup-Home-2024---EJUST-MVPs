# RoboCup-Home-2024---EJUST-MVPs

## Table of Contents
- [Overview](#overview)
- [Components and Assembly](#components-and-assembly)
  - [Components](#components)
  - [Assembly](#assembly)
- [Dependencies Installation](#dependencies-installation)
- [Package Installation](#package-installation)
- [Usage](#usage)
- [Credits](#credits)
- [Future Work](#future-work)

## Overview
Welcome to the repository for the RoboCup@Home Education Competition Robot developed by the EJUST MVPs team for the year 2024. This service robot is designed to compete in the RoboCup@Home education competition, showcasing capabilities in speech recognition, navigation, mapping, and interaction. The robot integrates various sensors, hardware components, and software libraries under the umbrella of ROS2 Foxy.

---------------------------

## Components and Assembly
### Components:
<img src="https://github.com/Yomna02/RoboCup-Home-2024---EJUST-MVPs/blob/main/pioneer.jpg?raw=true" alt="Our Robot" width="200" align="right" caption="Our Robot"/>
- Robot Base: Pioneer3DX
- Sensors:
  - RPLidar Sensor
  - ZED Stereo Camera
- Hardware:
  - Speakers
  - Microphone
  - USB Hubs (2)
- Computing Setup:
  - Three laptops connected through a hotspot
  
### Assembly:
1. Attach the RPLidar sensor and ZED stereo camera to the Pioneer3DX robot base.
2. Connect speakers, microphone, and USB hubs to the robot base as needed.
3. Ensure laptops are connected to the hotspot for remote computing.

---------------------------

## Dependencies Installation
To install dependencies for the project, follow these steps:

1. Ensure ROS2 Foxy Fitzroy is installed on your system. If not, follow the installation instructions on the ROS2 website.
2. Install the following Python libraries:
    - Whisper AI model for speech recognition
    - pyttsx3 for text-to-speech conversion
    - TensorFlow and OpenCV for image processing
    - Nav2 for path planning and navigation
    - SLAM toolbox for mapping and localization
3. Install the necessary ROS packages:
    - Install ROS1 bridge for communication with ROS1 components.
    - Install rosaria library for controlling the Pioneer mobile base and obtaining odometry feedback.

---------------------------

## Package Installation

---------------------------

## Usage
1. Connect all hardware components and sensors to the on-board laptop.
2. Ensure other laptops are connected through the hotspot.
3. Launch ROS2 nodes for sensor data acquisition, perception, navigation, and interaction scripts.
4. Monitor robot behavior and performance using RViz for visualization.
[Add ya Beedo the main launch commands to start the robot]

---------------------------

## Credits
This project was developed by the EJUST MVPs team from Egypt-Japan University of Science and Technology for the RoboCup@Home education competition in 2024. Team members include:
- Abdallah Amr (abdallah.amr@ejust.edu.eg)
- Mostafa Osama (mostafa.eshra@ejust.edu.eg)
- Tarek Shohdy (tarek.shohdy@ejust.edu.eg)
- Yomna Mohamed (yomna.mokhtar@ejust.edu.eg)
- Ahmad Mongy (ahmad.aboelnaga@ejust.edu.eg)

We acknowledge the contributions of team members and mentors who helped in the design, implementation, and testing phases of the project. We would also like to acknowledge the following libraries and tools that were used in the development of this project:

[Add credits for used pkgs]

---------------------------

## Future Work
- Enhancing the onboard processing.
- Removing the ROS1-bridge and build a ROS2 aria library.
- Debug some main script problems and develop more sophisticated task scripts for diverse competition scenarios.
- Integrate additional sensors for enhanced perception capabilities.
