import threading
reso = 0

def out(t, dbg=None):
    global last_debug, reso
    if reso == 0:
        reso = threading.Lock()


    if dbg == None:
        dbg = last_debug
    else:
        last_debug = dbg

    if dbg:
        with reso:
            print 'DEBUG: ' + t
