#!/usr/bin/env bash

OUTPUT_DIR="$(cd "$(dirname "$0")" && pwd)/photos"
mkdir -p "$OUTPUT_DIR"

# read the current clueboard coordinates and store in CLUEBOARD_COORDS: XYZ and angle
CLUEBOARD_COORDS=()
for i in 0 1 2 3 4 5 6 7; do
    CLUEBOARD_COORDS+=("$(gz model -m sign_$i --pose | tr -d '[]' | awk '/^[[:space:]]*-?[0-9]/ { a[n++] = $0 } END { split(a[0], p, " "); split(a[1], r, " "); print p[1], p[2], p[3], r[3] }')")
done

#link to the clueboard csv 
CLUES_CSV="$HOME/ENPH353_Competition/src/2026_competition/src/world_pkg/world/clues.csv"


HEIGHT_OFFSET=0.06 #since signs are 0.03m above the ground and the robot should spawn at 0.1m off the ground.
# arena bounds (walls)
XMIN=-5.7
XMAX=5.7
YMIN=-2.5
YMAX=2.5

# if the sign has angle pi, the robot must face 90. x can be anything in the bounding box, and robot y < sign y
# if the sign has angle +pi/2, the robot faces 0. robot x < sign x, and y can be anything. 
# if the sign has angle -pi/2, the robot faces 180deg. robot x > sign x, and y can be anything   
# so robot facing angle = sign angle - 90deg. 

i=0

for coords in "${CLUEBOARD_COORDS[@]}"; do

    D=$(awk -v r="$RANDOM" 'BEGIN { print 0.5 + 1.0 * r / 32768 }') #vertical (facing) offset 
    S=$(awk -v r="$RANDOM" 'BEGIN { print -0.5 + 0.5 * r / 32768 }') #sideways offset
    ANGLEOFFSET=$(awk -v r="$RANDOM" 'BEGIN { print -0.15 + 0.3 * r / 32768 }') #facing angle offset (rad)

    #read the randomly-generated clue texts 
    # row i+1 of clues.csv is the clue on sign_i. tr removes the Windows-style line ending and turns the comma into an underscore
    CLUE=$(sed -n "$((i + 1))p" "$CLUES_CSV" | tr -d '\r' | tr ',' '_')

    read -r SIGNX SIGNY SIGNZ SIGNANGLE <<< "$coords"

    # use the normal bounds, except for specific signs
    XLO=$XMIN
    if [ "$i" -eq 5 ]; then XLO=3; fi   # 6th sign (index 5): robot x can't be less than 3 bc of the pit

    read -r DELTAX DELTAY ROBOTX ROBOTY ROBOTANGLERAD ROBOTANGLEDEG ROBOTZ <<< "$(awk \
        -v sx="$SIGNX" -v sy="$SIGNY" -v sz="$SIGNZ" -v a="$SIGNANGLE" -v d="$D" -v s="$S" -v h="$SIGN_HEIGHT" \
        -v xmin="$XLO" -v xmax="$XMAX" -v ymin="$YMIN" -v ymax="$YMAX" -v off="$ANGLEOFFSET" '
        BEGIN {
            pi = atan2(0, -1)
            dx = s * cos(a) - d * sin(a)
            dy = s * sin(a) + d * cos(a)
            x = sx + dx
            y = sy + dy
            # if the robot is out of bounds, put it on the boundary instead
            if (x < xmin) x = xmin
            if (x > xmax) x = xmax
            if (y < ymin) y = ymin
            if (y > ymax) y = ymax
            rad = a - pi / 2 + off
            print dx, dy, x, y, rad, rad * 180 / pi, sz - h
        }')"

    echo "sign: $SIGNX $SIGNY $SIGNZ $SIGNANGLE -> robot: $ROBOTX $ROBOTY $ROBOTZ $ROBOTANGLEDEG"
    ./teleport.sh "$ROBOTX" "$ROBOTY" "$ROBOTANGLEDEG" "$ROBOTZ"

    sleep 1.0

    python3 take_photo.py "$OUTPUT_DIR/${CLUE}.png"  #saves the labelled photo 

    i=$((i + 1))

done