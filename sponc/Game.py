#!/usr/bin/env python
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



import os
import math
from random import random, seed

from libavg import avg, Point2D, apphelpers, app
from libavg.utils import getMediaDir
from libavg.widget import button

from Geometry import Box, Line, Triangle
import Audio
import config


g_player = avg.Player.get()

def screenPosToSoundPos(screenPos):
    return ((screenPos.x / config.resolution.x) * 2 - 1.0,
            (screenPos.y / config.resolution.y) * 2 - 1.0)


class Clash(avg.ImageNode):
    """clash explosion"""

    def __init__(self, game, pos, **kwargs):
        super(Clash, self).__init__(href="clash.png", **kwargs)
        self.registerInstance(self, None)
        game.addNode(self)
        self.center = pos

        self.step = 0
        self.__onFrameHandler = g_player.subscribe(g_player.ON_FRAME, self.__animate)
        self.__animate()

    def __animate(self):
        self.width = 80*math.log(self.step*10+2)
        self.height = self.width
        self.pos = self.center - self.size / 2
        self.step += 1
        if self.step > 3:
            self.__stop()

    def __stop(self):
        g_player.unsubscribe(g_player.ON_FRAME, self.__onFrameHandler)
        self.unlink(True)


class SideLine(Line):

    def __init__(self, p1, p2):
        Line.__init__(self, p1, p2)

    def onClash(self, object, position):
        Line.onClash(self, object, position)
        if isinstance(object, Ball):
            self.__playSound(position)
            return True

    def __playSound(self, position):
        global g_AudioInterface

        spos = screenPosToSoundPos(position)
        g_AudioInterface.playSample('boundary', spos[0], spos[1])


class BoundaryLine(Line):

    """line to be put at the left and right play area ends - whenever it's hit,
    the corresponding player loses a point"""
    def __init__(self, p1, p2, player):
        Line.__init__(self, p1, p2)
        self.__player = player

    def onClash(self, object, position):
        if isinstance(object, Ball):
            bGameOver = self.__player.lose()
            object.reset()
            self.__playSound(position)
            return True

    def isHard(self):
        return False

    def __playSound(self, position):
        global g_AudioInterface

        spos = screenPosToSoundPos(position)
        g_AudioInterface.playSample('goal', spos[0], spos[1])


def eventPosToCagePos(event):
    cageNode = g_player.getElementByID('cage')
    return cageNode.getRelPos(event.pos)


class Batpoint(Point2D):

    def __init__(self, player, pos):
        Point2D.__init__(self, pos)
        self.player = player
        self.node = g_player.createNode('image',
                {'href':'finger.png', 'size': config.BATPOINT_SIZE})
        avg.ContinuousAnim(self.node, "angle", 0, config.FINGER_ROT_SPEED, False).start()
        player.game.addNode(self.node)
        self.updateNode()

        self.dependants=[]
        self.lines=[]
        self.__cursorID = None

    def onCursorDown(self, event):
        self.__cursorID = event.cursorid
        self.node.subscribe(avg.Node.CURSOR_MOTION, self.onCursorMotion)
        self.node.subscribe(avg.Node.CURSOR_UP, self.onCursorUp)
        self.node.setEventCapture(event.cursorid)
        self.goto(event.pos-config.SPACING)
        self.player.changeSound()

    def onCursorMotion(self, event):
        if event.cursorid != self.__cursorID:
            return
        self.goto(event.pos-config.SPACING)
        self.player.changeSound()

    def onCursorUp(self, event):
        if event.cursorid != self.__cursorID:
            return
        self.release()

    def release(self):
        if not self.__cursorID:
            return
        self.node.releaseEventCapture(self.__cursorID)
        self.__cursorID = None
        self.player.changeSound()

    def isTouched(self):
        return self.__cursorID is not None

    def inCage(self, pos):
        return self.player.cage.inbound(pos)

    def getOther(self): # XXX
        if(self.player.ends[0]==self):
            other=self.player.ends[1]
        else:
            other=self.player.ends[0]
        return other

    def addDependant(self, dep):
        self.dependants.append(dep)

    def addLine(self, line):
        """add a line connected to this batpoint"""
        self.lines.append(line)

    def goto(self, pos):
        """reposition batpoint: new position (x,y) marks the middle of the new
        batpoint"""
        new=self.inCage(pos)

        if self.player.batline.isHard():
            self.moveBounce(new)

        self.x, self.y = new

        self.updateNode()
        self.updateDependants()

    def updateDependants(self):
        for dep in self.dependants:
            dep.onEndUpdate(self)

    def moveBounce(self, new):
        """once this batpoint is moved, try linemove-bounces"""
        for line in self.lines:
            line.moveBounce(self, new)

    def updateNode(self):
        self.node.pos = self - self.node.size/2


