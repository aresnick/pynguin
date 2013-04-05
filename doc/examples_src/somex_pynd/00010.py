def arcs():
    for r in range(20, 300, 20):
        arc(r, 120, True)
        lt(180)
        arc(r, 120, True)
        lt(90)
        arc(r+10, 120, True)
        lt(180)
        arc(r+10, 120, True)
        lt(90)
