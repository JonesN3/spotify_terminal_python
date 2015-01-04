#!/usr/bin/env python 
from curses import *

setupterm()
cols = int(tigetnum("cols"))
lines = int(tigetnum("lines"))
print(cols, lines)
