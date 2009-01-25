#!/bin/bash
export SC_JACK_DEFAULT_OUTPUTS="alsa_pcm:playback_1,alsa_pcm:playback_2"
while [ true ]; do
    scsynth -u 57110 -b 1026 2>/dev/null &
    sleep 6
    ./sponc.py >> sponc.log 2>&1
    killall scsynth
    sleep 1
    killall -9 scsynth
    sleep 1
done
