def cmdall(cmdname, *args, **kw):
    #import threading
    for pyn in pynguins:
        cmd = getattr(pyn, cmdname)
        cmd(*args, **kw)
        #thr = threading.Thread(target=cmd, args=args, kwargs=kw)
        #thr.start()
