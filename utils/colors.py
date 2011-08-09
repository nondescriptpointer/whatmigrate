def color(t, c):
        return chr(0x1b)+"["+str(c)+"m"+t+chr(0x1b)+"[0m"
def black(t):
        return color(t, 30)
def red(t):
        return color(t, 31)
def green(t):
        return color(t, 32)
def yellow(t):
        return color(t, 33)
def blue(t):
        return color(t, 34)
def mangenta(t):
        return color(t, 35)
def cyan(t):
        return color(t, 36)
def white(t):
        return color(t, 37)
def bold(t):
        return color(t, 1)
