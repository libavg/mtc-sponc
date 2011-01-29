# omgz no license!

import math
from libavg import Point2D


#resolution = Point2D(400, 300)
#resolution = Point2D(800, 600)
#resolution = Point2D(1024, 768)
#resolution = Point2D(1920, 1080)
resolution = Point2D(1280, 800)

SPACING = Point2D(0,resolution.y / 25) # leave x=0, not implemented!
BASE_BALL_SPEED = 10 * (resolution.x / 1280) # TODO: fix weird speed for some resolutions
STATE_FADE_TIME = 800
MAX_BAT_LENGTH = resolution.y/2 - SPACING.y
FINGER_ROT_SPEED = -math.pi
TIME_BETWEEN_BALLS = 800
MAX_SCORE = 5
BALL_SIZE = BATPOINT_SIZE = Point2D(50,50) * (resolution.x/1280)
