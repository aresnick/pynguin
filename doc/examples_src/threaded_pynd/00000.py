def make(n):
    '''Create n new pynguins,
    and set up for the ability
    to kill active threads later
    using the kill_threads()
    function.

    Note: If you already have some
    pynguins that you want to run
    threaded commands with, you can
    call make(0) in order to set up
    the thread kill mechanism.

    Note also that the examples in
    this file use a threaded style.
    For a different approach, see
    the examples in the multi.pyn
    example file.
    '''

    import threading
    try:
        threading.threads
    except AttributeError:
        threading.threads = {}

    for i in range(n):
        Pynguin()