class BatLine(Line):

    def __init__(self, gfxhref, ends, game):
        self.ends = ends
        for end in ends:
            end.addDependant(self)
            end.addLine(self)
        self.node = g_player.createNode('<image href="%s"/>' % gfxhref)
        self.updateNode()
        game.addNode(self.node)
        game.addSurface(self)
        self.game = game

    def onEndUpdate(self, xxx):
        self.updateNode()

    def updateNode(self):
        p1 = self.ends[0]
        p2 = self.ends[1]

        self.node.height = math.fabs(self.getLength() - self.ends[0].node.height + 15)
        # ^ assume both ends have the same diameter
        # we want a line from the edges of the batpoints, not from the middles

        width = self.getWidth()

        self.node.width = math.fabs(width)

        if self.isHard():
            self.node.opacity = 1
        else:
            self.node.opacity = 0

        self.node.x = (p1.x+p2.x)/2 - (self.node.width/2)
        self.node.y = (p1.y+p2.y)/2 - (self.node.height/2)

        self.node.angle = self.getNormal()

    def getWidth(self):
        return (config.MAX_BAT_LENGTH-self.getLength())/10.0

    def isHard(self):
        return self.getLength() <= config.MAX_BAT_LENGTH

    def onClash(self, object, position):
        if self.isHard():
            Clash(self.game, pos=position)
            object.hitSpeedup(self.getLength()/config.MAX_BAT_LENGTH)

            self.__playSound(position)
        Line.onClash(self, object ,position)
        return False

    def moveBounce(self, end, new):
        """
        O = old point -> moved batend
        N = new point -> new position
        F = fixpoint  -> other bat-end
        """

        F = self.ends[0]
        O = self.ends[1]
        if (end != O):
            (F,O) = (O,F)
        N = new
        T = Triangle(F, O, N)
        if isinstance(self.game.curState, PlayingState):
            ball = self.game.curState.ball
            if T.contains(ball):
                self.__playSound(N)
#               if Line(F,N).getAngle()-Line(F,O).getAngle()<0.05:
#                   return
#               print "triangle: %s, ball=%s" % (T,ball)
                moveline = Line(O,N)
                newdir = moveline.getAngle() + 0.01
                ball.direction = newdir
                ball.updateNext()
                newbat = Line(F, N)
                movevect = Point2D(ball.nextx, ball.nexty) - ball
                futurepos = ball + 100 * movevect
                ballmove = Line(ball, futurepos)
                newpos = newbat.collide(ballmove)
#               print "%s and %s collide at %s" % (newbat,moveline,newpos)
                if (newpos): #XXX
                    ball.goto(newpos.x,newpos.y)
                else:
                    print "warning: no newpos!"
                Clash(self.game, pos=ball)
                ball.hitSpeedup(self.getLength()/(config.MAX_BAT_LENGTH*2))
                ball.update()

    def __playSound(self, position):
        global g_AudioInterface

        spos = screenPosToSoundPos(position)
