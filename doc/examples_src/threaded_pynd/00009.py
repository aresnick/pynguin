def slasher(n, slashes=6):
    '''Create n pynguins, then use
    all available pynguins to
    make a slash pattern.
    '''

    make(n)

    for pyn in pynguins:
        trun(pyn, slash, pyn, slashes)
