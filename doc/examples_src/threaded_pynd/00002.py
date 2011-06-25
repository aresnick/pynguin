def kill_thread(pyn):
    '''Signal the thread being used
    by Pynguin pyn that it should
    stop work.

    Threaded commands must cooperate
    by watching for this signal and
    doing the right thing.
    '''

    import threading
    ts = threading.threads
    ts[pyn] = 0
