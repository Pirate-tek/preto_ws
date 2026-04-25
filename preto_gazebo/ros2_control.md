# Upgrading to ros2_control procedure:

This guide provides a standardized procedure for replacing legacy Gazebo Diff Drive plugins with the **`ros2_control`** framework.

---

## Prerequisites
Ensure the following packages are installed:
```bash
sudo apt install ros-${ROS_DISTRO}-ros2-control \
                 ros-${ROS_DISTRO}-ros2-controllers \
                 ros-${ROS_DISTRO}-gz-ros2-control
```

---

## Step 1: Update the URDF
Replace the standalone Gazebo plugin with the `ros2_control` hardware abstraction.

### 1.1 Define Hardware Interfaces
Add a `<ros2_control>` block to your URDF. This defines how ROS 2 sees the motors and sensors.
```xml
<ros2_control name="GazeboSystem" type="system">
    <hardware>
        <plugin>gz_ros2_control/GazeboSimSystem</plugin>
    </hardware>
    <joint name="left_wheel_joint">
        <command_interface name="velocity"/>
        <state_interface name="position"/>
        <state_interface name="velocity"/>
    </joint>
    <joint name="right_wheel_joint">
        <command_interface name="velocity"/>
        <state_interface name="position"/>
        <state_interface name="velocity"/>
    </joint>
</ros2_control>
```

### 1.2 Add the Gazebo Controller Plugin
In your `<gazebo>` block, remove the old diff-drive plugin and add the `gz_ros2_control` plugin.
```xml
<gazebo>
    <plugin filename="gz_ros2_control-system" name="gz_ros2_control::GazeboSimROS2ControlPlugin">
        <parameters>$(find your_package)/config/controllers.yaml</parameters>
    </plugin>
</gazebo>
```
> [!IMPORTANT]
> Since standard URDF files often don't resolve `$(find ...)` at runtime, you may need to replace this path with a placeholder in the file and perform a string replacement in your Python launch file.

---

## Step 2: Create the Controller Configuration
Create a `config/controllers.yaml` file to define your controllers and their parameters.

```yaml
controller_manager:
  ros__parameters:
    update_rate: 100
    use_sim_time: True

    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

diff_drive_controller:
  ros__parameters:
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.5
    wheel_radius: 0.1
    odom_frame_id: odom
    base_frame_id: base_footprint
    publish_rate: 50.0
    use_stamped_vel: false
```

---

## Step 3: Update the Launch File
You must now "spawn" the controllers after Gazebo has loaded the robot.

### 3.1 Define Spawner Nodes
```python
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
```

### 3.2 Add Timer Delays
Controllers often fail to load if they start before Gazebo is ready. Use `TimerAction` to add a small delay (e.g., 5-10 seconds).
```python
from launch.actions import TimerAction

# ... in your LaunchDescription
TimerAction(
    period=5.0,
    actions=[joint_state_broadcaster_spawner]
),
TimerAction(
    period=5.0,
    actions=[diff_drive_controller_spawner]
)
```

---

## Step 4: Topic Remapping (Optional)
If your controllers publish to namespaced topics like `/diff_drive_controller/odom` and you want them to be global (e.g., `/odom`), add a `<ros>` block to the Gazebo plugin in your **URDF**:

```xml
<plugin filename="gz_ros2_control-system" name="gz_ros2_control::GazeboSimROS2ControlPlugin">
    <parameters>...</parameters>
    <ros>
        <remapping>/diff_drive_controller/cmd_vel_unstamped:=/cmd_vel</remapping>
        <remapping>/diff_drive_controller/odom:=/odom</remapping>
    </ros>
</plugin>
```

---

## Summary of Benefits
*   **Modular Architecture**: High-level logic is decoupled from hardware.
*   **Real-Time Ready**: `ros2_control` is designed for high-performance, real-time loops.
*   **Uniform API**: Use the same ROS 2 commands to control a simulated robot as you would a real one.
