#!/usr/bin/env bash

OUTPUT_DIR="$(cd "$(dirname "$0")" && pwd)/photos/run2photos/"
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
    S=$(awk -v r="$RANDOM" 'BEGIN { print -0.3 + 0.3 * r / 32768 }') #sideways offset
    ANGLEOFFSET=$(awk -v r="$RANDOM" 'BEGIN { print -0.15 + 0.3 * r / 32768 }') #facing angle offset (rad)

    read -r SIGNX SIGNY SIGNZ SIGNANGLE <<< "$coords"

    # hardcoded offsets for signs whose random placement is obstructed or out of bounds
    # (D = distance in front of sign, S = sideways offset, ANGLEOFFSET = yaw offset in rad)
    XLO=$XMIN; XHI=$XMAX; YLO=$YMIN; YHI=$YMAX; AIM=0
    case "$i" in
        1) # CRIME: fir_07 (-5,0.9) nearly touches the sign when its y is low, so the safe area depends on
           # the sign's current y (SIGNY). Low y: thin strip west of the tree. y >= 1.3: much more room.
           # Safe ranges were checked against the trees for the sign's full +/-0.15 rad pitch.
           read -r DLO DHI SLO SHI <<< "$(awk -v y="$SIGNY" 'BEGIN {
               if (y < 1.25)      print 0.4, 0.55, 0.20, 0.25
               else if (y < 1.3)  print 0.4, 0.60, 0.20, 0.25
               else { dh = 0.7 + (y - 1.3); if (dh > 1.0) dh = 1.0; print 0.4, dh, -0.6, 0.25 }
           }')"
           D=$(awk -v r="$RANDOM" -v lo="$DLO" -v hi="$DHI" 'BEGIN { print lo + (hi - lo) * r / 32768 }')
           S=$(awk -v r="$RANDOM" -v lo="$SLO" -v hi="$SHI" 'BEGIN { print lo + (hi - lo) * r / 32768 }')
           ANGLEOFFSET=$(awk -v r="$RANDOM" -v d="$D" -v s="$S" 'BEGIN { print -atan2(s, d) - 0.08 + 0.16 * r / 32768 }') ;;
        3) # WEAPON: fir_06 (-5,1.8) / fir_07 (-5,0.9) are west of the sign, so keep the robot close
           # (D <= 0.6) with S in [-0.5, 0.45]; aimed at the sign.
           D=$(awk -v r="$RANDOM" 'BEGIN { print 0.4 + 0.2 * r / 32768 }')
           S=$(awk -v r="$RANDOM" 'BEGIN { print -0.5 + 0.95 * r / 32768 }')
           AIM=1 ;;
        5) # TIME: the road is a narrow causeway (y in [-1.58,-1.22]) through the pit, and the sign sits just
           # south of it facing -x. Robot is clamped to y in [-1.52,-1.28] and x in [1.0, 2.95].
           D=$(awk -v r="$RANDOM" 'BEGIN { print 0.5 + 0.8 * r / 32768 }')
           S=$(awk -v r="$RANDOM" 'BEGIN { print 0.1 + 0.4 * r / 32768 }')
           YLO=-1.52; YHI=-1.28; XLO=1.0; XHI=2.95
           AIM=1 ;;
    esac

    #read the randomly-generated clue texts 
    # row i+1 of clues.csv is the clue on sign_i. tr removes the Windows-style line ending and turns the comma into an underscore
    CLUE=$(sed -n "$((i + 1))p" "$CLUES_CSV" | tr -d '\r' | tr ',' '_')

    read -r DELTAX DELTAY ROBOTX ROBOTY ROBOTANGLERAD ROBOTANGLEDEG ROBOTZ <<< "$(awk \
        -v sx="$SIGNX" -v sy="$SIGNY" -v sz="$SIGNZ" -v a="$SIGNANGLE" -v d="$D" -v s="$S" -v h="$SIGN_HEIGHT" \
        -v xmin="$XLO" -v xmax="$XHI" -v ymin="$YLO" -v ymax="$YHI" -v off="$ANGLEOFFSET" -v aim="$AIM" -v jit="$RANDOM" '
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
            # aim directly at the sign (+/- 0.08 rad) from the final, clamped position
            if (aim == 1) rad = atan2(sy - y, sx - x) - 0.08 + 0.16 * jit / 32768
            print dx, dy, x, y, rad, rad * 180 / pi, sz - h
        }')"

    echo "sign: $SIGNX $SIGNY $SIGNZ $SIGNANGLE -> robot: $ROBOTX $ROBOTY $ROBOTZ $ROBOTANGLEDEG"
    ./teleport.sh "$ROBOTX" "$ROBOTY" "$ROBOTANGLEDEG" "$ROBOTZ"

    sleep 1.0

    python3 take_photo.py "$OUTPUT_DIR/${CLUE}.png"  #saves the labelled photo 

    i=$((i + 1))

done