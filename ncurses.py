#!/usr/bin/env python 
# -*- coding: utf-8 -*- 

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


def now_playing_box():
    cols = int(tigetnum("cols"))
    lines = int(tigetnum("lines"))

    window = curses.newwin(3, cols, lines-4, 0)
    window.addstr(1, 2, "Nothing playing", 0)
    window.addstr(1, 2, "", 0)
    window.addstr(2, 2, "", 0)
    #window.attron(0)


    #window.box()
    screen.refresh()
    return window

np = now_playing_box()

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
    #go_next()

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
    np.addstr(0, (cols-len(track.artists[0].name))//2, track.artists[0].name.encode('utf-8'), 0)
    np.addstr(1, (cols-len(track.name))//2, track.name.encode('utf-8'), 0)
    np.addstr(2, (cols-len(track.album.name))//2, track.album.name.encode('utf-8'), 0)
    np.refresh()
    screen.refresh()

def go_next():
    if(len(play_queue) > 0):
        play(play_queue.popleft())
    else:
            print("Play queue empty")

# look for event changes 
session.on(
    spotify.SessionEvent.CONNECTION_STATE_UPDATED,
    on_connection_state_changed)
session.on(
    spotify.SessionEvent.END_OF_TRACK, on_end_of_track(session))

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

# ncurses
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
        screen.clear()
        textwin.clear()
        screen.addstr(3,0,text)
        screen.refresh()

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

        i = 0

        for playlist in container_root:
            if( type(playlist) == spotify.playlist.Playlist):
                if not playlist.is_loaded:
                    print("Not loaded!")
                else:
                    a = i, playlist.name.encode('utf-8')
                    print(a)
                i += 1

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

        now_playing_box()

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
        print('')
        return True

    def do_playlists(self, line):
        "print playlsits"
        print("Playlists")
        container_root = session.playlist_container
        container_root.load()  
        i = 0

        for playlist in container_root:
            if( type(playlist) == spotify.playlist.Playlist):
                a = i, playlist.name.encode('utf-8')
                print(a)
                i += 1

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

    def do_queue(self, line):
        "List current play queue"
        for track in play_queue:
            print(track.name.encode('utf-8'))

    def do_search(self, query):
        "search <query>"
        if query is None: return
        try:
            result = session.search(query)
            result.load()
        except spotify.Error as e:
            logger.warning(e)
            return

        print("\n") 
        print("%d tracks, %d albums, %d artists, and %d playlists found." %
            (result.track_total, result.album_total, 
                result.artist_total, result.playlist_total))
        i = 1
        for track in result.tracks:
                print(i, track.artists[0].name.encode('utf-8'), "-", track.name.encode('utf-8'))
                i+=1

        n = input("Select song to add to queue (0 = none)")
        n = int(n) - 1
        if(n == -1 ): return
        if(n > 20 ): return
        play_queue.appendleft(result.tracks[n])
        print(end_of_track) 
        if(end_of_track.is_set()):
            play(play_queue.pop())
        print("\n") 



if __name__ == '__main__':
    curses.noecho()
    textwin,textbox = maketextbox(1,40, 1,1,"")

    np.refresh()
    flag = False
    while not flag :
        text = textbox.edit()
        curses.beep()
        session.process_events()
        #text = input("test")
        flag = Commands().onecmd(text)




