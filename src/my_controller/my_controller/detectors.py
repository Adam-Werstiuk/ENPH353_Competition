# contains functions for detecting the crosswalk, the truck, and baby yoda 
import cv2
import rclpy
import time
import numpy as np
from cv_bridge import CvBridge


# Helper function
# using cv2.contourArea excludes stripes that are 1 pixel tall so we can't use that 
def pixel_area(c, shape):
    m = np.zeros(shape, np.uint8)
    cv2.drawContours(m, [c], -1, 255, thickness=cv2.FILLED)
    return cv2.countNonZero(m)


def isCrosswalkAhead(frame, thresholdLen=100, maxAspectRatio = 1/5, maxSlope = 10):  

    img = frame  # BGR numpy image (MyController.latest_frame is already converted)

    #convert to HSV for better colour processing
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  

    #since red wraps around the HSV scale, we need to define lower and upper bounds for red (two ranges):
    # Lower red range (0 to 10)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    # Upper red range (170 to 179)
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([179, 255, 255])

    # Create masks for both ranges and combine them
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) < 2:  # automatically skip if less than 2 strips detected
        return False

    # sort contours by num pixels, largest (closest) first
    contours = sorted(contours, key=lambda c: pixel_area(c, red_mask.shape), reverse=True)

    # keep only long thin strips 
    candidates = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w >= thresholdLen and h <= w * maxAspectRatio:
            candidates.append((c, (x, y, w, h)))

    # keep only the strips whose line of best fit is near-horizontal
    flatCandidates = []
    for c, rect in candidates:
        vx, vy, _, _ = cv2.fitLine(c, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
        angle = abs(np.degrees(np.arctan2(vy, vx)))
        angle = min(angle, 180 - angle)  # fitLine's direction vector can point either way
        if angle <= maxSlope:
            flatCandidates.append(rect)

    if len(flatCandidates) < 2:  # need two near-horizontal strips
        return False

    #unpack the rectangle values from flatCandidates, taking the two largest only: 
    xClose, yClose, wClose, hClose = flatCandidates[0] 
    xFar, yFar, wFar, hFar = flatCandidates[1] 

    # validate that this is the crosswalk: the larger (closer) strip should have Xmax >= Xmax of the further strip
    # and yMax > yMax of the further strip (closer = lower in the image = larger y)
    xMaxClose, xMaxFar, yMaxClose, yMaxFar = xClose + wClose, xFar + wFar, yClose + hClose, yFar + hFar

    if (xMaxClose >= xMaxFar and yMaxClose > yMaxFar):
        return True

    return False 











def pedestrian_in_crosswalk(frame):   # True/False
    return False 


def truck_in_view(frame):             # (found, left-right position, size)
    return (found, pos, size)

def yoda_in_view(frame):              # (found, left-right position, size)
    return (found, pos, size)