#        print position, spos
        if position.x < 640:
            g_AudioInterface.playSample('ping_left', spos[0], spos[1])
        else:
            g_AudioInterface.playSample('ping_right', spos[0], spos[1])


class Player:

    def __init__(self, cage, game):
        global g_AudioInterface
        self.cage = cage
        self.score = 0
        self.game = game

        xpos = cage.x + cage.width/2
        self.addBatpoints(Point2D(xpos,cage.height*1/3), Point2D(xpos,cage.height*2/3))
        self.batline = BatLine("bat.png", self.ends, game)
        self.__playerActive = False
        self.__soundStopTimeout = -1

        if cage.x == 0:
            self.side = 'left'
        else:
            self.side = 'right'

    def addBatpoints(self, pos1, pos2):
        self.ends = (
                Batpoint(self, pos1),
                Batpoint(self, pos2)
                )

    def lose(self):
        self.game.adjust_score(self)

    def release(self):
        for batpoint in self.ends:
            batpoint.release()
        self.__changeSound()

    def onCursorDown(self, event):
        if not self.cage.contains(event.pos):
            return
        mindist = 10000
        curBatpoint = None
        for batpoint in self.ends:
            dist = Line(event.pos, batpoint).getLength()
            if dist < mindist and not batpoint.isTouched():
                mindist = dist
                curBatpoint = batpoint
        if curBatpoint:
            curBatpoint.onCursorDown(event)

    def changeSound(self): # XXX
        self.__changeSound()

    def __changeSound(self):

        def stopSynth():
            g_AudioInterface.setStretchParam(self.side, 'gate', 0)

        global g_AudioInterface
        if self.ends[0].isTouched() and self.ends[1].isTouched():
            if not(self.__playerActive):
                self.__playerActive = True
                #start playback
                g_AudioInterface.setStretchParam(self.side, 'gate', 1)
                g_player.clearInterval(self.__soundStopTimeout)
        else:
            if self.__playerActive:
                self.__playerActive = False
                #stop playback
                self.__soundStopTimeout = g_player.setTimeout(200, stopSynth)
        # change synth params
        g_AudioInterface.setStretchParam(self.side, 'fCutoff',
                self.batline.getLength()/config.MAX_BAT_LENGTH * 1950 + 50)
        ypos = (self.ends[0].y+self.ends[1].y)/config.resolution.y - 1
        g_AudioInterface.setStretchParam(self.side, 'ypos', ypos)


class Ball(Point2D):

    def __init__(self, posx, posy, game):
        Point2D.__init__(self, 0, 0)
        self.startx = posx
        self.starty = posy
        self.game = game

        self.node = self.createNode(game, posx, posy)
        self.reset()

    def createNode(self, game, x, y):
        balldiv = g_player.createNode('<div x="%i" y="%i"></div>' % (x,y))
        img = g_player.createNode('image', {"href":"ball.png"})
        img.size = config.BALL_SIZE
        balldiv.appendChild(img)
        game.addNode(balldiv)
        self.radius = img.width/2.0
        return balldiv

    def stop(self):
        self.node.unlink(True)

    def reset(self):
        self.direction = random()*2.0-1 # from -1.0 to 1.0
        self.direction *= math.pi/5
        if (random() > 0.5): # 50% -> shoot left
            self.direction += math.pi

        self.speed = config.BASE_BALL_SPEED
        self.sleepStartTime = g_player.getFrameTime()
        self.node.opacity = 0
        self.goto(self.startx, self.starty)
        avg.fadeIn(self.node, 1500, 1.0)

    def goto(self,x,y):
        if x < -100 or x > self.game.node.width + 100:
            print ("BUG! ball out of horizontal bounds: %s, next %s, old next %s speed %f!"
                    % (self, Point2D(x,y), Point2D(self.nextx,self.nexty), self.speed))
            self.reset()
        if y < -100 or y > self.game.node.height + 100:
            print ("BUG! ball out of vertical bounds: %s, next %s, old next %s speed %f!"
                    % (self, Point2D(x,y), Point2D(self.nextx,self.nexty), self.speed))
            self.reset()
        self.x = x
        self.y = y
        self.updateNode()

    def updateNode(self):
        self.node.x = self.x - self.radius
        self.node.y = self.y - self.radius

    def gotoNext(self):
        self.updateNext()
        self.goto(self.nextx, self.nexty)

    def updateNext(self):
        self.nextx = self.x + (math.cos(self.direction)*self.speed)
        self.nexty = self.y + (math.sin(self.direction)*self.speed)

    def update(self):
        if g_player.getFrameTime() - self.sleepStartTime < config.TIME_BETWEEN_BALLS:
            return

        #check if the ball collides with bats
        for line in self.game.getSurfaces():
            if self.trybounce(line):
