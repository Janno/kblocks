from collections import defaultdict

def is_mao(g, m):
    if len(m) < len(g):
        return False
    for i, v in enumerate(m):
        prev = set(m[:i])
        v_edges = prev.intersection(g[v].viewkeys())
        for u in m[i+1:]:
            if len(prev.intersection(g[u].viewkeys())) > len(v_edges):
                return False
    return True

def mao(graph, s):
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
