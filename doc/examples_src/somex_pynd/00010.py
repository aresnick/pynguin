def arcs():
    for r in range(20, 300, 10):
        arc(r, 120, True)
        lt(180)
        arc(r+5, 120, True)
        lt(90)
