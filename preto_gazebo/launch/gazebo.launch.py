#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch.substitutions import Command

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_name = 'preto_gazebo'
    pkg_description = 'preto_description'

    pkg_path = get_package_share_directory(pkg_name)
    pkg_description_path = get_package_share_directory(pkg_description)
    
    ros_gz_sim_pkg = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_path, 'world', 'warehouse.sdf')

    urdf_file = os.path.join(pkg_description_path, 'urdf', 'preto_description.urdf')

    controllers_config_file = os.path.join(pkg_path, 'config', 'controllers.yaml')

    with open(urdf_file, 'r') as file:
        description = file.read().replace('CONTROLLER_PARAMS_FILE', controllers_config_file)
    
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_pkg, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': description,
            'use_sim_time': True
        }],
        output='screen'
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'preto',
            '-topic', 'robot_description',
            '-x', '0',
            '-y', '0',
            '-z', '0.1',
        ],
        output='screen'
    )

    bridge_config = os.path.join(pkg_path, 'config', 'bridge.yaml')

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p', f'config_file:={bridge_config}',
        ],
        output='screen'
    )

    lidar_fusion = Node(
        package='preto_gazebo',
        executable='lidar_fusion_node',
        name='lidar_fusion_node',
        output='screen',
        parameters=[{
            'target_frame': 'base_link',
            'publish_scan': True,
        }]
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    diff_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
        lidar_fusion,
        TimerAction(
            period=10.0,
            actions=[joint_state_broadcaster_spawner]
        ),
        TimerAction(
            period=10.0,
            actions=[diff_drive_controller_spawner]
        ),
    ])