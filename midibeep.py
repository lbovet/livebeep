from mididings import *

channel_controls = dict()

def set_control(channel, control, value):
    global channel_controls
    controls = channel_controls.setdefault(channel, dict())
    controls[control] = value

def get_control(channel, control):
    global channel_controls
    return channel_controls.get(channel, dict()).get(control, 64)

def handle_control(ev):
    if ev.type == CTRL and ev.ctrl >= 60 and ev.ctrl <= 67:
        c = get_control(ev.channel, ev.ctrl)
        c = c + (64.0 - ev.value) / 64.0
        if c < 0:
            c = 0
        if c > 127:
            c = 127
        ev.value = int(c)
        set_control(ev.channel, ev.ctrl, c)
    return ev

run(Process(handle_control) >> Velocity(gamma=3))
