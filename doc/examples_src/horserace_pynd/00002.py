def setup():
    horses = make_horses()

    startline(horses)
    draw_track()

    # wait for track to
    # finish drawing ...
    import time
    for count in range(3, 0, -1):
        print(count)
        time.sleep(1)
    print('go!')

    return horses
