# contains functions for detecting the crosswalk, the truck, and baby yoda 
import cv2
import rclpy
import time
import numpy as np
from cv_bridge import CvBridge


def crosswalk_ahead(frame):           # how close the lines are

    # from Lab 7's linefollower_env.py: 
    cv_image = CvBridge().imgmsg_to_cv2(frame, desired_encoding='bgr8')
    cv2.imshow("Camera Feed", cv_image)
    cv2.waitKey(1)

    #get the dimensions of the image 
    im_height, im_width, _ = cv_image.shape 
    # Convert BGR to grayscale. 'grayFrame' is a new copy of the original frame, so the information about the original colours are preserved in 'frame'
    grayFrame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to make the white parts 'pop' --> use THRESH_BINARY_INV so pixels ABOVE threshold become black (0). Need to test on actual data!
    _, thresh = cv2.threshold(grayFrame, 60, 255, cv2.THRESH_BINARY_INV)



    return False 

def pedestrian_in_crosswalk(frame):   # True/False
    return False 


def truck_in_view(frame):             # (found, left-right position, size)
    return (found, pos, size)

def yoda_in_view(frame):              # (found, left-right position, size)
    return (found, pos, size)