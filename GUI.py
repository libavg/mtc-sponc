# Copyright (C) 2007
#    Martin Heistermann, <mh at lulzmeister dot de>
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


from Geometry import Box

g_buttons=[]

def CursorUp(pos):
    for b in g_buttons:
        if(b.match(pos)):
            if(b.parent.active):
                b.click()

def CursorDown(pos):
    for b in g_buttons:
        if(b.match(pos)):
            if(b.parent.active):
                b.down()


class Image(Box):
    def __init__(self,parent,x,y,width,height,href,putUnder=False):
        Box.__init__(self,x,y,width,height)
        self.parent=parent
        self.height=height
        self.width=width
        self.node=g_Player.createNode(
        '<image x="%i" y="%i" />' %(x,y))
        self.setHref(href)
        if putUnder:
            self.parent.node.insertChild(self.node,0)
        else:
            self.parent.node.appendChild(self.node)
    def setHref(self,href):
        self.node.href=href
        self.node.height=self.height
        self.node.width=self.width
    def stop(self):
        pos=self.parent.node.indexOf(self.node)
        self.parent.node.removeChild(pos)
    def setOpacity(self,val):
        self.node.opacity=val

class Label(Box):
    def __init__(self,parent,x,y,width,height,text,center=False,size=40,font="Checkbook"):
        Box.__init__(self,x,y,width,height)
        self.parent=parent
        self.center=center
        self.node=g_Player.createNode(
        '<words x="%i" y="%i" size="%i" font="%s"></words>' %(x,y,size,font))
        self.parent.node.appendChild(self.node)
        self.setText(text)
    def setText(self,text):
        self.node.text=str(text)
#       print "text '%s' is %u wide" %(text,self.node.width)
        if self.center:
            self.doCenter()
    def setColor(self,color):
        self.node.color=color
    def doCenter(self):
        self.node.x=self.x+(self.width-self.node.width)/2
        self.node.y=self.y+(self.height-self.node.height)/2
    def stop(self):
        pos=self.parent.node.indexOf(self.node)
        self.parent.node.removeChild(pos)

def init(Player):
    global g_Player
    g_Player = Player


