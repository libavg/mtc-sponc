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
#
# Audio gateway by OXullo Intersecans <x@xul.it>
# Setup howto can be found here:
# https://www.libavg.de/wiki/index.php/Audio_on_Sponc

g_AudioEnabled = True
try:
    import scsynth
except ImportError:
    g_AudioEnabled = False
import os, time

if g_AudioEnabled:
    class SponcPlayer(scsynth.Player):
        def __init__(self, server, quadra=False):
            scsynth.Player.__init__(self, server)
            self.ldr = scsynth.loader.Loader(server)
            self.quadra = quadra
            
        def allocateSample(self, file):
            return self.ldr.load(file, True)
        
        def allocateSynth(self, synth):
            sid = self.play_rt(synth)
            time.sleep(0.1)
            return sid
            
        def playSample(self, bid, xpos=0, ypos=0, loop=False):
            sid = self.server.synthpool.get()

            if self.quadra:
                sdef = 'QuadraPlayer'
            else:
                sdef = 'StereoPlayer'
                
            if loop:
                self.server.sendMsg('/s_new', sdef, sid, 0, 0, 'bufnum', bid, 'xpos', xpos, 'ypos', ypos, 'loop', 1)
                return sid
            else:
                self.server.sendMsg('/s_new', sdef, sid, 0, 0, 'bufnum', bid, 'xpos', xpos, 'ypos', ypos)
# TODO: asynchronous sid recycling!
#            self.server.synthpool.recycle(sid)
                return None

        def killSample(self, sid):
            self.server.sendMsg('/n_free', sid)
            self.server.synthpool.recycle(sid)
        
        def loadSynthDef(self, file):
            print "Loading: ",file
            self.server.sendMsg('/d_load', file)
        
        def setParam(self, sid, key, value):
            self.server.sendMsg('/n_set', sid, key, value)

class AudioInterface:
    def __init__(self, sponcDir, quadra=False, debug=False):
        global g_AudioEnabled
        
        if not g_AudioEnabled:
            print "AUDIO: Audio subsystem not available"
            return
        
        self.__soundDir = os.path.abspath(sponcDir+'/media/Sound')

        self.__server = scsynth.connect()
        
        try:
            self.__server.sendMsg('/notify', 1)
            self.__server.receive()
        except:
            print "AUDIO: Audio subsystem available but server is not responding. Disabling audio"
            g_AudioEnabled = False
            return
            
        if debug:
            self.__server.sendMsg('/dumpOSC', 1)

        self.__server.sendMsg('/g_freeAll', 0);
        
        self.__scPlayer = SponcPlayer(self.__server, quadra)

        self.__scPlayer.loadSynthDef(self.__soundDir+'/scsyndefs/QuadraPlayer.scsyndef')
        self.__scPlayer.loadSynthDef(self.__soundDir+'/scsyndefs/StereoPlayer.scsyndef')
        self.__scPlayer.loadSynthDef(self.__soundDir+'/scsyndefs/simpleAnalog.scsyndef')

        self.__sampDict = {}
        self.__sampDict['ping_left'] = self.__scPlayer.allocateSample(self.__soundDir+'/ping_left.wav')
        self.__sampDict['ping_right'] = self.__scPlayer.allocateSample(self.__soundDir+'/ping_right.wav')
        self.__sampDict['boundary'] = self.__scPlayer.allocateSample(self.__soundDir+'/bande_dry.wav')
        self.__sampDict['goal'] = self.__scPlayer.allocateSample(self.__soundDir+'/tor_bekommen.wav')

        self.__leftSynth = scsynth.Synth()
        self.__leftSynth.name = 'simpleAnalog'
        self.__rightSynth = scsynth.Synth()
        self.__rightSynth.name = 'simpleAnalog'
        
        self.__leftSynthSID = self.__scPlayer.allocateSynth(self.__leftSynth)
        self.__rightSynthSID = self.__scPlayer.allocateSynth(self.__rightSynth)
        
        self.setStretchParam('left', 'baseFreq', 69)
        self.setStretchParam('left', 'xpos', -1)
        self.setStretchParam('right', 'xpos', 1)
        
        print "AUDIO: Audio subsystem initialized"
        
        if quadra:
            print "AUDIO: Using QuadraPlayer synthdef for sample playback"
        else:
            print "AUDIO: Using StereoPlayer synthdef for sample playback"
        
    def playSample(self, label, posx=0, posy=0):
        global g_AudioEnabled
        if not g_AudioEnabled:
            return
        self.__scPlayer.playSample(self.__sampDict[label], posx, posy)

    def setStretchGate(self, side, on):
        global g_AudioEnabled
        if not g_AudioEnabled:
            return

        if on:
            val = 1
        else:
            val = 0
        
        self.setStretchParam(side, 'gate', val)
            
    def setStretchParam(self, side, key, value):
        global g_AudioEnabled
        if not g_AudioEnabled:
            return

        if side == 'left':
            self.__scPlayer.setParam(self.__leftSynthSID, key, value)
        else:
            self.__scPlayer.setParam(self.__rightSynthSID, key, value)
        
    def deInit(self):
        global g_AudioEnabled
        if not g_AudioEnabled:
            return

        self.__server.sendMsg('/g_freeAll', 0);
        self.__server.sendMsg('/dumpOSC', 0)
        
        
