import sys, rclpy, cv2
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

rclpy.init()
node = Node('snap') #creates a node called "snap"
msg = []
node.create_subscription(Image, '/camera/image_raw', lambda m: msg.append(m), 1) #creates the subscriber
while not msg:
    rclpy.spin_once(node)
cv2.imwrite(sys.argv[1], CvBridge().imgmsg_to_cv2(msg[0], 'bgr8'))
print('saved', sys.argv[1])