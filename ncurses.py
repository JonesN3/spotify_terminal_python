#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
## TODO
# Event loop is probably not working properly
#

# ncurses imports
import curses 
import curses.textpad
from curses import tigetnum

# spotify imports
import spotify

# other imports
import logging
import threading
import cmd
import random
from collections import deque

# for debugging
import sys
import traceback

# Logging
logging.basicConfig(filename='spotify.log',level=logging.DEBUG)
logging.info("## Start of log ##")

# initiate ncureses
screen = curses.initscr()   

randommode = 0
play_queue = deque ([])

# create the spotify session
session = spotify.Session()

# so whe can manage the state for these callbacks
logged_in = threading.Event()
logged_out = threading.Event()
end_of_track = threading.Event()

# set logged_out and end_of_track to true
logged_out.set()
end_of_track.set()

#logger = logging.getLogger('shell.commander')

#global init
container_root = session.playlist_container

# ncurses windows
# newwin(height, length, y, x)
def maketextbox(h,w,y,x,value="",deco=None,textColorpair=0,decoColorpair=0):
    # thanks to http://stackoverflow.com/a/5326195/8482 for this
    nw = curses.newwin(h,w,y,x)
    txtbox = curses.textpad.Textbox(nw,insert_mode=True)
    if deco=="frame":
        screen.attron(decoColorpair)
        curses.textpad.rectangle(screen,y-1,x-1,y+h,x+w)
        screen.attroff(decoColorpair)
    elif deco=="underline":
        screen.hline(y+1,x,underlineChr,w,decoColorpair)

    nw.addstr(0,0,value,textColorpair)
    nw.attron(textColorpair)
    screen.refresh()
    return nw,txtbox

def now_playing_window():
    cols = tigetnum("cols")
    lines = tigetnum("lines")

    window = curses.newwin(5, cols, lines-5, 0)
    window.addstr(1, 2, "Nothing playing", 0)
    window.addstr(1, 2, "", 0)
    window.addstr(2, 2, "", 0)
    window.box()
    screen.refresh()
    window.refresh()
    return window

def list_window():
    cols = tigetnum("cols")
    lines = tigetnum("lines")

    # lines-10: 5 from bottom, and 5 space for now_playing box
    window = curses.newwin(lines-10, cols, 5, 0)

    window.addstr(1, 2, "Nothing done", 0)
    window.addstr(1, 2, "", 0)
    window.addstr(2, 2, "", 0)
    window.box()
    screen.refresh()
    window.refresh()
    return window

def list_info_window():
    cols = tigetnum("cols")
    lines = tigetnum("lines")

    # one above the list_window
    window = curses.newwin(1, cols, 4, 0)
    window.addstr(0, 0, "Nothing done", 0)
    screen.refresh()
    window.refresh()
    return window

def commnder_info():
    cols = tigetnum("cols")
    lines = tigetnum("lines")

    # one above the list_window
    window = curses.newwin(1, cols, 0, 0)
    window.addstr(0, 0, "Enter command", 0)
    screen.refresh()
    window.refresh()
    return window

