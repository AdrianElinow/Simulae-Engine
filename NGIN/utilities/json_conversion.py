
from NGIN.implementation.lib.SimulaeNode import SimulaeNode
from NGIN.utilities.lib.ngin_console_log import logAll

def jsonify( state: SimulaeNode ):
    logAll("jsonify(state)")

    d = state.__dict__

    for k,v in state.Relations.items():

        v =  v = { nid:node.__dict__ for nid, node in v.items() }
        d['relations'][k] = v

    return d
