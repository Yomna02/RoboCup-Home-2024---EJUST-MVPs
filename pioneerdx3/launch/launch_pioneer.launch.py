import os
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, PythonExpression
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='pioneerdx3' #<--- CHANGE ME

    port_arg = DeclareLaunchArgument("port", default_value="/dev/ttyUSB0")
    port = LaunchConfiguration("port")

    
    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false'}.items()
    )
    
    lidar =  Node(package='rplidar_ros', executable='rplidar_composition', name='rplidar_composition',
            parameters=[
                {'Serial_port': port},
                {'frame_id': 'laser_frame'},
                {'angle_compensate': True},
                {'scan_mode': 'Standard'}
            ],
            remappings=[
                ('scan','base_scan')
            ]
        )
    
    filter = Node(
            package="laser_filters",
            executable="scan_to_scan_filter_chain",
            parameters=[
                PathJoinSubstitution([
                    get_package_share_directory("laser_filters"),
                    "examples", "range_filter_example.yaml",
                ])],
            remappings=[
                ('scan','base_scan'),
                ('scan_filtered','scan')
            ]
        )
    
    tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=["0.05", "0", "0.27", "0", "0", "0", "base_link", "laser_frame"]
    )
    
    tts = Node(
        package="speech",
        executable="text-to-speech",
    )
    
    whisper = Node(
        package="speech",
        executable="whisper_recognition",
    )

    battery = Node(
        package="tasks",
        executable="battery",
    )

    zed = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory("zed_wrapper"),'launch','zed_camera.launch.py'
                )]), launch_arguments={'camera_model': 'zed2'}.items()
    )

    face = Node(
        package="vision",
        executable="face_features")
    
    person = Node(
        package="vision",
        executable="person")

    chair = Node(
        package="vision",
        executable="chairs")
    
    face_detect = Node(
        package="vision",
        executable="detect_face")

    face_recog = Node(
        package="vision",
        executable="recog_face")
    # Launch them all!
    return LaunchDescription([
        port_arg,
        rsp,
        lidar,
        filter,
        # zed,
        tf,
        tts,
        whisper,
        battery,
        person,
        chair,
        face_detect,
        face_recog
        ])