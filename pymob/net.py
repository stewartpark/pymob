import pymob
import threading
import socket
import datetime
import time
import struct
import pymob.debug


__PYMOB_NET_VERSION__ = 0.01

MAX_CONNECTION = 32
PORT = 4343

#for searching
hosts_range = []

communicator = 0
mobnetl = 0

__dbg = False

MobNets = []
def dummy_hook_mobnet_handler(src, cmd, prm):
    return
hook_mobnet_handler = dummy_hook_mobnet_handler


#avoid network confusion
itersense = {}


__running__ = 0
def get_local_ip():
    try:
        rst = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][0]
    except:
        rst = "0.0.0.0"
    return rst

def default_mobnet_handler(self, data):
    global communicator, MobNets, itersense, hook_mobnet_handler

    isBroadcast = False

    try:
        header = data.split("\xFF", 6)        
        version = header[0]
        species = header[1]
        src = header[2]
        dst = header[3]
        _date = eval(header[4])
        cmd = header[5].upper()
        prm = header[6]
    except:
        pymob.debug.out('wrong packet header')
        return False


    if dst == '':
      dst = '*'
    if species == '':
      species = '*'
    if dst.upper() == 'BROADCAST':
      dst = '*'
      isBroadcast = True

    pymob.debug.out("MobNet overlay network: packet version=" + version + ", species=" + species + ", src=" + src + ", dst=" + dst + ", _date=" + repr(_date) + ", cmd=" + cmd + ", prm=" + prm)

    if version != str(__PYMOB_NET_VERSION__):
        pymob.debug.out("version is different.")
        return False #disconnect
    try:
        if _date <= itersense[src]:
            pymob.debug.out("packet dropped because it's repeated: itersensed.")
            return True #won't disconnect
    except KeyError:
            pymob.debug.out("stranger's packet: allocating new itersense table node")
    itersense[src] = _date #update itersense

    if (dst == '*' or dst == communicator.get('name')) and (species == '*' or species == communicator.get('species')):
        #system commands
        if cmd == "NODE":
            pymob.debug.out("new node noticed:" + prm)
            connect(prm)
        elif cmd == "EXEC":
            pymob.debug.out('EXEC command arrived: processing')
            try:
                send(src, "RESULT", str([True ,eval(prm)]))
                pymob.debug.out(' - done')
            except:
                send(src, "RESULT", str([False, 0]))
                pymob.debug.out(' - error')
        else:
            pymob.debug.out(cmd + ' command hooked: ' + prm)
            t = hook_mobnet_handler(src, cmd, prm)

        if isBroadcast:
           forward(self,data)
        
        return t
    else:
        forward(self, data)
       
def forward(self, data):
    global MobNets
    pymob.debug.out('Forwarding...')
    #other species'network or others, forwarding
    for x in range(len(MobNets)):
        try:
            if MobNets[x]._MobNet__socket.getpeername() == self._MobNet__socket.getpeername():
                pymob.debug.out(' - (sender)')
                continue
            pymob.debug.out(' - (new path) forwarding to ' + MobNets[x]._MobNet__socket.getpeername()[0])
            MobNets[x]._MobNet__socket.send(data + '\n')
        except:
            pymob.debug.out('error raised while forwarding')
    pymob.debug.out("packet forwarded.")
 

class MobNet(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self) #super(this)
        self.__socket = sock
    def run(self):
        global __running__
        t = ''
        buf = ''
        while __running__:
            try:
                t = self.__socket.recv(1)
            except:
                pymob.debug.out("connection reset by peer.")
                t = ''
            if t == '':
                pymob.debug.out('connection lost')
                break

            if t == '\n':
                tt = default_mobnet_handler(self, buf)
                if not tt:
                    break
                buf = ''
            else:
                buf = buf + t

        self.__socket.close()
        del buf, t


