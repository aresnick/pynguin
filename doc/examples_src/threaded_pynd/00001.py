def trun(fname, *args):
    import threading
    for p in pynguins:
        f = getattr(p, fname)
        t = threading.Thread(target=f, args=args)
        t.run()
