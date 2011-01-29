import datetime
import pymob

def save(pmob, path):
    try:
        f = open(path, 'w')
        f.write(pmob.serialize())
        f.close()
    except:
        return False
    return True

def load(path):
    try:
        f = open(path, 'r')
        fr = f.read()
        f.close()
    except:
        raise "file error"
    t = pymob.pymob()    
    t.config = eval(fr)
    return t
