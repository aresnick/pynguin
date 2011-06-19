def kill_threads():
    '''Signal running threads that
    they should stop working.

    Threaded commands must cooperate
    by watching for this signal and
    doing the right thing.
    '''

    import threading
    for pyn in threading.threads:
        threading.threads[pyn] = 0