#               print "bouncing!"
                return # a bounce might trigger a .reset(), we dont want to move
                       # directly after that, so return

        #move ball
        self.gotoNext()

    def trybounce(self, line):
        self.updateNext()
        moveline = Line(self, Point2D(self.nextx,self.nexty))
        intersection = moveline.clash(line)

        if (intersection):
            return line.onClash(self, intersection)
#           print "doing bounce of %s <> %s: %s" % (moveline,line,intersection)
#           if(line.isHard()):
#               print "hardbounce"
#               self.dobounce(line)
#               return True
#           else:
#               return False
        return False

    def dobounce(self, line):
        moveline = Line(self, Point2D(self.nextx,self.nexty))
        intersection = moveline.collide(line) # lines do not HAVE to intersect!
        if not intersection:
            print "lines are parallel"
            return False

        normale = line.getNormal()
        if (abs(winkelabstand(normale+math.pi,self.direction)) >
                abs(winkelabstand(normale,self.direction))):
            normale += math.pi

        einfall = winkelabstand(normale, self.direction+math.pi)
        ausfall = normale + einfall
        self.direction = ausfall;

    def hitSpeedup(self, factor):
        hitSpeed = 5/factor
        maxSpeedup = config.BASE_BALL_SPEED * 2
        if hitSpeed > maxSpeedup:
            hitSpeed = maxSpeedup
        self.speed = hitSpeed + config.BASE_BALL_SPEED

def sgn(x):
    if x < 0: return -1
    if x > 0: return 1
    if x == 0: return 0

def winkelabstand(a, b):
    a %= math.pi*2
    b %= math.pi*2
    d = a-b
    if d < 0:
        d = math.pi*2 - d
    d *= sgn(a-b)
    return d

class Button(button.BmpButton):

    def __init__(self, upImage, downImage, clickHandler=None, **kwargs):
        button.BmpButton.__init__(self, upSrc=upImage, downSrc=downImage, **kwargs)
        if clickHandler:
            self.subscribe(self.CLICKED, clickHandler)

        avg.fadeIn(self, config.STATE_FADE_TIME)


class IdleState:

    def __init__(self, game):
        self.game = game
        self.node = g_player.getElementByID("buttons")

    def enter(self):
        self.game.hideScore()
        self.game.showButtons(True)

    def leave(self):
        self.game.showButtons(False)


class InfoState:

    def __init__(self, game):
        self.game = game
        self.node = g_player.getElementByID("infoscreen")

    def enter(self):
        self.game.hideScore()
        self.node.sensitive = True
        avg.fadeIn(self.node, config.STATE_FADE_TIME)
        g_player.setTimeout(20000, self.__back)
        self.eventID = self.node.subscribe(avg.Node.CURSOR_DOWN,
                lambda event: self.__back())

    def leave(self):
        self.node.unsubscribe(avg.Node.CURSOR_DOWN, self.eventID)
        avg.fadeOut(self.node, config.STATE_FADE_TIME)
        self.node.sensitive = False

    def __back(self):
        self.game.switchState(self.game.idleState)


