import cv2
import numpy as np


class PID:
    def __init__(self, kp, ki, kd, i_limit=1.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.i_limit = i_limit
        self.integral = 0.0
        self.prev_error = None
        self.prev_t = None

    def reset(self):
        self.integral = 0.0
        self.prev_error = None
        self.prev_t = None

    def update(self, error, t):
        dt = 0.0
        if self.prev_t is not None:
            dt = t - self.prev_t
        if dt > 1.0:          # a big jump in time (restart or pause), ignore it
            dt = 0.0

        derivative = 0.0
        if dt > 0:
            self.integral += error * dt
            self.integral = max(-self.i_limit, min(self.i_limit, self.integral))
            derivative = (error - self.prev_error) / dt

        self.prev_error = error
        self.prev_t = t
        return self.kp * error + self.ki * self.integral + self.kd * derivative


class LaneFollower:
    def __init__(self):
        # Asphalt in HSV: any hue, low saturation, dark (a first guess, tune it)
        self.lower = np.array([0, 0, 30])
        self.upper = np.array([179, 60, 110])

        # Image rows to look at, as fractions of the image height
        self.near_band = (0.85, 0.95)   # right in front of the robot
        self.far_band = (0.80, 0.85)    # a bit further ahead
        self.min_pixels = 200           # fewer road pixels than this = no road seen

        # Steering PID (the error is normalized to -1..1)
        self.pid = PID(kp=2, ki=0.0, kd=0.3)

        # Speed limits (m/s) and turn limit (rad/s), guesses
        self.max_speed = 0.7
        self.min_speed = 0.15
        self.max_turn = 4.0

        self.last_angular = 0.0

    def road_mask(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        return mask

    def band_error(self, mask, top_frac, bottom_frac):
        """Where the road is in one band: -1 (far left) to +1 (far right), or None if no road."""
        h, w = mask.shape
        band = mask[int(top_frac * h):int(bottom_frac * h), :]
        m = cv2.moments(band, binaryImage=True)
        if m['m00'] < self.min_pixels:
            return None
        cx = m['m10'] / m['m00']
        return (cx - w / 2) / (w / 2)

    def step(self, frame, t):
        """frame: BGR image, t: time in seconds. Returns (linear_x, angular_z, debug_image)."""
        mask = self.road_mask(frame)
        near_err = self.band_error(mask, *self.near_band)
        far_err = self.band_error(mask, *self.far_band)

        # Combine the two bands, or use whichever one we have
        if near_err is None and far_err is None:
            debug = self.draw_debug(frame, mask, None, self.last_angular)
            return self.min_speed, self.last_angular, debug
        if near_err is None:
            error = far_err
        elif far_err is None:
            error = near_err
        else:
            error = 0.6 * near_err + 0.4 * far_err

        # Road to the right (positive error) means turn right, which is negative angular.z in ROS
        angular = -self.pid.update(error, t)
        angular = max(-self.max_turn, min(self.max_turn, angular))

        # Slow down in bigger turns
        linear = self.max_speed * (1.0 - 0.6 * min(abs(error), 1.0))
        linear = max(self.min_speed, linear)

        self.last_angular = angular
        debug = self.draw_debug(frame, mask, error, angular)
        return linear, angular, debug

    def draw_debug(self, frame, mask, error, angular):
        h, w = mask.shape
        out = frame.copy()
        out[mask > 0] = (0.5 * out[mask > 0] + 0.5 * np.array([0, 255, 0])).astype(np.uint8)
        for top, bottom in (self.near_band, self.far_band):
            cv2.line(out, (0, int(top * h)), (w, int(top * h)), (255, 255, 0), 1)
            cv2.line(out, (0, int(bottom * h)), (w, int(bottom * h)), (255, 255, 0), 1)
        cv2.line(out, (w // 2, 0), (w // 2, h), (0, 0, 255), 1)
        text = 'no road' if error is None else f'err {error:+.2f}  ang {angular:+.2f}'
        cv2.putText(out, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return out