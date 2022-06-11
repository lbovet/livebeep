#/bin/sh

jackd -dalsa -dhw:SB,0 -r44100 -p1024 -n2 &

sleep 2

a2jmidid -e &

sleep 2

carla $(dirname $0)/livebeep.carxp
