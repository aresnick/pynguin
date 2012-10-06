def trun(pyn, cmd, *args):
    '''run a command in a thread.

    Pass in the pynguin that will
    be performing the action as
    the first argument. That will
    be used to track which pynguins
    are already busy working and
    allow their threads to be stopped
    later using the kill_threads()
    function.
    '''

    if hasattr(pyn, '_is_helper') and pyn._is_helper:
        return 'Use primary pynguin, not helper.'

    import threading

    busy = threading.threads.get(pyn, False)
    if busy:
        return 'Pynguin %s busy. Try again later.' % pyn

    t = threading.Thread(target=cmd, args=args)
    threading.threads[pyn] = 1
    t.start()
