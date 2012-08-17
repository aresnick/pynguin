def bugs(auto=True):
    '''Create 4 pynguins at the
    corners of the screen and have
    each one follow the one at the
    next corner over.

    with auto=True (the default)
    the chase will stop automatically
    when every pynguin has caught
    the one it is following.

    To stop the action if you choose
    to go with auto=False use the
    kill_threads() function manually.

    Note that the shapes produced
    are not the perfect curves that
    might be expected due to the fact
    that some threads might run longer
    or more often than others.

    For another way to do this that
    produces more regular and more
    repeatable results, see the bugs()
    example in the multi.pyn example
    file.
    '''

    make(0)
    reap()
    clear()

    p1 = p
    p1.avatar('pynguin')
    p2 = Pynguin()
    p2.avatar('arrow')
    p3 = Pynguin()
    p3.avatar('robot')
    p4 = Pynguin()
    p4.avatar('turtle')

    xn, yn, xx, yx = viewcoords()

    p1.goto(xn, yn)
    p2.goto(xn, -yn)
    p3.goto(-xn, -yn)
    p4.goto(-xn, yn)

    trun(p1, follow, p1, p2)
    trun(p2, follow, p2, p3)
    trun(p3, follow, p3, p4)
    trun(p4, follow, p4, p1)

    if not auto:
        return

    while True:
        if not caught(p1, p2):
            continue
        elif not caught(p2, p3):
            continue
        elif not caught(p3, p4):
            continue
        elif not caught(p4, p1):
            continue
        else:
            kill_threads()
            break
