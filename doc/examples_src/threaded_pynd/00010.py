def slash(pyn, n):
    '''Use pyn to create a slash
    pattern.

    Cooperates with the kill_threads()
    mechanism by watching to see if it
    has been asked to stop, and also by
    indicating when it is finished
    working by setting
    threading.threads[pyn] = 0
    '''

    import threading
    ts = threading.threads

    for s in range(n):
        if not ts[pyn]:
            break
        pyn.goto('random')
        pyn.fd(100)
        pyn.lt(360./n)

    ts[pyn] = 0
