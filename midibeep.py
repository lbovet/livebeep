from mididings import *

c = 0

def control_state(ev):
    if ev.type == CTRL:
        global c
        c = c + (64.0 - ev.data2) / 64.0
        if c < 0:
            c = 0
        if c > 127:
            c = 127
        ev.data2 = int(c)
    return ev


run(Process(control_state))
