#!/usr/bin/env bash

OUTPUT_DIR="$(cd "$(dirname "$0")" && pwd)/photos"
mkdir -p "$OUTPUT_DIR"

# XYZ and angle
CLUEBOARD_COORDS=(
    "-5.160000 1.281170 0.040000 -3.017360"
    "-4.000000 1.670000 0.040000 1.636360"
    "-0.830000 0.219370 0.040000 0.020601"
)

ROBOTZ=0.1

i=0

for coords in "${CLUEBOARD_COORDS[@]}"; do

    # random int angle from -90 to 90
    ANGLE=$(( RANDOM % 181 - 90 ))
    OFFSET_X=$(awk -v r="$RANDOM" 'BEGIN { print 0.5 + 2.0 * r / 32768 }')
    OFFSET_Y=$(awk -v r="$RANDOM" 'BEGIN { print 0.5 + 2.0 * r / 32768 }')

    read -r BX BY BZ BYAW <<< "$board"

    DIST=$(awk -v r="$RANDOM" 'BEGIN { print 0.5 + 2.0 * r / 32768 }')
    VIEW=$(( RANDOM % 91 - 45 ))     # -45 to 45 degrees

    read -r ROBOTX ROBOTY ROBOTYAW <<< "$(awk \
        -v bx="$BX" -v by="$BY" -v byaw="$BYAW" -v d="$DIST" -v v="$VIEW" '
        BEGIN {
            pi  = 3.14159265358979
            phi = (byaw + v) * pi / 180
            printf "%.4f %.4f %.1f", bx + d * cos(phi), by + d * sin(phi), byaw + v + 180
        }')"

    ./teleport.sh "$ROBOTX" "$ROBOTY" "$ANGLE" "$ROBOTZ"

    sleep 0.5

    python3 take_photo.py "$OUTPUT_DIR/photo${i}.png"

    i=$((i + 1))

done