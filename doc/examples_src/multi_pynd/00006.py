def acmd(cmdname, *args, **kw):
    for pyn in pynguins:
        cmd = getattr(pyn, cmdname)
        cmd(*args, **kw)
