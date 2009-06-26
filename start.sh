#!/bin/bash
cd `dirname $0`
export SC_JACK_DEFAULT_OUTPUTS="alsa_pcm:playback_1,alsa_pcm:playback_2"
while [ true ]; do
    killall -9 scsynth
    scsynth -u 57110 -b 1026 2>/dev/null &
    sleep 6
    ./Game.py >> sponc.log 2>&1
    killall scsynth
    sleep 1
    killall -9 scsynth
    sleep 1
done