class MobNet_Listener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global MobNets, __running__, MAX_CONNECTION
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind( ('0.0.0.0', PORT) )
        self.__socket.listen(MAX_CONNECTION)
        pymob.debug.out('listening on ' + str(PORT))
        while __running__:
            optimize()
            if count() > MAX_CONNECTION:
                continue
            try:
                (client, host)  = self.__socket.accept()
            except:
                pymob.debug.out("accept failed.")
                return
            pymob.debug.out('connected: ' + str(host))
            cmob = MobNet(client)
            MobNets.append(cmob)
            cmob.start()
        self.__socket.close()


class MobNet_Searcher(threading.Thread):
    def __init__(self, hosts_range_l):
        threading.Thread.__init__(self)
        self.hosts_range_ = hosts_range_l
    def run(self):
        global MobNets, __running__, MAX_CONNECTION
        while __running__:
            time.sleep(0.01)
            if count() > MAX_CONNECTION:
                continue
            for x in self.hosts_range_:
                if x in gethosts():
                    continue
                if __running__ == 0:
                    pymob.debug.out("stopped searcher thread.")
                    return
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                try:
                    pymob.debug.out('searching:' + str(x))
                    sock.connect( (x, PORT) )
                    sock.settimeout(None)
                except:
                    continue
                cmob = MobNet(sock)
                MobNets.append(cmob)
                cmob.start()
                pymob.debug.out("discovered a new connection")

def count():
    global MobNets
    return len(MobNets)
def gethosts():
    global MobNets
    hosts = []
    optimize()
    hosts.append(get_local_ip())
    for x in range(len(MobNets)):
        try:
            hosts.append(MobNets[x]._MobNet__socket.getpeername()[0])
        except:
            continue

    return hosts

def sethook(func):
    global hook_mobnet_handler
    hook_mobnet_handler = func

def connect(dst):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect( (dst, PORT) )
    except:
        return False
    cmob = MobNet(sock)
    MobNets.append(cmob)
    cmob.start()
    return True

def optimize():
    global MobNets
    for x in range(len(MobNets)):
        try:
            if not MobNets[x].isAlive():
                MobNets.pop(x)
        except:
            continue

def send(dst, cmd, prm):
    global MobNets, communicator
    count()
    for x in range(len(MobNets)):
        try:
            MobNets[x]._MobNet__socket.send(str(__PYMOB_NET_VERSION__) + '\xFF' + communicator.get('species') + '\xFF'+ communicator.get('name') + '\xFF' + str(dst) + '\xFF' + repr(datetime.datetime.now()) + '\xFF' + str(cmd) + '\xFF' + str(prm) + '\n')
            pymob.debug.out("sent to " + str(dst))
        except:
            pymob.debug.out('error raised')

           
def quit():
    global mobnetl, MobNets, __running__
    __running__ = 0
    try:
        mobnetl._MobNet_Listener__socket.shutdown(socket.SHUT_RDWR)
        for x in range(len(MobNets)):
            MobNets[x]._MobNet__socket.shutdown(socket.SHUT_RDWR)
    except:
        pymob.debug.out('exception catched')
    pymob.debug.out('detaching from network.')

def search(lis):
    global hosts_range
    hosts_range = lis

def join(pmob, listener = True, searcher = True, debugging = False, search_split = 15):
    global mobnetl, __running__, communicator, hosts_range, __dbg
    pymob.debug.out('pymob.net debugging on', debugging)
    if __running__ == 1:
        pymob.debug.out('already joined the network.')
        return False
    __running__ = 1
    communicator = pmob
    pymob.debug.out(pmob.get('name') + ' is connecting to MobNet network.')
    del mobnetl
    if listener:
        mobnetl = MobNet_Listener()
        mobnetl.start()
    if searcher:
        hosts_tmp = hosts_range
        while len(hosts_tmp) != 0:
            mobnets = MobNet_Searcher(hosts_tmp[:search_split])
            mobnets.start()
            hosts_tmp = hosts_tmp[search_split:]

    return True