def debug_window():
    cols = tigetnum("cols")
    lines = tigetnum("lines")

    # one above the list_window
    window = curses.newwin(5, cols//2, 0, cols//2)
    window.addstr(0, 0, "Debug", 0)
    window.box()
    screen.refresh()
    window.refresh()
    return window

# ncurses window functions
def update_lwi(msg):
    lwi.clear()
    lwi.addstr(0,0, msg, 0)
    lwi.refresh()

def update_ci(msg):
    ci.clear()
    ci.addstr(0, 0, msg, 0)
    ci.refresh()

def reset_ci():
    update_ci("Enter command")

def livebug(msg):
    debug_window.clear()
    debug_window.addstr(1,1,msg,0)
    debug_window.box()
    debug_window.refresh()
    pass

def livebug2(msg):
    debug_window.clear()
    debug_window.addstr(2,1,msg,0)
    debug_window.box()
    debug_window.refresh()

# Create windows, for global accesss
np = now_playing_window()
lw = list_window()
lwi = list_info_window()
ci = commnder_info()
#debug_window = debug_window()
textwin,textbox = maketextbox(1,40, 1,1,"")

# spotify API calls spesific
def on_connection_state_changed(session):
    if session.connection.state is spotify.ConnectionState.LOGGED_IN:
        # set the user login states
        logged_in.set()
        logged_out.clear()

        # once logged in, load the users playlistcontainer
        load_root_container()

    elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
        # log out properly when logout callback returns
        logged_in.clear()
        logged_out.set()

def on_end_of_track(session):
    #logger.info("End of track")
    session.player.play(False)
    end_of_track.set()
    go_next()

def load_root_container():
    container_root = session.playlist_container
    container_root.load()


# functional methods
def play(track):
    track.load()
    session.player.load(track)
    session.player.play()
    end_of_track.clear()

    cols = int(tigetnum("cols"))
    lines = int(tigetnum("lines"))

    # cols = int(cols/2)

    # ncurses
    np.clear()
    np.addstr(1, (cols-len(track.artists[0].name))//2, track.artists[0].name.encode('utf-8'), 0)
    np.addstr(2, (cols-len(track.name))//2, track.name.encode('utf-8'), 0)
    np.addstr(3, (cols-len(track.album.name))//2, track.album.name.encode('utf-8'), 0)
    np.box()
    np.refresh()
    #screen.refresh()

# jump to next song i queue
def go_next():
    if(len(play_queue) > 0):
        play(play_queue.popleft())
    else:
        pass

def print_queue():
    window_max= lw.getmaxyx()[0]
    lw.clear()
    lw.box()

    update_lwi("Play queue")

    i = 0
    for track in play_queue:
        if(i+3 > window_max): break
        lw.addstr(i+1, 1, track.name.encode('utf-8'), 0)
        i = i + 1
    lw.refresh()

def fast_shell_print():
    update_lwi("Fast-shell")
    update_ci("Fastshell: Press a key")

    window_max = lw.getmaxyx()[0]
    lw.clear()
    lw.box()

    try:
        lw.addstr(1, 1, "You are now in fast-shell mode", 0)
        lw.addstr(2, 1, "All actions require only one keypress, and happens instatnly", 0)
        lw.addstr(4, 1, ">Press 'x' to return to normal command mode", 0)
        lw.addstr(5, 1, ">Press 'h' to show this help-screen", 0)
    except curses.error:
        pass

    lw.refresh()


def fast_shell():


    textwin.clear()

    fast_shell_print()

    textwin.clear()
    screen.refresh()
    #curses.echo()

    while 1:
        c = screen.getch()
        if c == ord('n'):
            go_next()
        elif c == ord('x'):
            break  # Exit the while()
        elif c == ord('p'):
            session.player.play(False) 
        elif c == ord('r'):
            session.player.play()
        elif c == ord('q'):
            print_queue()
        elif c == ord('h'):
            fast_shell_print()
        elif c == curses.KEY_HOME:
            x = y = 0

    reset_ci()




# look for event changes 
session.on(
    spotify.SessionEvent.CONNECTION_STATE_UPDATED,
    on_connection_state_changed)
session.on(
    spotify.SessionEvent.END_OF_TRACK, on_end_of_track)

# initialize the alsa audio
try:
    audio_driver = spotify.AlsaSink(session)
except ImportError:
    #logger.warning(
    #    'No audio sink found; audio playback unavailable.')
    print("audio problem")

# start the event loop
event_loop = spotify.EventLoop(session)
event_loop.start()



class StdOutWrapper:
    text = ""
    def write(self,txt):
        self.text += txt
        self.text = '\n'.join(self.text.split('\n')[-30:])
    def get_text(self,beg,end):
        return '\n'.join(self.text.split('\n')[beg:end])

mystdout = StdOutWrapper()
sys.stdout = mystdout
sys.stderr = mystdout


class Commands(cmd.Cmd):
    """Simple command processor example."""
        
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "> "
        self.intro  = "Welcome to console!"  ## defaults to None
	
    def do_greet(self, line):
        self.write("hello "+line)

    def default(self,line) :
        self.write("Don't understand '" + line + "'")

    def do_quit(self, line):
        curses.endwin()
        return True

    def write(self,text) :
        pass
        #screen.clear()
        #textwin.clear()
        #screen.addstr(3,1,">" + text + "<")
        #screen.refresh()

    def do_login(self, line):
        "login <username> <password>"
        self.write("loggin in ...")
        username, password = line.split(' ', 1)
        session.login(username, password, remember_me=True)
        logged_in.wait()
        self.write("logged in")

    def do_playlists(self, line):
        "print playlsits"
        print("Playlists")
        container_root = session.playlist_container
        container_root.load()
        boole = container_root.is_loaded

        if(boole): print("loaded")
        else: print("NOT loaded")

        # ncurses: clear the window
        window_max= lw.getmaxyx()[0] 
        lw.clear()
        lw.box()
        #lw.addstr(2, (cols-len(track.name))//2, track.name.encode('utf-8'), 0)

        update_lwi("My playlists")

        i =     0
        for playlist in container_root:
            if i+3 > window_max:
                self.write("window is full" + str(i) + "max: " + str(window_max))
                break
            if( type(playlist) == spotify.playlist.Playlist):
                if not playlist.is_loaded:
                    a = i
                    #lw.addstr(i+2, 1, "playlists", 0)
                    #print("Not loaded!")
                else:
                    a = i
                    try: 
                        lw.addstr(i+1, 1, str(i) + ":", 0)
                        lw.addstr(i+1, 5, playlist.name.encode('utf-8'), 0)
                    except curses.error:
                        pass
                        #raise
                    #print(a)
                i += 1

        lw.refresh()

    def do_playp(self, line):
        "Play selected playlist in background"
        current_playlist_counter = 0;

        container_root = session.playlist_container
        container_root.load()

        playlistnumber = line.split(' ', 0)
        playlistnumber = int(playlistnumber[0])
        playlist = container_root[playlistnumber]
        playlist.load()

        current_playlist = [] 
        current_playlist.extend(playlist.tracks)

        if randommode: random.shuffle(current_playlist)
        play_queue.extend(current_playlist) 

        play(play_queue.popleft())

    def do_info(self, line):
            "Show normal logging output"
            print('Logging at INFO level')
            print(container_root)
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)

    def do_exit(self, line):
        "Exit"
        if logged_in.is_set():
            print('Logging out...')
            session.logout()
            logged_out.wait()
        event_loop.stop()
        curses.endwin()
        print("Thank you")
        return True

    def do_list(self, line):
        "Print contents of a playlist"
        playlistnumber = line.split(' ', 0)
        playlistnumber = int(playlistnumber[0])
        playlist = container_root[playlistnumber]
        playlist.load()

        for track in playlist.tracks:
            print( track.artists[0].name.encode('utf-8') , "-", 
                track.name.encode('utf-8'))

    def do_n(self, line):
        "Go to next song in current_playlist"
        go_next()

    def do_search(self, line):
        "Search for a song"

    def do_ls(self, line):
        "alias for playlists"
        do_playlists(line)

    def do_clear(self, line):
        play_queue.clear()

    def do_pause(self, line):
        session.player.play(False)

    def do_resume(self, line):
        session.player.play()

    def do_random(self, line):
        if(randommode): randommode = 0
        else: randommode = 1
        print("Random", randommode)

    def do_fastshell(self, line):
        fast_shell() 

    def do_queue(self, line):
        "List current play queue"
        print_queue()

    def do_search(self, query):
        "search <query>"
        if query is None: return
        try:
            result = session.search(query)
            result.load()
        except spotify.Error as e:
            logger.warning(e)
            return

        update_lwi("Search results")
        update_ci("Type search result number")

        textwin.clear()
        window_max = lw.getmaxyx()[0]
        lw.clear()
        lw.box()

        lw.addstr(1, 1, "Found: %d tracks, %d albums, %d artists, and %d playlists" %
            (result.track_total, result.album_total, 
                result.artist_total, result.playlist_total), 0)
        lw.addstr(2, 1, "", 0)



        i = 1
        for track in result.tracks:
                #print(i, track.artists[0].name.encode('utf-8'), "-", track.name.encode('utf-8'))
                if(i+3 > window_max): break
                lw.addstr(i+2, 1, track.name.encode('utf-8'), 0)
                i+=1

        lw.refresh()


        #n = input("Select song to add to queue (0 = none)")
        n = textbox.edit()
        n = int(n) - 1

        #self.write(str(n))
        if(n == -1 ): return
        if(n > 20 ): return
        play_queue.appendleft(result.tracks[n])
        if(end_of_track.is_set()):
            play(play_queue.pop())

        reset_ci()


if __name__ == '__main__':
    curses.noecho()

    np.refresh()
    flag = False
    while not flag :
        text = textbox.edit()
        curses.beep()
        # session.process_events()
        #text = input("test")
        flag = Commands().onecmd(text)
        textwin.clear()





