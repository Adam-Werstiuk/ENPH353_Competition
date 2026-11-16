#!/usr/bin/env bash

#user-input variables in order: eg. when running the script, you would type:
# ./teleport.sh x_coord y_coord yaw_angle_deg 
#note: bash doesn't like spaces around the '='
X=$1
Y=$2
YAW=$3 
Z="${4:-0.1}" 

#convert angle to the correct value for the simulation 
QZ=$(awk -v yaw="$YAW" 'BEGIN {print sin(yaw * 3.14159265 / 360)}')
QW=$(awk -v yaw="$YAW" 'BEGIN {print cos(yaw * 3.14159265 / 360)}')

# Stop the wheels first so the robot doesn't keep driving after the jump
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" >/dev/null 2>&1 || true

#teleport the robot 
gz service -s /world/fast_world/set_pose \
 --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
 --req "name: \"my_robot\", position: {x: $X, y: $Y, z: $Z}, orientation: {x: 0, y: 0, z: $QZ, w: $QW}"