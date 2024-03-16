import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node



def generate_launch_description():
    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='pioneerdx3' #<--- CHANGE ME

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false'}.items()
    )

    lidar =  Node(package='rplidar_ros', executable='rplidar_composition', name='rplidar_composition',
            parameters=[
                {'Serial_port': '/dev/tty/USB0'},
                {'frame_id': 'laser_frame'},
                {'angle_compensate': True},
                {'scan_mode': 'Standard'}
            ]
        )
    
    rviz = Node(package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', get_package_share_directory('pioneerdx3') + '/config/main.rviz']
        )

     # Launch them all!
    return LaunchDescription([
        rsp,
        lidar,
        rviz
    ])
