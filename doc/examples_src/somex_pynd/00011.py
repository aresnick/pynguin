def arcs2():
    for r in range(20, 300, 20):
        arc(r, 120, center=True, move=False)
        lt(180)
        arc(r, 120, True, move=False)
        lt(90)
        arc(r+10, 120, True, move=False)
        lt(180)
        arc(r+10, 120, True, move=False)
        lt(90)
