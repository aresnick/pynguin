def c(pyn):
    '''Use pyn to make a circle.
    Watches the kill_threads()
    mechanism to know when to stop.

    To start this running in a
    separate thread, use this:

    p4 = Pynguin()
    trun(p4, c, p4)

    You should get your cursor back
    almost immediately, so that you
    can carry on with other commands.

    To stop the action, use
    kill_threads()
    '''

    import threading
    ts = threading.threads
    while ts[pyn]:
        pyn.fd(1)
        pyn.rt(1)
