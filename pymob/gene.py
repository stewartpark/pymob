import random

MAX_GENE_CODE = 10240

def __new_one_gene():
    return str(random.randrange(10))    

def generate():
    gene_code = ''
    for x in range(MAX_GENE_CODE):
        gene_code = gene_code + __new_one_gene()
    return gene_code

def clone(old):
    new = list(old)
    for x in range(random.randrange(len(old))):
        i = random.randrange(len(old))
        new[i] = __new_one_gene()
    return "".join(new)
