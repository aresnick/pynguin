def follow(pyn, fpyn):
    '''Have pyn move towards
    fpyn 1 small step at a time.
    '''

    import threading
    ts = threading.threads

    while ts[pyn]:
        x, y = fpyn.xy()
        pyn.toward(x, y)
        pyn.fd(1)
