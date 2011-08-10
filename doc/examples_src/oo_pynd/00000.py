class ZZ(Pynguin):
    '''A pynguin that draws in circles instead of straight lines
    '''

    def __init__(self, csize=12):
        Pynguin.__init__(self)
        self._csize = csize

    def cfd(self, d):
        r = self._csize / 2.0
        pen = self.pen
        while d > 0:
            Pynguin.circle(self, r, True)
            self.penup()
            Pynguin.fd(self, 2*r)
            d -= 2*r
            if pen:
                self.pendown()

    def forward(self, d):
        self.cfd(d)
    fd = forward

    def circle(self, r, center=False):
        if center:
            pen = self.pen
            self.penup()
            self.fd(r)
            self.rt(90)
            if pen:
                self.pendown()
            self.circle(r)
            self.penup()
            self.rt(90)
            self.fd(r)
            self.lt(180)
            if pen:
                self.pendown()
            return

        ox, oy = self.xy()
        oa = self.ritem.ang

        if r < 0:
            direction = 1
            r = -r
        else:
            direction = 0

        circ = 2*PI*r
        arc = self._csize
        steps = circ / arc
        angle = 360.0 / steps

        # correct for distortion
        if direction:
            self.lt(angle/2)
        else:
            self.rt(angle/2)

        for s in range(int(steps)):
            self.fd(arc)
            if direction:
                self.lt(angle)
            else:
                self.rt(angle)

        # correct for distortion
        if direction:
            self.rt(angle/2)
        else:
            self.lt(angle/2)

        self.goto(ox, oy)
        self.turnto(oa)
