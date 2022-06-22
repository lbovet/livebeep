import sys
import time
from mididings import *

from liblo import (
    Address,
    Server,
    make_method,
    send as lo_send,
    TCP as LO_TCP,
)

class Channel:
    def __init__(self):
        self.name = "..."
        self.controls = dict()
    def __repr__(self):
        return "<"+self.name+"> "+str(self.controls)

class Control:
    def __init__(self):
        self.name = "..."
        self.value = 0.0
        self.min = 0.0
        self.max = 0.0

    def __repr__(self):
        return "<"+self.name+"> {"+str(self.min)+".."+str(self.max)+"} "+str(self.value)

class OscServer(Server):
    def __init__(self):
        Server.__init__(self, proto=LO_TCP)

    @make_method('/ctrl/info', 'iiiihiisssssss')
    def plugin_info(self, path, args):
        (
            pluginId, type_, category, hints, uniqueId, optsAvail, optsEnabled,
            name, filename, iconName, realName, label, maker, copyright,
        ) = args
        channel = channels.setdefault(pluginId, Channel())
        channel.name = name

    @make_method('/ctrl/paramInfo', 'iissss')
    def param_info(self, path, args):
        pluginId, paramId, name, unit, comment, groupName = args
        channel = channels.setdefault(pluginId, Channel())
        control = channel.controls.setdefault(paramId, Control())
        control.name = name

    @make_method('/ctrl/paramData', 'iiiiiifff')
    def param_data(self, path, args):
        pluginId, paramId, type_, hints, midiChan, mappedCtrl, mappedMin, mappedMax, value = args
        channel = channels.setdefault(pluginId, Channel())
        control = channel.controls.setdefault(paramId, Control())
        control.value = value

    @make_method('/ctrl/paramRanges', 'iiffffff')
    def param_ranges(self, path, args):
        pluginId, paramId, def_, min_, max_, step, stepSmall, stepLarge = args
        channel = channels.setdefault(pluginId, Channel())
        control = channel.controls.setdefault(paramId, Control())
        control.min = min_
        control.max = max_

    @make_method('/ctrl/iparams', 'ifffffff')
    def carla_iparams(self, path, args):
        pluginId, active, drywet, volume, balLeft, balRight, pan, ctrlChan = args

    def full_url(self):
        return "%sctrl" % self.get_url()

params_init = False
lo_target_tcp = Address("osc.tcp://:22752")

def init_params():
    global params_init
    if not params_init:
        params_init = True
        lo_server_tcp = OscServer()
        lo_send(lo_target_tcp, "/register", lo_server_tcp.full_url())

        start = time.time()
        while time.time() < start + 1.0:
            lo_server_tcp.recv(0)

        lo_send(lo_target_tcp, "/unregister", lo_server_tcp.full_url())
        while lo_server_tcp.recv(0):
            pass
        lo_server_tcp.free()
        lo_server_tcp = None
        print(channels)

channels = dict()

control_port = 1

if(len(sys.argv)>1):
    config(
        in_ports=[ ("controller", "MPK mini.*") ],
        out_ports= [ (name.lower().replace(" ","-"), name+".*") for name in sys.argv[1:] ]
    )
else:
    control_port = 2
    config(
        in_ports = [ ("controller") ],
        out_ports = [ ("instrument"), ("control") ]
    )

def handle_control(ev):
    init_params()
    if ev.type == CTRL and ev.ctrl >= 60 and ev.ctrl <= 67:
        plugin_id = ev.channel-1
        channel = channels.setdefault(plugin_id, Channel())
        param_id = ev.ctrl - 60
        control = channel.controls.setdefault(param_id, Control())
        span = control.max - control.min
        inc = ((ev.value if ev.value < 64 else -(128 - ev.value)) / 128.0) * span
        control.value += inc
        if control.value > control.max:
            control.value = control.max
        if control.value < control.min:
            control.value = control.min
        ev.port = control_port
        lo_send(lo_target_tcp, "/Carla/"+str(plugin_id) +
                "/set_parameter_value", param_id, control.value)
    return ev

run(Process(handle_control) >> Velocity(gamma=3))
