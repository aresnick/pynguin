def caught(pyn, fpyn):
    fx, fy = fpyn.xy()
    return pyn.distance(fx, fy) <= 1
