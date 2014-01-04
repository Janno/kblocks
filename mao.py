from collections import defaultdict
from itertools import permutations

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

class MaoState(object):
    def __init__(self, g, L=None, V=None, hi=None):
        if not L:
            L = defaultdict(list)
            L[0].extend(g.nodes_iter()) 
        if not V:
            V = {v:(0, i) for i,v in enumerate(L[0])}
        if not hi:
            hi = 0
        self.g = g
        self.L = L 
        self.V = V
        self.hi = hi

    def copy(self):
        L_new = defaultdict(list)
        for k, l in self.L.iteritems():
            if l:
                L_new[k] = l[:]
        return MaoState(self.g, L_new, dict(self.V.iteritems()), self.hi)

    def update_hi(self):
        while not self.L[self.hi] and self.hi > 0:
            self.hi = self.hi - 1

    def push(self, u):
        for v in self.g[u]:
            # print '\tneighbour', v
            if not v in self.V:
                continue
            hp, tp = self.V[v]
            # print '\tposition', hp, tp
            # swap v last element in current list L[hp], if necessary
            self.movetoend(hp, tp)
            # append v to higher list
            self.V[v] = hp+1, len(self.L[hp+1])
            self.L[hp+1].append(v)
            self.hi = max(self.hi, hp+1)
            # delete old occurence of v which is now at the last index in L[hp]
            # print '\tdeleting from', hp
            self.L[hp].pop()
            # del self.L[hp][tp]

    def candidates(self):
        return xrange(len(self.L[self.hi]))

    def show(self):
        for hp in sorted(self.L.iterkeys(), reverse=True):
            print 'L', hp, self.L[hp]
        print 'V', self.V

    def swap(self, hp, tp1, tp2):
        v1, v2 = self.L[hp][tp1], self.L[hp][tp2]
        self.V[v1], self.V[v2] = self.V[v2], self.V[v1]
        self.L[hp][tp1], self.L[hp][tp2] = self.L[hp][tp2], self.L[hp][tp1]

    def movetoend(self, hp, tp):
        if tp < len(self.L[hp])-1:
            # print '\tswapping %s with last element in %s' % (tp, hp)
            self.swap(hp, tp, len(self.L[hp])-1)

    def step(self, i):
        self.movetoend(self.hi, i)
        v = self.L[self.hi].pop()
        del self.V[v]

        self.update_hi()

        # if we are not done we need to update L
        if self.L[self.hi]:
            self.push(v)
        return v

    def check(self):
        for hp, l in self.L.iteritems():
            for tp, v in enumerate(l):
                assert (hp, tp) == self.V[v], v

def all_maos(g):
    # list of pairs of ((partial) mao, state)
    if len(g) == 0:
        yield ()
    else: 
        todo = [((), MaoState(g)),]
        while todo:
            m, s = todo.pop()
            for c in s.candidates():
                s_ = s.copy()
                v = s_.step(c)
                m_ = m+(v,)
                if len(m_) == len(g):
                    yield m_ 
                else:
                    todo.append((m_, s_))
        
def all_maos_slow(g):
    for l in permutations(g.nodes_iter(), len(g)):
        if is_mao(g,l):
            yield l


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

    def show():
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
        # show() 
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

class Tree(object):
    def __init__(self, tag, children=None):
        if not children: 
            children = []
        self.tag = tag
        self.children = children
    def is_leaf(self):
        return len(self.children) == 0
    def paths(self):
        for c in self.children:
            for p in c.paths():
                yield (self.tag,) + p
        if not self.children:
            yield (self.tag,)
    def all_children(self):
        if tag:
            yield tag
        for c in self.children:
            for c_ in c.all_children():
                yield c_
    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self.tag, self.children)

def maotree(g, m):
    from networkx import Graph, connected_components
    from itertools import chain
    if len(m) == 0:
        return None

    T = Tree(None, [])
    # node -> index in mao
    o = dict((v,i) for i,v in enumerate(m))
    # list of edges (u,v) with o[u] <= o[v]
    e = [(u,v) if o[u] <= o[v] else (v,u) for u,v in g.edges()]
    # we sort e w.r.t. to o such that we can disregard the entire prefix
    # up to the first pair (u,v) with o[u] >= o[current node]
    e.sort(key=lambda (u,v): (o[u], o[v]))
    # todo is a tuple of the current tree node,
    # the remaining mao to process and
    # the offset of the edges to be considered in the
    # edge list e
    todo = [(T, m[:], 0)]
    while todo:
        t, m, i = todo.pop(0)
        x = m.pop(0)
        t.tag = x
        if not m:
            continue
        while i < len(e) and o[e[i][0]] <= o[x]:
            i = i+1
        g_ = Graph()
        for (u,v) in e[i:]:
            g_.add_edge(u,v)
        g_.add_nodes_from(m)
        cs = connected_components(g_)
        for c in cs:
            c.sort(key=o.get)
        t.children = [Tree(None, []) for c in cs]
        todo.extend(zip(t.children, cs, (i for c in cs)))
    return T


if __name__=='__main__':
    from networkx import parse_graph6
    from sys import stdin

    for l_ in stdin:
        l = l_.strip()
        g = parse_graph6(l)
        m1 = list(all_maos(g))
        m2 = list(all_maos_slow(g))
        m1.sort()
        m2.sort()
        if not set(m1) == set(m2):
            print l
            print len(m1)
            print len(m2)

