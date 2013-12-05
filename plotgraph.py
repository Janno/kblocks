#!/usr/bin/python
from networkx import parse_graph6, draw
import pylab as P


if __name__=='__main__':
    from sys import argv
    g = parse_graph6(argv[1])
    draw(g)
    P.draw()
    P.show()
