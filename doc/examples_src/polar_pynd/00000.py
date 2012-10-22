def show_all():
    mode('pynguin')
    notrack()

    import time

    xmin, ymin, xmax, ymax = viewcoords()
    funcs = sorted(list(globals().keys()))
    for fname in funcs:
        if fname.startswith('eq'):
            clear()
            f = globals().get(fname)
            doc = f.__doc__
            doclines = doc.split('\n')
            thmax = None
            if len(doclines)>1:
                line2 = doclines[1].strip()
                if line2.startswith('thmax'):
                    thmaxstr = line2[7:]
                    thmax = eval(thmaxstr)
            grid()
            axis()
            color('rdark')
            if thmax is None:
                plot(f)
            else:
                plot(f, thmax)
            label(f)
            goto(xmax-50, ymin+50)
            time.sleep(5)
