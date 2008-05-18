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



from util import in_between, boundary, delNode
from Geometry import Point, Box, Line, Triangle
from config import *
from libavg import avg
from libavg import anim
from random import random, seed
import GUI
import sys

numRound=0

MAX_SCORE=25

#GLOBAL LISTS
toUpdate=[]
toAnimate=[]
players=[]
surfaces=[]
touchactive=[]

class Clash(Point):
    """clash explosion"""
    def __init__(self,p):
        self.node=g_Player.createNode(
                '<image href="clash.png" />')
        cage.appendChild(self.node)
        (self.x,self.y)=(p.x,p.y)
        self.step=0
        
        self.animate()
        toAnimate.append(self)

    def animate(self):
        self.node.width=80*math.log(self.step*10+2)
        self.node.height=self.node.width
        self.node.x=self.x-self.node.width/2
        self.node.y=self.y-self.node.height/2
        self.step+=1
        if(self.step>3):
            self.stop()
    def stop(self):
        toAnimate.remove(self)
        delNode(self.node)

class BoundaryLine(Line):
    """line to be put at the left and right play area ends - whenever its hit,
    the corresponding player loses a point"""
    def __init__(self,p1,p2,player):
        Line.__init__(self,p1,p2)
        self.player=player
    def onClash(self,object,position):
        if isinstance(object, Ball): 
            bGameOver = self.player.lose()
            object.reset()
            return True
    def isHard(self):
        return False

class Batpoint(Point):
    def __init__(self,bat,pos,size=50):
        global cage,touchactive
        self.bat=bat
        self.node=g_Player.createNode(
        '<image width="%i" height="%i" href="%s" />' % (size,size,"finger.png"))
        self.size=size
        self.x=pos.x
        self.y=pos.y
        self.anim=anim.ContinuousAnim(self.node,"angle",0,fingerRotSpeed,False)
        cage.appendChild(self.node)
        self.updateNode()

        self.dependants=[]
        self.lines=[]
    def onMouse(self,pos):
        pos.x-=cage.x
        pos.y-=cage.y
        self.goto(pos)
    def inCage(self,pos):
        return self.bat.player.cage.inbound(pos)
    def getOther(self): # XXX
        if(self.bat.ends[0]==self):
            other=self.bat.ends[1]
        else:
            other=self.bat.ends[0]
        return other
    def getNewPos(self,pos):
        p=self.inCage(pos)
        return p
    def addDependant(self,dep):
        self.dependants.append(dep)
    def addLine(self,line):
        """add a line connected to this batpoint"""
        self.lines.append(line)
    def goto(self,pos):
        """reposition batpoint: new position (x,y) marks the middle of the new
        batpoint"""
        new=self.getNewPos(pos)
    
        if self.bat.isHard():
            self.moveBounce(new)

        (self.x,self.y)=(new.x,new.y)
        self.updateNode()
        self.updateDependants()


    def updateDependants(self):
        for dep in self.dependants:
            dep.onEndUpdate(self)

    def moveBounce(self,new):
        """once this batpoint is moved, try linemove-bounces"""
        for line in self.lines:
            line.moveBounce(self,new)

    def updateNode(self):
        self.node.x=self.x-self.size/2
        self.node.y=self.y-self.size/2

class FixBatpoint(Batpoint):
    def getNewPos(self,pos):
        global fixBatLength
        new=self.inCage(pos)
        other=self.getOther()
        l=Line(other,new)
        len=l.getLength()
        ratio=fixBatLength/len
        deltax=l.ends[1].x-l.ends[0].x
        deltay=l.ends[1].y-l.ends[0].y

        newx=l.ends[0].x+ratio*deltax
        newy=l.ends[0].y+ratio*deltay

        return self.inCage(Point(newx,newy))


class BatLine(Line):
    def __init__(self,gfxhref,ends,game):
        global cage
        self.ends=ends
        for end in ends:
            end.addDependant(self)
            end.addLine(self)
        self.node=g_Player.createNode('<image href="%s"/>' % gfxhref)
        self.updateNode()
        cage.appendChild(self.node)
        surfaces.append(self)
        self.game = game

    def onEndUpdate(self,xxx):
        self.updateNode()
    def updateNode(self):
        p1=self.ends[0]
        p2=self.ends[1]

        self.node.height=self.getLength()-self.ends[0].node.height+15
        # ^ assume both ends have the same diameter
        # we want a line from the edges of the batpoints, not from the middles

        width=self.getWidth()

        self.node.width=boundary(width,minBatWidth,maxBatWidth)

        if self.isHard():
            self.node.opacity=1
        else:
            self.node.opacity=0

        self.node.x=(p1.x+p2.x)/2-(self.node.width/2)
        self.node.y=(p1.y+p2.y)/2-(self.node.height/2)

        self.node.angle=self.getNormal()

    def getWidth(self):
        return 10
        
    def isHard(self):
        return True
    
    def onClash(self,object,position):
        if self.isHard():
            Clash(position)
        Line.onClash(self,object,position)
        return False
    def moveBounce(self,end,new):
        """
        O = old point -> moved batend
        N = new point -> new position
        F = fixpoint  -> other bat-end
        """

        F=self.ends[0]
        O=self.ends[1]
        if(end!=O):
            (F,O)=(O,F)
        N=new
        T=Triangle(F,O,N)
        ball = self.game.ball
        if T.contains(ball):