class PlayingState:

    def __init__(self, game):
        self.game = game
        self.node = game.node
    def enter(self):
        self.__toUpdate=[]
        self.game.resetScores()
        self.ball = Ball(self.node.width/2,self.node.height/2,self.game)
        self.__toUpdate.append(self.ball)
        self.__onFrameHandler = g_player.subscribe(g_player.ON_FRAME, self.onFrame)
    def leave(self):
        self.ball.stop()
        self.ball = None
        g_player.unsubscribe(g_player.ON_FRAME, self.__onFrameHandler)
    def onFrame(self):
        for x in self.__toUpdate:
            x.update()
        for p in self.game._players:
            if p.score >=config.MAX_SCORE:
                self.game.switchState(self.game.endState)

class EndState:

    def __init__(self, game):
        self.game = game
        self.node = game.node
    def enter(self):
        self.timeout = g_player.setTimeout(5000, self.onTimeout)
        winnerField = g_player.getElementByID("winner")
        avg.fadeIn(winnerField, config.STATE_FADE_TIME)
        winner_left = g_player.getElementByID("winner_left")
        winner_right = g_player.getElementByID("winner_right")
        if self.game.getWinner() == 0:
            winner_left.opacity = 1
            winner_right.opacity = 0
        else:
            winner_left.opacity = 0
            winner_right.opacity = 1

    def leave(self):
        g_player.clearInterval(self.timeout)
        winnerField = g_player.getElementByID("winner")
        avg.fadeOut(winnerField, config.STATE_FADE_TIME)

    def onTimeout(self):
        self.game.switchState(self.game.idleState)

    def onStartClick(self, event):
        self.game.switchState(self.game.playingState)


