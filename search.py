"""Usage: search.py [-p]

Options:
    -p, --progress      Print absolute progress about once every 5 seconds
    -h, --help          Show this
"""
from networkx.generators.random_graphs import gnm_random_graph
from networkx.algorithms import local_node_connectivity, node_connectivity, triangles
from networkx.linalg import adjacency_matrix
from networkx.readwrite import read_graph6_list, parse_graph6
from docopt import docopt
from itertools import permutations, combinations
from math import ceil

from mao import mao, is_mao


def certify_non_kblock(g, block, k):
    for u,v in combinations(block, 2):
        if g.has_edge(u,v):
            continue
        k_ = local_node_connectivity(g, u, v)
        if k_ < k:
            return u,v,k_

def mao_kblock(g, k, s):
    o = mao(g, s)
    # assert is_mao(g, o)
    candidate = o[-(k)::]
    # assert len(kp1_block) == k+1
    result = certify_non_kblock(g, candidate, k=k)
    if result:
        u,v,k_ = result
        return {'mao':o, 'u':u, 'v':v, 'k_':k_}

# Verm1
def single_mao_kp1b(g6):
    """ [Verm1] """
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= k+1, take maximal k
    k = d-1
    s = g.nodes_iter().next()
    result = mao_kblock(g, k+1, s)
    if result:
        result['g'] = g6
        result['k'] = k
        result['d'] = d
        return result
# Verm2
def single_all_mao_kp1b(g6):
    """ [Verm2] """
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= k+1, take maximal k
    k = d-1
    starters = []
    for s in g.nodes_iter():
        result = mao_kblock(g, k+1, s)
        # result = None if it is indeed a MAO
        if not result:
            starters.append(s)
            # we found one, let's skip ahead
            break
    if not starters:
        return {'g':g6, 'd':d, 'k':k}

# Verm2, try ALL maos in a stupid way
def single_ALL_mao_kp1b(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= k+1, take maximal k
    k = d-1
    if k < 2:
        return
    last = None
    for l in permutations(g.nodes_iter(), len(g)):
        if is_mao(g,l):
            last = l
            if not certify_non_kblock(g, l[-(k+1):], k+1):
                return 
    return {'g': g6, 'd': d, 'k': k, 'last': last}


# Try any mao but try all k+1-long sub sequences
def single_mao_all_kp1b(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= k+1, take maximal k
    k = d-1
    s = g.nodes_iter().next()
    m = mao(g, s)
    for i in xrange(0, len(g)-(k+1)):
        result = certify_non_kblock(g, m[i:i+k+1], k+1)
        if not result:
            return
    # all are non-k+1-blocks 
    result['g'] = g6
    result['k'] = k
    result['d'] = d
    return result

    
# Verm3
def single_kp1b(g6):
    """ [Verm3] """
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= k+1, take maximal k
    k = d-1
    def chk():
        for candidates in combinations(g.nodes_iter(),k+1):
            if not certify_non_kblock(g, candidates, k+1):
                return True
        return False

    if not chk():     
        return {'g':g6, 'd': d, 'k': k}

# Verm4
def single_kb1p32(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= 3k/2
    # or d > 3k/2 - 1
    k = int(2 * (d / 3.0))
    if node_connectivity(g) >= k:
    	return
    def chk():
        for candidates in combinations(g.nodes_iter(),k+1):
            if not certify_non_kblock(g, candidates, k+1):
                return True
        return False

    if not chk():     
        return {'g':g6, 'k': k, 'd': d}

# Verm5
def single_mao_kb1p32(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # or d > 3k/2 - 1
    k = int(ceil(2 * ((d+1) / 3.0)) - 1)
    result = mao_kblock(g, k+1, g.nodes_iter().next())
    if result:
        result['g'] = g6
        result['k'] = k
        result['d'] = d
        return result
# Verm6
def single_maos_kb1p32(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= 3k/2
    # or d > 3k/2 - 1
    k = int(2 * (d / 3.0))
    starters = []
    for s in g.nodes_iter():
        result = mao_kblock(g, k+1, s)
        # result = None if it is indeed a MAO
        if not result:
            starters.append(s)
            # we found one, let's skip ahead
            break
    if not starters:
        return {'g':g6, 'd':d, 'k':k}

# Verm8    
def single_maos_connected_kb1p32(g6):
    g = parse_graph6(g6)
    d = min(g.degree().viewvalues())
    # d >= 3k/2
    # or d > 3k/2 - 1
    k = int(2 * (d / 3.0))
    if node_connectivity(g) < k+1:
        return
    starters = []
    for s in g.nodes_iter():
        result = mao_kblock(g, k+1, s)
        # result = None if it is indeed a MAO
        if not result:
            starters.append(s)
            # we found one, let's skip ahead
            break
    if not starters:
        return {'g':g6, 'd':d, 'k':k}

def main(argv):
    from sys import stdin
    opts = docopt(__doc__, argv=argv)

    from time import clock
    t = clock()
    p = opts['--progress']
    for i, g6_ in enumerate(stdin):
        g6 = g6_.strip()
        x = single_ALL_mao_kp1b(g6)
        if x:
            print x
        if p and clock()-t > 5:
            t = clock()
            print '\r', i,
    print '\r', i

    

if __name__ == '__main__':
    from sys import argv
    main(argv[1:])
