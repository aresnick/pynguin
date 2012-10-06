def arun(cmdname, *args):
    '''Have all pynguins run the named
    command, each in its own separate
    thread. Any additional arguments will
    be passed on to the command.

    cmdname should be a string naming the
    command to be run.

    Looks first to see if cmdname is the name
    of a method of a pynguin, and if not it
    looks for a function with that name in the
    global namespace. For the function to work
    properly, it should take a pynguin as its
    first argument.
    '''

    for pyn in pynguins:
        if hasattr(pyn, '_is_helper') and pyn._is_helper:
            continue

        try:
            cmd = getattr(pyn, cmdname)
            trun(pyn, cmd, *args)
        except AttributeError:
            cmd = globals().get(cmdname, None)
            if cmd is None:
                continue
            trun(pyn, cmd, pyn, *args)
            

def arun_k(cmdname, *args):
    '''if running a command that you know will finish
    quickly, arun_k will clear the threads list after
    starting the command running.
    '''
    arun(cmdname, *args)
    kill_threads()
