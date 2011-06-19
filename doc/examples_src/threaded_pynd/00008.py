def burst(pyn, x, y):
    '''Use pyn to create a starburst
    pattern. Watches the kill_threads
    mechanism to know when to stop.
    '''

    pyn.color('random')
    pyn.goto('random')
    pyn.toward(x, y)

    import threading
    ts = threading.threads

    while ts[pyn]:
        pyn.fd(10)
        if not pyn.onscreen():
            pyn.goto('random')
            pyn.toward(x, y)
