def arun(cmdname, *args):
    '''Have all pynguins run the named
    command, each in its own separate
    thread. Any dditional arguments will
    be passed on to the command.
    '''

    for pyn in pynguins:
        cmd = getattr(pyn, cmdname)
        trun(pyn, cmd, *args)

    kill_threads()
