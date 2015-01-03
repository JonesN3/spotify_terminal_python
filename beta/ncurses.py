#!/bin/env python
import curses

# initialize
stdscr = curses.initscr()
# no automatically print input to screen
curses.noecho()
# no need for enter
curses.cbreak()
# for special keys
stdscr.keypad(1)

def printDocument(): 
	print("document")

while 1: 
    c = stdscr.getch()
    if c == ord('p'):
        printDocument()
    elif c == ord('q'):
        break  # Exit the while()
    elif c == curses.KEY_HOME:
        x = y = 0

#terminate
curses.nocbreak(); stdscr.keypad(0); curses.echo()
curses.endwin()

