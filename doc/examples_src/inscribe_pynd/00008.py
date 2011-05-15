def tris(eq, n):
    x0, x1, x2 = tri(eq, 0)
    points = []
    for x in domain(x0+(x2-x0)/float(n), x2, (x2-x0)/float(n)):
        tri(eq, x)
        y = eq(x)
        if y is not None:
            points.append((round(x, 5), y))
    return points
