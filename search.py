from networkx.generators.random_graphs import gnm_random_graph
from networkx.algorithms import local_node_connectivity, node_connectivity, triangles
from networkx.linalg import adjacency_matrix
from networkx.readwrite import read_graph6_list, parse_graph6
from itertools import combinations, imap
from subprocess import Popen, PIPE
from multiprocessing import Pool



def get_triangles(g):
    for n1 in g:
        neighbors1 = set(g[n1])
        for n2 in filter(lambda x: x>n1, neighbors1):
            neighbors2 = set(g[n2])
            common = neighbors1 & neighbors2
            for n3 in filter(lambda x: x>n2, common):
                yield n1,n2,n3

def gen(n,m):
    return gnm_random_graph(n,m)

def has_triangles(g):
    return trace(adjacency_matrix(g)**3) > 1e-10

from random import choice
def remove_triangles(g, triangles=None):
    c = g.copy()
    while True:
        has_triangles = False
        for (n1, n2, n3) in triangles if triangles else get_triangles(c):
            has_triangles = True
            candidates = [n1, n2, n3]
            d1 = choice(candidates)
            candidates.remove(d1)
            d2 = choice(candidates)
            c.remove_edge(d1,d2)
            # print 'removing edge %s %s' % (n1, n2)
            break
        if not has_triangles:
            return c


def mao(graph, s):
    from collections import defaultdict
    m = [s]
    # mimic linked list of linked lists (outer layer is lazy)
    L = defaultdict(list)
    # initialize L according to number of edges to s
    L[0].extend(filter(lambda v: v!=s, graph.nodes_iter()))
    # 2d index of every node in L, initialized in accordance with L
    V = {v:(0, i) for i,v in enumerate(L[0])}
    # helper functions
    h = lambda v: V[v][0]
    t = lambda v: V[v][1]

    def showL():
        for hp in sorted(L.iterkeys(), reverse=True):
            print hp, L[hp]
    
    def push(u):
        # print 'pushing', u
        hi_new = 0 
        for v in sorted(graph[u], key=V.get, reverse=True):
            # print '\tneighbour', v
            if not v in V:
                continue
            hp, tp = V[v]
            hi_new = max(hi_new, hp+1)
            # swap v last element in current list L[hp], if necessary
            if tp < len(L[hp])-1:
                v_last = L[hp][-1]
                V[v_last] = (hp, tp) 
                L[hp][tp], L[hp][-1] = L[hp][-1], L[hp][tp]
                tp = len(L[hp])-1 
            # append v to higher list
            V[v] = hp+1, len(L[hp+1])
            L[hp+1].append(v)
            # delete old occurence of v which is now at the last index in L[hp]
            del L[hp][tp]
        # showL() 
        # print V
        return hi_new
    # transfer all nodes with edges to s to L[1]
    push(s)

    # keeping track of highest non-empty list in L
    hi = 1
    def update_hi(hi):
        while not L[hi] and hi > 0:
            hi = hi - 1
        return hi

    while len(m) < len(graph):
        v = L[hi].pop() 
        del V[v]
        m.append(v)

        hi = update_hi(hi)


        # see if we are done
        if not L[hi]:
            assert len(m) == len(graph)
            break 
        else:
            hi_new = push(v)
            hi = max(hi, hi_new)

    return m

def is_mao(g, s, m):
    # necessary, not sufficient
    for i, v in enumerate(m):
        prev = set(m[:i])
        v_edges = prev.intersection(g[v].viewkeys())
        for u in m[i+1:]:
            if prev.intersection(g[u].viewkeys()) > v_edges:
                return False
    return True



def unweighted_ma_ordering(graph, s):
    """Return a maximum adjacency ordering of the nodes, starting with s. Every edge is assumed to have weight 1.
       This function takes O(n+m) time."""
    queue = [[s]]
    r = dict((v,0) for v in graph.nodes_iter())
    seen = set()
    for i in xrange(len(graph)):
        v = None
        while v == None or v in seen:
            v = queue[-1].pop()
            if queue[-1] == []: queue.pop()
        seen.add(v)
        assert v != None
        yield v
        #if v in graph.nodes():
        for u, edges in graph[v].iteritems():
            r[u] = r[u] + len(edges)
            while len(queue) <= r[u]: 
                queue.append([])
            queue[r[u]].append(u)

def read_graph6_iter(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield parse_graph6(line)

def certify_non_kblock(g, block, k):
    for u,v in combinations(block, 2):
        if g.has_edge(u,v):
            continue
        k_ = local_node_connectivity(g, u, v)
        if k_ < k:
            return u,v,k_

def mao_kblock(g, k, s):
    o = mao(g, s)
    # assert is_mao(g, s, o)
    candidate = o[-(k+1)::]
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
    # d >= 3k/2
    # or d > 3k/2 - 1
    k = int(2 * (d / 3.0))
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

def task(geng_params, nrange, f, P=None):
    if not P:
        P = Pool()
    for n in nrange:
        print ' '*20,
        print '\rn=%d' % n,
        p = Popen(['geng',] + geng_params + ['%d' % n], stdout=PIPE, stderr=open('/dev/null', 'w'))
        #with open("/tmp/graph%s" % n, 'r') as f:
        s = 2**(n/2)
        for i, o in enumerate(P.imap_unordered(f, imap(str.strip, p.stdout), chunksize=s)):
            if o:
                print
                print o
            if i % s == 0:
                print 'n=%d, %d%s\r' % (n, i, ' '*20),

def main(argv):
    # Verm2
    # task(['-Ct', '-d2'], xrange(1,14), single_all_mao_kp1b)

    # Verm4
    # task(['-C', '-d2'], xrange(1,14), single_kb1p32)

    # [Verm5] Bilden die letzten k+1 Knoten einer jeden MAO eines Graphen mit
    # Minimalgrad > 3k/2 -1 einen (k+1)-block?
    # task(['-C', '-d2'], xrange(1,14), single_mao_kb1p32)

    # [Verm6] Gibt es für jeden Graphen mit Minimalgrad > 3k/2 -1 eine MAO
    # deren letzten k+1 Knoten einen (k+1)-block bilden?
    # task(['-C', '-d2'], xrange(1,14), single_maos_kb1p32)

    # [Verm7] Verm5 wenn der Graph zusätzlich k-connected ist

    # [Verm8] Verm6 wenn der Graph zusätzlich k-connected ist
    task(['-C', '-d2'], xrange(1,14), single_maos_connected_kb1p32)


    

if __name__ == '__main__':
    from sys import argv
    main(argv)
