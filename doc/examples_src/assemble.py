import os

def make_pyn(ex):
    os.chdir(ex)
    history = open('@@history@@', 'w')
    history.close()

    if ex.endswith('_pynd'):
        exfile = '%s.pyn' % ex[:-5]
    else:
        exfile = '%s.pyn' % ex

    if os.path.exists(exfile):
        os.remove(exfile)
    cmd = 'zip -r %s *' % exfile
    os.system(cmd)

    os.chdir('..')

    fromfile = '%s/%s' % (ex, exfile)
    tofile = '../examples/%s' % exfile
    os.rename(fromfile, tofile)

def make_all():
    dirs = get_ex_dirs()
    for ex in dirs:
        make_pyn(ex)

def cleanup():
    dirs = get_ex_dirs()
    for ex in dirs:
        files = os.listdir(ex)
        for f in files:
            if f.startswith('##'):
                n = f[2:7]
                fpf = os.path.join(ex, f)
                fpt = os.path.join(ex, n + '.py')
                os.rename(fpf, fpt)

        if not ex.endswith('_pynd'):
            os.rename(ex, ex+'_pynd')

def get_ex_dirs():
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    return dirs

if __name__ == '__main__':
    import sys
    if len(sys.argv)==1:
        make_all()
    elif '-C' in sys.argv:
        cleanup()