#               if Line(F,N).getAngle()-Line(F,O).getAngle()<0.05:
#                   return
#               print "triangle: %s, ball=%s" % (T,ball)
            moveline=Line(O,N)
            newdir=moveline.getAngle()+0.01
            ball.direction=newdir
            ball.updateNext()
            newbat=Line(F,N)
            newpos=newbat.collide(moveline)
#               print "%s and %s collide at %s" % (newbat,moveline,newpos)
            if(newpos): #XXX
                ball.goto(newpos.x,newpos.y)
            Clash(ball)
            ball.hitSpeedup()
            ball.update()

class RipBatLine(BatLine):
    def __init__(self,gfxhref,ends,maxLen, game):
        self.maxLength=maxLen
        BatLine.__init__(self,gfxhref,ends, game)
    def isHard(self):
        return self.getLength()<=self.maxLength
    def getWidth(self):
        return (self.maxLength-self.getLength())/10

class Bat(Line):
    def __init__(self,player,game):
        self.player=player
        pcage=self.player.cage
        xpos=pcage.x+pcage.width/2
        self.addBatpoints(Point(xpos,pcage.height*1/3),Point(xpos,pcage.height*2/3))
        self.batline=RipBatLine("bat.png",self.ends,maxBatLength,game)

    def genBatline(self):
        self.batline=BatLine("bat.png",self.ends)

    def genBatpoint(self,pos):
        return Batpoint(self,pos)

    def addBatpoints(self,pos1,pos2):
        self.ends=(
                self.genBatpoint(pos1),
                self.genBatpoint(pos2)
                )
        for end in self.ends:
            touchactive.append(end)

class Player:
    def __init__(self,cage,batType, game):
        self.cage=cage
        self.score=0
        self.game=game
        # XXX magic numbers
        self.bat=Bat(self,game)

    def lose(self):
        global numRound
        numRound += 1;
        for p in players:
            if(p!=self):
                p.score+=1
        XXXgame.adjust_score()

def onKeyUp(Event):
    if Event.keystring == "t":
#       CoordCalibrator(Tracker, Player)
        pass

class Ball(Point):
    def __init__(self,posx,posy):
        self.startx=posx
        self.starty=posy

        self.node=self.createNode(posx,posy)
        self.reset()
        self.speed = baseSpeed
        toUpdate.append(self)

    def createNode(self,x,y):
        global cage,g_Player

        balldiv=g_Player.createNode('<div x="%i" y="%i"></div>' % (x,y))
        img = g_Player.createNode('image', {"href":"ball.png"})
        balldiv.appendChild(img)
        self.radius = img.width/2.0
        cage.appendChild(balldiv)
        return balldiv
    def stop(self):
        delNode(self.node)
    def reset(self):
        self.direction=random()*2.0-1 # from -1.0 to 1.0
        self.direction*=math.pi/5
        if(random()>0.5): # 50% -> shoot left
            self.direction+=math.pi

        self.numHit = 0
        self.calcSpeed()
        self.sleeptime=25
        self.node.opacity=0
        self.goto(self.startx,self.starty)
        anim.fadeIn(self.node,1500,1.0)

    def goto(self,x,y):
        global numRound
        if(x<-100 or x>cage.width+100):
            print "BUG! ball out of horizontal bounds: %s, next %s, old next %s speed %f!" % (self,Point(x,y),Point(self.nextx,self.nexty),self.speed)
            sys.exit()
        if(y<-100 or y>cage.height+100):
            print "BUG! ball out of vertical bounds: %s, next %s, old next %s speed %f!" % (self,Point(x,y),Point(self.nextx,self.nexty),self.speed)
            sys.exit()
        self.x=x
        self.y=y
        self.updateNode()

    def updateNode(self):
        self.node.x=self.x-self.radius
        self.node.y=self.y-self.radius

    def gotoNext(self):
        self.updateNext()
        self.goto(self.nextx,self.nexty)

    def updateNext(self):
        self.nextx=self.x+(math.cos(self.direction)*self.speed)
        self.nexty=self.y+(math.sin(self.direction)*self.speed)

    def update(self):
        global numRound

        if self.sleeptime:
            self.sleeptime-=1
            return
        
        #check if the ball collides with bats
        for line in surfaces:
            if self.trybounce(line):
