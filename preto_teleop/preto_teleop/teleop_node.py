import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import select
import termios
import tty

# Instructions for the user
msg = """
---------------------------
Control Your Preto Robot!
---------------------------
Moving around:
        w
   a    s    d
        x

w/x : increase/decrease linear velocity (x)
a/d : increase/decrease angular velocity (z)

space key, s : force stop

CTRL-C to quit
"""

moveBindings = {
    'w': (1, 0, 0, 0),
    's': (0, 0, 0, 0),
    'a': (0, 0, 0, 1),
    'd': (0, 0, 0, -1),
    'x': (-1, 0, 0, 0),
}

class PretoTeleop(Node):
    def __init__(self):
        super().__init__('preto_teleop')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        
        self.declare_parameter('speed', 0.5)
        self.declare_parameter('turn', 1.0)
        
        self.speed = self.get_parameter('speed').value
        self.turn = self.get_parameter('turn').value
        
        self.settings = termios.tcgetattr(sys.stdin)
        self.get_logger().info("Preto Teleop Node Started")

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        print(msg)
        target_linear_vel = 0.0
        target_angular_vel = 0.0
        
        try:
            while True:
                key = self.get_key()
                if key in moveBindings.keys():
                    target_linear_vel = moveBindings[key][0] * self.speed
                    target_angular_vel = moveBindings[key][3] * self.turn
                elif key == ' ':
                    target_linear_vel = 0.0
                    target_angular_vel = 0.0
                elif key == '\x03': # CTRL-C
                    break
                else:
                    target_linear_vel = 0.0
                    target_angular_vel = 0.0
                
                twist = Twist()
                twist.linear.x = float(target_linear_vel)
                twist.angular.z = float(target_angular_vel)
                self.publisher_.publish(twist)
                
        except Exception as e:
            print(e)
            
        finally:
            twist = Twist()
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.publisher_.publish(twist)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

def main(args=None):
    rclpy.init(args=args)
    node = PretoTeleop()
    node.run()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
