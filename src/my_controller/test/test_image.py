import sys, rclpy, cv2
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge #converts between ROS and NumPy for image formats

rclpy.init() #starts ROS in this program 
node = Node('snap') #creates a node called "snap"
msg = [] #creates an empty "mailbox" to wait for the image
node.create_subscription(Image, '/camera/image_raw', lambda m: msg.append(m), 1) 
#creates the subscriber. The subscriber listens to the image_raw topic, and then runs the 
#inline lambda function to append the incoming message "m" to the "msg" list, and the 1 
# makes it so that at most one image is appended 
while not msg:
    rclpy.spin_once(node) #waits for an image while the mailbox msg is empty 
cv2.imwrite(sys.argv[1], CvBridge().imgmsg_to_cv2(msg[0], 'bgr8'))
print('saved', sys.argv[1])

rclpy.shutdown()