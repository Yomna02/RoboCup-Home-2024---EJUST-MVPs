# RoboCup-Home-2024---EJUST-MVPs

## Table of Contents
- [Overview](#overview)
- [Components and Assembly](#components-and-assembly)
  - [Components](#components)
  - [Assembly](#assembly)
- [Dependencies Installation](#dependencies-installation)
- [Package Installation](#package-installation)
  - [Installing ROS1 pkg](#installing-ros1-pkg)
  - [Installing ROS2 pkg](installing-ros2-pkg)
- [Usage](#usage)
- [Credits](#credits)
- [Future Work](#future-work)

## Overview
<img src="https://github.com/Yomna02/RoboCup-Home-2024---EJUST-MVPs/blob/main/pioneer.jpg?raw=true" alt="Our Robot" width="200" align="right" caption="Our Robot"/>
Welcome to the repository for the RoboCup@Home Education Competition Robot developed by the EJUST MVPs team for the year 2024. This service robot is designed to compete in the RoboCup@Home education competition, showcasing capabilities in speech recognition, navigation, mapping, and interaction. The robot integrates various sensors, hardware components, and software libraries under the umbrella of ROS2 Foxy.

---------------------------

## Components and Assembly
### Components:
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
1. Attach the sensors and hardware to the Pioneer3DX robot base.
2. Connect speakers, microphone, RPLidar sensor, ZED stereo camera, and robot base serial cable to the USB hubs.
3. Ensure laptops are connected to the hotspot for remote computing.

---------------------------

## Dependencies Installation
To install dependencies for the project, follow these steps:

1. Ensure [ROS2 Foxy Fitzroy](https://docs.ros.org/en/foxy/index.html) is installed on Ubuntu (Debian). If not, follow the installation instructions on the [ROS2 website](https://docs.ros.org/en/foxy/Installation/Ubuntu-Install-Debians.html).
2. Install [ROS1 Noetic](https://wiki.ros.org/noetic/Installation)
3. Install the following Python libraries:
    - [Whisper](https://github.com/openai/whisper) AI model for speech recognition
    - [pyttsx3](https://pypi.org/project/pyttsx3/) for text-to-speech conversion
    - [TensorFlow](https://github.com/tensorflow/tensorflow) and [OpenCV]() for image processing
    - [Nav2](https://github.com/ros-planning/navigation2) for path planning and navigation
    - [SLAM toolbox](https://github.com/SteveMacenski/slam_toolbox) for mapping and localization
4. Install the necessary ROS packages:
    - Install [ROS1 bridge](https://github.com/ros2/ros1_bridge) for communication with ROS1 components and follow the example to ensure that connection is established.
    - Install [rosaria](https://wiki.ros.org/ROSARIA) library for controlling the Pioneer mobile base and obtaining odometry feedback.

---------------------------

## Package Installation
### Installing ROS1 pkg
1. Clone the Repository: <br>
    Use `git clone` to clone the repository into the `src` directory of your ROS1 workspace.
2. Build the Workspace: <br>
    Navigate to the root directory of your workspace and build the packages using `catkin_make`.
3. Source the Workspace: <br>
    Source the setup script to add the new package to your ROS environment.
   
### Installing ROS2 pkg
1. Clone the Repository: <br>
    Use `git clone` to clone the repository into the `src` directory of your ROS2 workspace.
2. Build the Workspace: <br>
    Navigate to the root directory of your workspace and build the packages using `colcon build`.
3. Source the Workspace: <br>
    Source the setup script to add the new package to your ROS2 environment. <br>
[Add ya Beedo the git clone links and revise if any further packages are missing]

---------------------------

## Usage
1. Connect all hardware components and sensors to the on-board laptop.
2. Ensure other laptops are connected through the hotspot.
3. Launch ROS2 nodes for sensor data acquisition, perception, navigation, and interaction scripts.
4. Monitor robot behavior and performance using RViz for visualization. <br>
[Add ba2a ya Beedo the main launch/run commands to start the robot]

---------------------------

## Credits
This project was developed by the EJUST MVPs team from Egypt-Japan University of Science and Technology for the RoboCup@Home education competition in 2024. We acknowledge the contributions of team members and mentors who helped in the design, implementation, and testing phases of the project. Team members include:
- Abdallah Amr (abdallah.amr@ejust.edu.eg)
- Mostafa Osama (mostafa.eshra@ejust.edu.eg)
- Tarek Shohdy (tarek.shohdy@ejust.edu.eg)
- Yomna Mohamed (yomna.mokhtar@ejust.edu.eg)
- Ahmad Mongy (ahmad.aboelnaga@ejust.edu.eg)

We would also like to acknowledge the following libraries and tools that were used in the development of this project:

- [ROS2 Foxy Fitzroy](https://docs.ros.org/en/foxy/index.html) - Robot Operating System 2 (ROS2) provides the middleware framework for developing robotic applications.
- [ROS1 Noetic](https://wiki.ros.org/noetic/Installation) - Robot Operating System 1 (ROS1) provides the middleware framework for developing robotic applications.
- [Whisper](https://github.com/openai/whisper) - AI model for speech recognition developed by OpenAI.
- [pyttsx3](https://pypi.org/project/pyttsx3/) - Python library for text-to-speech conversion.
- [TensorFlow](https://github.com/tensorflow/tensorflow) - Open-source machine learning framework developed by Google for building and training neural networks.
- [OpenCV](https://github.com/opencv/opencv) - Open-source computer vision library.
- [Nav2](https://github.com/ros-planning/navigation2) - ROS2 navigation stack for path planning and navigation.
- [SLAM toolbox](https://github.com/SteveMacenski/slam_toolbox) - Tools for Simultaneous Localization and Mapping (SLAM) in ROS.
- [ROS1 bridge](https://github.com/ros2/ros1_bridge) - Enables communication between ROS1 and ROS2 components.
- [rosaria](https://wiki.ros.org/ROSARIA) - ROS driver for controlling the Pioneer mobile base and obtaining odometry feedback.

---------------------------

## Future Work
- Enhancing the onboard processing.
- Removing the ROS1-bridge and build a ROS2 aria library.
- Debug some main script problems and develop more sophisticated task scripts for diverse competition scenarios.
- Integrate additional sensors for enhanced perception capabilities.
