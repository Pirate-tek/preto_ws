# Preto Robot Simulation

**WEEK 1:** *Modeling preto's URDF and simulating in Gazebo Harmonic.*

---

## Robot Architecture
The **Preto Robot** is a 4-wheeled autonomous mobile platform featuring a robust 2-tier structural design.

*   **Chassis**: 2-tier structure (Base & Top plate) connected by precision support pillars.
*   **Dimensions**: `60cm x 50cm x 15cm`
*   **Drivetrain**: Differential drive system with 2 active wheels and 4 passive casters.
    *   **Wheel Radius**: `0.1m` (10cm)
    *   **Wheel Separation**: `0.56m` (56cm)
    *   **Wheel Width**: `0.06m` (6cm)
*   **Sensing**: Dual **360° LiDARs** strategically mounted at the **Front-Right** and **Back-Left** corners to ensure total sensor coverage and eliminate blind spots.

---

## Physics & Control
*   **DiffDrive Controller**: Integrated Gazebo plugin for high-fidelity, physics-based motion.
*   **Joint State Tracking**: Real-time kinematics publishing for precise internal system monitoring via the `JointStatePublisher`.

---

## LiDAR Fusion Pipeline
An advanced sensor processing system designed for robust obstacle detection and navigation:

-   **Temporal Alignment**: Uses `message_filters` to synchronize asynchronous laser scans from multiple sensors.
-   **Spatial Fusion**: Unifies separate `LaserScan` data into a single, high-density `PointCloud2` in the `base_link` frame.
-   **Virtual Scanner**: Built-in logic outputs a single, merged 360° `LaserScan` on the `/scan_combined` topic, ensuring 100% compatibility with the **Nav2** navigation stack.

---

## Quick Start

### 1. Build the workspace
```bash
colcon build --packages-select
source install/setup.bash
```

### 2. Launch Simulation
```bash
ros2 launch preto_gazebo gazebo.launch.py
```
### 3. Teleop Node
```bash
ros2 run preto_teleop teleop_node
```
---
