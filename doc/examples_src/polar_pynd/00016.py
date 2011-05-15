def label(f):
    xmin, ymin, xmax, ymax = viewcoords()
    goto(xmin+20,ymin+20)
    turnto(0)
    color('white')
    doc = f.__doc__
    lines = doc.split('\n')
    l = lines[0]
    write(l)
    if len(lines) > 1:
        line2 = lines[1].strip()
        if line2.startswith('thmax'):
            thmaxstr = line2[7:].replace('*', ' ')
            goto(xmin+20,ymin+60)
            write('0 < th < %s' % thmaxstr)
