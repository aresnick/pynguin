def angs(n=10, quiet=False):
    '''Show that a triangle inscribed
        in a semicircle is a right
        triangle.

    Draw n triangles inscribed
        in a semicircle.

    For each triangle, find the slopes
        of both of the non-diameter sides
        of the triangle, then check that
        those lines are perpendicular by
        checking that the slopes are
        negative reciprocals of each other.

    if quiet == True, only show a message
        if a triangle is found that
        is not a right triangle.
    '''

    mode('pynguin')
    reset()

    grid()
    axes()
    plot(sc)

    points = tris(sc, n)
    x0, x1, x2 = tri(sc, 0)
    y0 = y2 = 0

    for x1, y1 in points:
        if x1 != x0:
            s01 = round((y1-y0)/(x1-x0), 9)
        else:
            s01 = None

        if x2 != x1:
            s12 = (y2-y1)/(x2-x1)
        else:
            s12 = None

        if s12 != 0 and s12 is not None:
            s12nr = round(-1/s12, 9)
        elif s12 is None:
            s12nr = 0
        else:
            s12nr = None

        if s01 == s12nr:
            if not quiet:
                print('%.3f == %.3f (%s)' % (s01, s12nr, s01==s12nr))
        else:
            # this should never happen!
            print('**** ** **** *****')
            print('%.3f != %.3f' % (s01, s12nr))
            print('**** ** **** *****')
            print()
