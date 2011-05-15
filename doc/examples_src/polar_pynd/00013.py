def domain(start, end, step):
    th = start
    yield th
    while th < end:
        th += step
        yield th