class SponcApp(app.MainDiv):
    def onInit(self):
        global g_AudioInterface

        avg.WordsNode.addFontDir(getMediaDir(__file__, 'fonts'))

        cageWidth = self.width - 2 * config.SPACING.x
        cageHeight = self.height - 2 * config.SPACING.y
        playerWidth = cageWidth / 3.0

        dotLine1x = self.width * 1 / 3
        dotLine2x = self.width * 2 / 3

        sizeRatio = self.width/1280
        titleSize = Point2D(725, 128) * sizeRatio
        titlePos = Point2D(self.width/2 - titleSize.x/2,
                config.SPACING.y*3*sizeRatio)
        fontSize = 90 * sizeRatio
        self.mainNode = g_player.createNode(
        """
        <div mediadir="%(mediadir)s">
            <image width="%(width)u" height="%(height)u" href="black.png"/>
            <image width="%(width)u" height="%(height)u" href="background_color.png"
                    opacity="0.5"/>
            <image id="background_texture" width="%(width)u" height="%(height)u"
                    href="background_texture.png" blendmode="add" opacity="0.1"/>
            <image href="border.png" y="%(cageY)u"
                    width="%(width)u" height="%(cageHeight)u" opacity="1"/>
            <div id="cage" x="%(cageX)u" y="%(cageY)u"
                    width="%(cageWidth)u" height="%(cageHeight)u">
                <image x="%(vertline1x)u" href="third_line.png" height="%(cageHeight)u"/>
                <image x="%(vertline2x)u" href="third_line.png" height="%(cageHeight)u"/>
                <div id="textfield" x="0" y="%(text_y)u" opacity="0">
                    <words x="%(mid_x)u" y="0" width="%(fontsize)u" alignment="center"
                            text=":" font="%(font)s" fontsize="%(fontsize)u"
                            color="f0ead8"/>
                    <words id="leftplayerscore" x="%(score_left_x)u" width="180"
                            alignment="right" text="00" font="%(font)s"
                            fontsize="%(fontsize)u" color="f0ead8"/>
                    <words id="rightplayerscore" x="%(score_right_x)u" width="180"
                            alignment="left" text="00" font="%(font)s"
                            fontsize="%(fontsize)u" color="f0ead8"/>
                    <div id="winner" opacity="0">
                        <words id="winner_left" x="%(winnerLeft_x)u"
                                width="%(playerWidth)u" alignment="center" text="WINNER"
                                font="%(font)s" fontsize="%(fontsize)u" color="f0ead8"/>
                        <words id="winner_right" x="%(winnerRight_x)u"
                                width="%(playerWidth)u" alignment="center" text="WINNER"
                                font="%(font)s" fontsize="%(fontsize)u" color="f0ead8"/>
                    </div>
                </div>
            </div>
            <div id="buttons"/>
            <div id="infoscreen" sensitive="False" opacity="0">
                <image width="%(width)u" height="%(height)u" href="black.png"
                        opacity="0.8" />
                <image href="title.png" size="%(titleSize)s" pos="%(titlePos)s" />
                <words x="%(mid_x)u" y="%(infotext_y)u" width="%(width)u"
                        alignment="center" fontsize="%(fontsize_info)u" color="f0ead8">
                            <b>Written by:</b><br/>
                            Martin Heistermann<br/>
                            Tim Grocki<br/><br/>
                            <b>Support:</b><br/>
                            Archimedes GmbH<br/>
                            http://www.archimedes-exhibitions.de<br/>
                            <br/>
                            <b>Based on libavg:</b><br/>
                            http://www.libavg.de<br/>
                            <br/>
                            <b>Source code:</b><br/>
                            http://sponc.de
                </words>
            </div>
        </div>
        """ % {
            'mediadir': getMediaDir(__file__),
            'width': self.width,
            'height': self.height,
            'cageX': config.SPACING.x,
            'cageY': config.SPACING.y,
            'cageWidth': cageWidth,
            'cageHeight': cageHeight,
            'vertline1x': playerWidth,
            'vertline2x': cageWidth - playerWidth,
            'playerWidth': playerWidth,
            'text_y': self.height/4,
            'winnerLeft_x': playerWidth/2,
            'winnerRight_x': cageWidth - playerWidth/2,
            'mid_x': self.width/2,
            'score_left_x': self.width/2 - fontSize/4,
            'score_right_x': self.width/2 + fontSize/4,
            'fontsize': fontSize,
            'fontsize_info': fontSize/3,
            'titleSize': titleSize,
            'titlePos': titlePos,
            'infotext_y': self.height/3,
            'font': 'Alarm Clock',
            })
        self.insertChild(self.mainNode, 0)
        self.node = g_player.getElementByID("cage")
        seed()
        self._surfaces=[]

        # Check if quadraphonic system is available
        if os.getenv("MTT_DEPLOY"):
            quadra = True
        else:
            quadra = False
        g_AudioInterface = Audio.AudioInterface(quadra)


        playerleft = Player(Box(0,0,playerWidth,cageHeight), self)
        playerright = Player(Box(cageWidth-playerWidth,0,playerWidth,cageHeight), self)
        self._players = (playerleft, playerright)

        topline = SideLine(Point2D(-10,0), Point2D(cageWidth+10,0))
        self._surfaces.append(topline)

        bottomline = SideLine(Point2D(-10,cageHeight), Point2D(cageWidth+10,cageHeight))
        self._surfaces.append(bottomline)

        leftbound = BoundaryLine(Point2D(0,-10), Point2D(0,cageHeight+10), playerleft)
        self._surfaces.append(leftbound)

        rightbound = BoundaryLine(Point2D(cageWidth,-10),
                Point2D(cageWidth,cageHeight+10), playerright)
        self._surfaces.append(rightbound)

        self.node.subscribe(avg.Node.CURSOR_DOWN, self.onCursorDown)

        self.__states = []
        self.idleState = IdleState(self)
        self.__states.append(self.idleState)
        self.playingState = PlayingState(self)
        self.__states.append(self.playingState)
        self.endState = EndState(self)
        self.__states.append(self.endState)
        self.infoState = InfoState(self)
        self.__states.append(self.infoState)

        self.__createButtons()

        self.curState = None
        self.switchState(self.idleState)
        self.hideMainNodeTimeout = None

        self.touchVisOverlay = app.touchvisualization.TouchVisualizationOverlay(isDebug=False,
                visClass=app.touchvisualization.TouchVisualization, parent=self)

        self.__setupMultitouch()

    def switchState(self, newState):
        if self.curState != None:
            self.curState.leave()
        self.curState = newState
        newState.enter()

    def getSurfaces(self):
        return self._surfaces

    def addSurface(self, surface):
        self._surfaces.append(surface)

    def onCursorDown(self, event):
        for player in self._players:
            player.onCursorDown(event)

    def addNode(self, node):
        self.node.appendChild(node)

    def adjust_score(self, loser):
        for p in self._players:
            if p != loser:
                p.score += 1
        self.showScore()

    def getWinner(self):
        i = 0
        for i, p in enumerate(self._players):
            if p.score == config.MAX_SCORE:
                return i
        bork() # We shouldn't get here.

    def resetScores(self):
        for p in self._players:
            p.score = 0
        self.showScore()

    def showScore(self):
        g_player.getElementByID("leftplayerscore").text = str(self._players[0].score)
        g_player.getElementByID("rightplayerscore").text = str(self._players[1].score)
        scoreDisplay = g_player.getElementByID("textfield")
        avg.LinearAnim(scoreDisplay, "opacity", 400, 1, 0.3, False, None,
            lambda: avg.LinearAnim(scoreDisplay, "opacity", 400, 0.3, 1).start()).start()
        background = g_player.getElementByID("background_texture")
        avg.LinearAnim(background, "opacity", 400, 0.1, 0.3, False, None,
            lambda: avg.LinearAnim(background, "opacity", 400, 0.3, 0.1).start()).start()

    def hideScore(self):
        scoreDisplay = g_player.getElementByID("textfield")
        avg.fadeOut(scoreDisplay, 400)
  
    def showButtons(self, show):
        self.startButton.active = show
        self.infoButton.active = show
        self.exitButton.active = show

    def __createButtons(self):
        screenSize = self.size
        buttonSize = Point2D(210, 80)
