def show_all():
    import time
    xmin, ymin, xmax, ymax = viewcoords()
    funcs = globals().keys()
    funcs.sort()
    for fname in funcs:
        if fname.startswith('eq'):
            clear()
            f = globals().get(fname)
            grid()
            axes()
            color('rdark')
            plot(f)
            label(f)
            goto(xmax-50, ymin+50)
            time.sleep(5)
