# THINGS TO CLARIFY FOR LOGBOOK
#   1. Setup stuff
#       - The command that makes a ROS2 package (the one we did for my_controller),
#         what are the arguments used? How does that work?
#       - The thing I added to the setup.py in the package, the 'entry point,' what is
#         that?
#   2. Controller content
#       - Explain the command that runs this controller. What does it mean to run this?
#         Are the other packages not also being run? What's the difference?
#       - These dependencies that I created the package with, what is a dependency and
#         what is rclpy and why do I have to import nodes and twist? I know it has to do with
#         the topics this program is subscribed and publishing to, but specify exactly what
#         the imports are.
#       - Why does the controller class take a Node argument? Is that what's going on, or
#         is it something else?
#       - Do all controller classes need an __init__(self) function? What would you call this?
#         What does it do? And what is that super().__init__('my_controller') doing?
#       - What is the 1 at the end of the self.create_publisher doing?
#       - What stuff needs a self. and what doesn't? I believe I see that all variables
#         attached to the my_controller object have self., but why does self.create_publisher
#         need one, and any of the other functions used?
#       - What does t_mark do/represent?
#       - Is Twist a datatype? Is it specific to ROS2?
#       - What are clocks? Does every node get a clock? Does it take information from
#         Gazebo? How accurate is it?
#       - Explain create_timer(0.1, self.tick). What does that mean/do?
#       - What does the elapsed function do? How does any of that stuff work? Is it finding
#         the difference between the node creation time and the current time? What is .nanosecond
#         doing then? Why rescale to 1*e-9? Wouldn't that just make computing harder?
#       - Why do we need to pass self as a parameter for elapsed and send_score? Can
#         we not access self.score_pub without it? Is 'plate' a variables that represents
#         which clue board we're looking at, and 'guess' is what we think the text is?
#       - Why send a pointless guess at the beginning? Is that just a test to see if it works?
#         And why do we not pass something into the self parameter?
#       - Explain logic of tick function and all of main (including why need args=)
#   3. Else
#       - Do I need to rebuild every time I make changes to anything? When do I rebuild? 
#       - Can I make aliases to speed things up? Where do they go?

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

TEAM = 'AandA'
PASSWORD = 'password'

class MyController(Node):
    def __init__(self):
        super().__init__('my_controller')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 1)
        self.score_pub = self.create_publisher(String, '/score_tracker', 1)
        self.t0 = self.get_clock().now()
        self.state = 'WAIT'
        self.t_mark = 0.0
        self.timer = self.create_timer(0.1, self.tick)

    def elapsed(self):
        return (self.get_clock().now() - self.t0).nanoseconds * 1e-9

    def send_score(self, plate, guess):
        msg = String()
        msg.data = f'{TEAM}, {PASSWORD}, {plate}, {guess}'
        self.score_pub.publish(msg)

    # TODO: IMPLEMENT
    def take_photo(self):
        return 0

    # TODO: Implement
    def teleport(self, x_location, y_location, angle):
        return 0
    
    def tick(self):
        t = self.elapsed()
        if self.state == 'WAIT' and t > 1.0:
            self.send_score(0, 'NA')
            self.state = 'DRIVE'
            self.t_mark = t
        elif self.state == 'DRIVE':
            cmd = Twist()
            cmd.linear.x = 0.5
            self.cmd_pub.publish(cmd)
            if t - self.t_mark > 4.0:
                self.state = 'STOP'
                self.t_mark = t
        elif self.state == 'STOP':
            self.cmd_pub.publish(Twist())
            if t - self.t_mark > 1.0:
                self.send_score(-1, 'NA')
                self.state = 'DONE'
                self.timer.cancel()

def main(args=None):
    rclpy.init(args=args)
    node = MyController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()