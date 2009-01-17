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
#from config import *
import config

global game

def onKey(event):
    global g_tracker
    if event.keystring=='h':
        print "resetting history"
        g_tracker.resetHistory()
    elif event.keystring=='d':
        fingers = avg.Player.get().getElementByID('fingers')
        fingers.opacity = 1 - fingers.opacity

def main():
    global g_tracker
    def myinit():
        g_tracker.setDebugImages(True, True)
        game = Game.Game(avgPlayer.getElementByID("main"), True)
        game.enter()

    def showTrackerImage():
        Bitmap = g_tracker.getImage(avg.IMG_FINGERS)
        Node = avgPlayer.getElementByID("fingers")
        Node.setBitmap(Bitmap)
        Node.width=1280
        Node.height=800
        #Grid = Node.getOrigVertexCoords()
        #Grid = [ [ (pos[0], 1-pos[1]) for pos in line ] for line in Grid]
        #Node.setWarpedVertexCoords(Grid)
    avgPlayer = avg.Player.get()
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
    
    avgPlayer.loadFile("sponc.avg")
    avgPlayer.showCursor(False)
    avgPlayer.setResolution(
            True, # fullscreen
            int(config.RESOLUTION[0]), # width
            int(config.RESOLUTION[1]), # height
            0 # color depth
            )
    g_tracker = avgPlayer.addTracker("avgtrackerrc")
    avgPlayer.setVBlankFramerate(1)

    # some operations fail when the Player ain't
    # running yet, so:
    avgPlayer.setTimeout(0,myinit)
    avgPlayer.setOnFrameHandler(showTrackerImage)
    avgPlayer.getRootNode().setEventHandler(avg.KEYDOWN, avg.NONE, onKey)
    avgPlayer.play()

main()
