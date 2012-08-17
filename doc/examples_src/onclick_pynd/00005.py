# monkeypatch method

p3 = Pynguin()

def p3onclick(self, x, y):
    self.goto(x, y)
    self.square(50, True)

import types
p3.onclick = types.MethodType(p3onclick, p3)
