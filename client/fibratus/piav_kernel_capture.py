"""
Stores registry changes, and loads of other bits yanno
"""
import json
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

__store__ = {
    "net": [],
    "file": [],
    "registry": []
}

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        # Convert datetime to isoformat
        if isinstance(o, datetime):
            return o.isoformat()
        # Convert IP addresses to string formats
        elif isinstance(o, (IPv4Address, IPv6Address)):
            return str(o)

        return json.JSONEncoder.default(self, o)

def on_init():
    pass

def on_next_kevent(kevent):
    data = {
        "event_name": kevent["name"],
        "params": kevent["kparams"]
    }

    __store__[kevent["category"]].append(data)
    
def on_stop():
    print("Dumping {} net events, {} file events and {} registry events...".format(len(__store__["net"]), len(__store__["file"]), len(__store__["registry"])))
    try:
        with open("fibratus_capture.json", "w") as output:
            json.dump(__store__, output, cls=CustomEncoder)
    except Exception as e:
        print("An error occured while trying to dump kernel events...")
        print(e)
    else:
        print("Successfully dumped kernel events.")
