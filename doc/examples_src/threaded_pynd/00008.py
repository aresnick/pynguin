def burster(n, center=False):
    '''Create n pynguins, then use
    all available pynguins to create
    a multicolored starburst pattern.

    Stop the action with the
    kill_threads() function.
    '''

    make(n)

    if not center:
        goto('random')
        x, y = xy()
    else:
        x, y = 0, 0

    for pyn in pynguins:
        trun(pyn, burst, pyn, x, y)
