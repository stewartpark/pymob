import pymob.gene
import pymob.net
import pymob.file
import pymob.debug

import threading
import datetime


__PYMOB_VERSION__ = 0.01

__CASE_ENABLED__ = True

class __pymob_case_launcher(threading.Thread):
    def __init__(self, self2, case):
        threading.Thread.__init__(self)
        self.case = case
        self.self2 = self2
    def run(self):
        global __CASE_ENABLED__
        while __CASE_ENABLED__:
            self.case(self.self2)

class pymob(object):
    
    #default class implementations
    def __init__(self, debugging=True):
        self.config = {}
        self.gene_tagging = {}
        self.cases = {}
        debug.out('pymob debugging on', debugging)
    def __repr__(self):
        return str(self.config)    
    def __str__(self):
        return str(self.config)


    #config methods
    def set(self, key, value):
        self.config[key] = value
    def get(self, key):
        return self.config[key]

            
    #gene tagging
    def tagging(self, gene_idx, tag, length=1):
        if length >= 1:
            debug.out('gene tagging: ' + tag + ':' + str(gene_idx) + ':' + str(length) + '=' + self.config['gene'][gene_idx:gene_idx+length])
            self.gene_tagging[tag] = (gene_idx, length)
        else:
            raise "gene tag length is invalid."

    def gene(self, tag):
        g = self.gene_tagging[tag]
        gene_code = self.config['gene'][g[0]:g[0]+g[1]]
        return int(gene_code)

    #serialize self
    def serialize(self):
        return repr(self)

    #mapping fundamental informations
    def mapping(self, species, gene, name='', birth=datetime.datetime.now()):
        self.set('species', species)
        if name == '':
            name = species + gene[:12]
        self.set('name', name)
        self.set('birth', birth)    
        self.set('gene', gene)

    #make decision case
    def disable_auto_case(self):
        global __CASE_ENABLED__
        __CASE_ENABLED__ = False
        
    def add_case(self, dname, func, auto=False):
        self.cases[dname] = func
        if auto:
            __pymob_case_launcher(self, func).start()   

    def case(self, dname):
        return self.cases[dname](self)
