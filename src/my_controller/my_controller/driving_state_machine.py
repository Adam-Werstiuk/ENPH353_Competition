# Driving state machine: decides what the robot is doing (following the road, stopping at the
# crosswalk, ...) and returns the (linear, angular) command for each camera frame.

from enum import Enum, auto

from .lane_follower import LaneFollower


class State(Enum):
    WAIT = auto()             # before the start signal
    LANE_FOLLOW = auto()      # normal driving on the road
    CROSSWALK_STOP = auto()   # stopped at the crosswalk, waiting for the pedestrian to clear
    CROSSWALK_CROSS = auto()  # driving straight across the crosswalk
    DONE = auto()


class DrivingStateMachine:

    def __init__(self, crosswalk_detector=None, pedestrian_detector=None, nHits=5):
        # detectors are passed in as functions of one frame -> bool, so they are easy to swap or fake
        self.follower = LaneFollower()
        self.crosswalk_ahead = crosswalk_detector or (lambda frame: False)
        self.pedestrian_in_crosswalk = pedestrian_detector or (lambda frame: False)

        self.nHits = nHits          # consecutive crosswalk detections required before stopping
        self.crosswalk_hits = 0     # how many detections in a row we have seen so far

        self.state = State.WAIT
        self.t_mark = 0.0   # time the current state was entered

    def _go(self, new_state, t):
        print(f"[state] {self.state.name} -> {new_state.name} at t={t:.2f}s")
        self.state = new_state
        self.t_mark = t

    def step(self, frame, t):
        """Returns (linear, angular) for this frame. t = elapsed seconds."""

        if self.state == State.WAIT:
            self._go(State.LANE_FOLLOW, t)   # TODO: only leave WAIT after the start/score message
            return 0.0, 0.0

        if self.state == State.LANE_FOLLOW:
            # remember previous outputs: count consecutive True results, reset on any False
            if self.crosswalk_ahead(frame):
                self.crosswalk_hits += 1
            else:
                self.crosswalk_hits = 0

            if self.crosswalk_hits >= self.nHits:
                self.crosswalk_hits = 0   # start fresh for the next time we are in LANE_FOLLOW
                self._go(State.CROSSWALK_STOP, t)
                return 0.0, 0.0
            linear, angular, _debug = self.follower.step(frame, t)
            return linear, angular

        if self.state == State.CROSSWALK_STOP:
            # TODO: tune; wait until the pedestrian has left the crosswalk
            if not self.pedestrian_in_crosswalk(frame) and t - self.t_mark > 1.0:
                self._go(State.CROSSWALK_CROSS, t)
            return 0.0, 0.0

        if self.state == State.CROSSWALK_CROSS:
            # TODO: tune the speed and duration to the crosswalk length
            if t - self.t_mark > 2.0:
                self._go(State.LANE_FOLLOW, t)
            return 0.5, 0.0

        return 0.0, 0.0   # DONE
