#!/usr/bin/env bash

#!/usr/bin/env bash

# usage: ./mass_photo_collection.sh [number_of_launches]
NUM_RUNS="${1:-5}"

cd "$(dirname "$0")"

# stop everything the launch started
cleanup() {
    kill -TERM -- -"$SIM_PID" 2>/dev/null
    pkill -f "gz sim" 2>/dev/null
    pkill -f ros_gz_bridge 2>/dev/null
    pkill -9 -f score_tracker 2>/dev/null
    sleep 5
}
trap cleanup EXIT    # also stops the sim if you press Ctrl+C

for run in $(seq 1 "$NUM_RUNS"); do

    echo "=== launch $run of $NUM_RUNS ==="

    # start the sim in its own process group so cleanup can kill all of it
    #setsid ros2 launch my_robot_bringup my_robot.launch.py > "sim_run${run}.log" 2>&1 & # this line would save a sim log file 
    setsid ros2 launch my_robot_bringup my_robot.launch.py > /dev/null 2>&1 &
    SIM_PID=$!

    # wait (up to 90 s) until the robot and all 8 signs exist
    for t in $(seq 1 90); do
        COUNT=$(gz model --list 2>/dev/null | grep -c -E "sign_[0-7]|my_robot")
        [ "$COUNT" -ge 9 ] && break
        sleep 1
    done

    if [ "$COUNT" -lt 9 ]; then
        echo "sim didn't finish starting, skipping launch $run (see sim_run${run}.log)"
        cleanup
        continue
    fi

    sleep 5     # let everything settle on the ground

    ./collect_photos.sh

    cleanup

done