#        if self.width < 1280:
#            buttonSize *= self.width/1280
        xPos = (screenSize.x-buttonSize.x)/2

        self.startButton = Button(
                pos=(xPos, screenSize.y/5),
                upImage="start_button_normal.png",
                downImage="start_button_pressed.png",
                clickHandler=lambda: self.switchState(self.playingState),
                parent=self.node)
                
        self.infoButton = Button(
                pos=(xPos, screenSize.y-4*buttonSize.y),
                upImage="info_button_normal.png",
                downImage="info_button_pressed.png",
                clickHandler=lambda: self.switchState(self.infoState),
                parent=self.node)

        self.exitButton = Button(
                pos=(xPos, screenSize.y-3*buttonSize.y),
                upImage="exit_button_normal.png",
                downImage="exit_button_pressed.png",
                clickHandler=g_player.stop,
                parent=self.node)

    def __setupMultitouch(self):
        if app.instance.settings.getBoolean('multitouch_enabled'):
            return

        import platform

        if platform.system() == 'Linux':
            os.putenv('AVG_MULTITOUCH_DRIVER', 'XINPUT')
        elif platform.system() == 'Windows':
            os.putenv('AVG_MULTITOUCH_DRIVER', 'WIN7TOUCH')
        else:
            os.putenv('AVG_MULTITOUCH_DRIVER', 'TUIO')

        try:
            g_player.enableMultitouch()
        except Exception, e:
            os.putenv('AVG_MULTITOUCH_DRIVER', 'TUIO')
            g_player.enableMultitouch()


if __name__ == '__main__':
    app.App().run(SponcApp())

