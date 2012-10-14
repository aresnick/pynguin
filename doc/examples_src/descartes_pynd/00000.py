def show_all():
    mode('pynguin')

    import time

    home()
    notrack()

    xmin, ymin, xmax, ymax = viewcoords()

    funcs = sorted(list(globals().keys()))
    for fname in funcs:
        if fname.startswith('eq'):
            f = globals().get(fname)

            clear()
            home()

            grid()
            axes()

            color('rdark')
            plot(f)
            label(f)
            goto(xmax-50, ymin+50)

            time.sleep(5)
