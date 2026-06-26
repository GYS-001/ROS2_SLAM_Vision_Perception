import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Gazebo 仿真世界（turtlebot3_world，有墙那个）
    turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo, 'launch', 'turtlebot3_world.launch.py')
        )
    )

    # SLAM（slam_toolbox）
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('slam_toolbox'),
                         'launch', 'online_async_launch.py')
        )
    )

    # 视觉检测节点
    detector = Node(
        package='vision_detector',
        executable='vision_detector',
        name='vision_detector'
    )

    # rviz2（手动启动也行，但这里自动开）
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2'
    )

    return LaunchDescription([
        gazebo,
        # SLAM 晚 5 秒启动，等 Gazebo 就绪
        TimerAction(period=5.0, actions=[slam]),
        # 视觉节点晚 8 秒启动
        TimerAction(period=8.0, actions=[detector]),
        # RViz 晚 10 秒启动
        TimerAction(period=10.0, actions=[rviz]),
    ])
