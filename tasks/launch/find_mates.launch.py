import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='pioneer_3dx' #<--- CHANGE ME

    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    script = Node(package='tasks', executable='mates')
    feat = Node(package='vision', executable='face_features')
    person = Node(package='vision', executable='person')

    # Launch them all!
    return LaunchDescription([
        # feat,
        script,
        feat,
        person
    ])
