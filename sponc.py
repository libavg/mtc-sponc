#!/usr/bin/python

# Copyright (C) 2007
#    Martin Heistermann, <mh at lulzmeister dot de>
#    Tim Grocki, <drogenkonsument at gmail dot com>
#
# This file is part of sponc.
#
# sponc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# sponc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sponc.  If not, see <http://www.gnu.org/licenses/>.

from libavg import avg

import Game
from config import *

global game

def main():
    def myinit():
        Tracker.setDebugImages(True, True)
        game = Game.Game(avgPlayer.getElementByID("main"))
        game.enter()

    def showTrackerImage():
        Bitmap = Tracker.getImage(avg.IMG_FINGERS)
        Node = avgPlayer.getElementByID("fingers")
        Node.setBitmap(Bitmap)
        Node.width=1280
        Node.height=800
        Grid = Node.getOrigVertexCoords()
        Grid = [ [ (pos[0], 1-pos[1]) for pos in line ] for line in Grid]
        Node.setWarpedVertexCoords(Grid)
    avgPlayer = avg.Player()
    Log = avg.Logger.get()
    Log.setCategories(
            Log.APP |
            Log.WARNING |
            Log.ERROR |
            Log.PROFILE |
    #       Log.PROFILE_LATEFRAMES |
            Log.CONFIG  |
    #       Log.MEMORY  |
    #       Log.BLTS    |
    #       Log.EVENTS  |
    #       Log.EVENTS2  |
    0)
    
#    avgPlayer.setResolution(1, 0, 0, 24)
    avgPlayer.loadFile("sponc.avg")

    Tracker = avgPlayer.addTracker("avgtrackerrc")
    avgPlayer.setVBlankFramerate(1)

    # some operations fail when the Player ain't
    # running yet, so:
    avgPlayer.setTimeout(0,myinit)
    avgPlayer.setOnFrameHandler(showTrackerImage)
    avgPlayer.play()

main()