#               print "bouncing!"
                return # a bounce might trigger a .reset(), we dont want to move
                       # directly after that, so return
        
        #move ball
        self.gotoNext()

    def trybounce(self,line):
        self.updateNext()
        moveline=Line(self, Point(self.nextx,self.nexty))
        intersection=moveline.clash(line)

        if(intersection):
            return line.onClash(self,intersection)
#           print "doing bounce of %s <> %s: %s" % (moveline,line,intersection)
#           if(line.isHard()):
#               print "hardbounce"
#               self.dobounce(line)
#               return True
#           else:
#               return False
        return False

    def dobounce(self,line):
        moveline=Line(self, Point(self.nextx,self.nexty))
        intersection=moveline.collide(line) # lines do not HAVE to intersect!
        if not intersection:
            print "lines are parallel"
            return False

        normale=line.getNormal()
        if(abs(winkelabstand(normale+math.pi,self.direction))>abs(winkelabstand(normale,self.direction))):
            normale+=math.pi

        einfall=winkelabstand(normale,self.direction+math.pi)
        ausfall=normale+einfall
        self.direction=ausfall;

        self.hitSpeedup()

    def hitSpeedup(self):
        self.numHit +=1
        self.calcSpeed()
    def calcSpeed(self):
        self.speed=(self.numHit*hitSpeedup)+baseSpeed

def sgn(x):
    if x < 0: return -1
    if x > 0: return 1
    if x == 0: return 0

def winkelabstand(a,b):
    a%=math.pi*2
    b%=math.pi*2
    d=a-b
    if d<0:
        d=math.pi*2-d
    d*=sgn(a-b)
    return d

def cageOnCursorMove(event):
    if event.source == avg.TOUCH:
        return
    button=False
    if event.source == avg.TRACK:
        if event.x > 640:
            if event.majoraxis[0]>0:
                y = event.y+event.majoraxis[1]*4
            else:
                y = event.y-event.majoraxis[1]*4
            x = event.x-abs(event.majoraxis[0]*4)
        else:
            if event.majoraxis[0]>0:
                y = event.y-event.majoraxis[1]*4
            else:
                y = event.y+event.majoraxis[1]*4
            x = event.x+abs(event.majoraxis[0]*4)
        pos = Point(x,y)
    else:
        pos = Point(event.x, event.y)
    for b in touchactive:
        # calculate distance to mouse event
        #not real distance, but as we are looking for the smallest one we dont need to sqrt
        dist=(pos.x-b.x)**2+(pos.y-b.y)**2
        if(not button or dist<mindist):
            mindist=dist
            button=b
    button.onMouse(pos);

def onFrame():
    for x in toUpdate:
        x.update()
    for x in toAnimate:
        x.animate()
    XXXgame.onFrame()

class Game:
    def __init__(self):
        global cage,scorenode,XXXgame
        XXXgame=self
        cage=g_Player.getElementByID("cage")
        self.node=cage
        seed()

    def enter(self):
        global cage
        
        batType=0

        playerWidth=cage.width*(400.0/1260)

        playerleft=Player(Box(0,0,playerWidth,cage.height),batType,self)
        playerright=Player(Box(cage.width-playerWidth,0,playerWidth,cage.height),
                batType,self)
        for p in (playerleft, playerright):
            players.append(p)
    
        self.score=GUI.Label(self,playerWidth,0,cage.width-2*playerWidth,cage.height,"DUMMY",True,100,"Checkbook")
        self.score.setColor("FF0000")
        self.adjust_score()

        topline=Line(
                Point(-10,0),
                Point(cage.width+10,0)
                )
        surfaces.append(topline)
        bottomline=Line(
                Point(-10,cage.height),
                Point(cage.width+10,cage.height)
                )
        surfaces.append(bottomline)

        leftbound=BoundaryLine(
                Point(0,-10),
                Point(0,cage.height+10),
                playerleft
                )
        surfaces.append(leftbound)
        rightbound=BoundaryLine(
                Point(cage.width,-10),
                Point(cage.width,cage.height+10),
                playerright
                )
        surfaces.append(rightbound)

        anim.fadeIn(cage,800,1.0)
        self.ball = Ball(cage.width/2,cage.height/2)
        g_Player.setOnFrameHandler(onFrame)
    def leave(self):
        global players
        global surfaces
        anim.fadeOut(cage,800)
        players = []
        self.ball.stop()
        surfaces = []
        self.score.stop()
        g_Player.stop()
        
    def onFrame(self):
        for p in players:
            if p.score >=MAX_SCORE:
                self.stop()
    def adjust_score(self):
        self.score.setText("%i:%i" % (players[0].score,players[1].score))

def init(Player):
    global g_Player
    g_Player = Player


