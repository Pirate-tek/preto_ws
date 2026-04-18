import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, PointCloud2
from laser_geometry import LaserProjection
import message_filters
import sensor_msgs_py.point_cloud2 as pc2
from tf2_ros import Buffer, TransformListener
from tf2_sensor_msgs.tf2_sensor_msgs import do_transform_cloud
import rclpy.duration
import numpy as np
import math

class LidarFusionNode(Node):
    def __init__(self):
        super().__init__('lidar_fusion_node')
        
        # Initialize projector and TF
        self.projector = LaserProjection()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Parameters
        self.target_frame = self.declare_parameter('target_frame', 'base_link').value
        self.tolerance = self.declare_parameter('tolerance', 0.1).value 
        self.pub_scan = self.declare_parameter('publish_scan', True).value
        
        # Scan parameters for merged output
        self.scan_min_angle = self.declare_parameter('scan_min_angle', -math.pi).value
        self.scan_max_angle = self.declare_parameter('scan_max_angle', math.pi).value
        self.scan_angle_increment = self.declare_parameter('scan_angle_increment', math.radians(1.0)).value
        self.scan_range_min = self.declare_parameter('scan_range_min', 0.15).value
        self.scan_range_max = self.declare_parameter('scan_range_max', 25.0).value
        
        # Subscriptions
        self.scan_front_sub = message_filters.Subscriber(self, LaserScan, '/scan_front')
        self.scan_rear_sub = message_filters.Subscriber(self, LaserScan, '/scan_rear')
        
        # Temporal Synchronization
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.scan_front_sub, self.scan_rear_sub], 
            queue_size=10, 
            slop=self.tolerance
        )
        self.ts.registerCallback(self.sync_callback)
        
        # Publishers
        self.pc_pub = self.create_publisher(PointCloud2, '/merged_cloud', 10)
        if self.pub_scan:
            self.scan_pub = self.create_publisher(LaserScan, '/scan_combined', 10)
        
        self.get_logger().info(f'Lidar Fusion Node initialized. Merging to frame: {self.target_frame}')

    def sync_callback(self, scan_front, scan_rear):
        try:
            # 1. Project scans to PointCloud2 in their local frames
            cloud_front_local = self.projector.projectLaser(scan_front)
            cloud_rear_local = self.projector.projectLaser(scan_rear)
            
            # 2. Lookup transforms to target frame
            target_time = rclpy.time.Time() # Use latest available to avoid sync issues with Gazebo time
            
            trans_front = self.tf_buffer.lookup_transform(
                self.target_frame, 
                cloud_front_local.header.frame_id, 
                target_time, 
                rclpy.duration.Duration(seconds=0.1)
            )
            trans_rear = self.tf_buffer.lookup_transform(
                self.target_frame, 
                cloud_rear_local.header.frame_id, 
                target_time, 
                rclpy.duration.Duration(seconds=0.1)
            )
            
            # 3. Transform clouds
            cloud_front_base = do_transform_cloud(cloud_front_local, trans_front)
            cloud_rear_base = do_transform_cloud(cloud_rear_local, trans_rear)
            
            # 4. Concatenate points
            points_front = list(pc2.read_points(cloud_front_base, field_names=("x", "y", "z"), skip_nans=True))
            points_rear = list(pc2.read_points(cloud_rear_base, field_names=("x", "y", "z"), skip_nans=True))
            merged_points = points_front + points_rear
            
            # 5. Create and publish merged PointCloud2
            merged_pc = pc2.create_cloud_xyz32(cloud_front_base.header, merged_points)
            merged_pc.header.frame_id = self.target_frame
            self.pc_pub.publish(merged_pc)
            
            # 6. Optionally convert back to LaserScan
            if self.pub_scan:
                self.publish_combined_scan(merged_points, cloud_front_base.header)
                
        except Exception as e:
            self.get_logger().error(f'Could not fuse scans: {str(e)}')

    def publish_combined_scan(self, points, header):
        num_bins = int((self.scan_max_angle - self.scan_min_angle) / self.scan_angle_increment)
        ranges = [float('inf')] * num_bins
        
        for p in points:
            x, y, z = p[0], p[1], p[2]
            # Ignore points too high or too low (optional filtering)
            if abs(z) > 0.1: continue 
            
            dist = math.sqrt(x*x + y*y)
            if dist < self.scan_range_min or dist > self.scan_range_max:
                continue
                
            angle = math.atan2(y, x)
            if angle < self.scan_min_angle or angle > self.scan_max_angle:
                continue
                
            bin_idx = int((angle - self.scan_min_angle) / self.scan_angle_increment)
            if 0 <= bin_idx < num_bins:
                if dist < ranges[bin_idx]:
                    ranges[bin_idx] = dist
        
        # Create LaserScan message
        scan = LaserScan()
        scan.header = header
        scan.header.frame_id = self.target_frame
        scan.angle_min = self.scan_min_angle
        scan.angle_max = self.scan_max_angle
        scan.angle_increment = self.scan_angle_increment
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = self.scan_range_min
        scan.range_max = self.scan_range_max
        scan.ranges = [r if r != float('inf') else 0.0 for r in ranges]
        
        self.scan_pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = LidarFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
