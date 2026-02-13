import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node



def generate_launch_description():


    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    script = Node(package='tasks', executable='curry_luggage')
    follow = Node(package='follower', executable='follower')
    pose = Node(package='vision', executable='human_pose')
    bag = Node(package='vision', executable='bag')

    # Launch them all!
    return LaunchDescription([
        bag,
        follow,
        pose,
        script,
    ])
