#!/bin/env python
#logging.basicConfig(level=logging.DEBUG)

#what is this?
#from __future__ import unicode_literals

import logging
import threading
import cmd

import spotify

#container_root = 0

print("Spotify_terminal")

class Commander(cmd.Cmd):
	# what is this
	doc_header = 'Commands'

	prompt = 'Command> '
	logger = logging.getLogger('shell.commander')
	container_root = 0

	def __init__(self):
		cmd.Cmd.__init__(self)

		self.logged_in = threading.Event()
		self.logged_out = threading.Event()
		self.logged_out.set()

		self.session = spotify.Session()
		self.session.on(
			spotify.SessionEvent.CONNECTION_STATE_UPDATED,
			self.on_connection_state_changed)
		self.session.on(
			spotify.SessionEvent.END_OF_TRACK, self.on_end_of_track)

		try:
			self.audio_driver = spotify.AlsaSink(self.session)
		except ImportError:
			self.logger.warning(
				'No audio sink found; audio playback unavailable.')

		self.event_loop = spotify.EventLoop(self.session)
		self.event_loop.start()

	def on_connection_state_changed(self, session):
		if session.connection.state is spotify.ConnectionState.LOGGED_IN:
			self.logged_in.set()
			self.logged_out.clear()
			print("loading playlists")
			self.load_root_container()

		elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
			self.logged_in.clear()
			self.logged_out.set()

	def on_end_of_track(self, session):
		self.logger.info("End of track")
		self.session.player.play(False)
		#end_of_track.set()

	# document this
	def precmd(self, line):
		if line:
			self.logger.debug('New command: %s', line)
		return line

	# document this
	def emptyline(self):
		pass

	def do_info(self, line):
		"Show normal logging output"
		print('Logging at INFO level')
		print(self.container_root)
		logger = logging.getLogger()
		logger.setLevel(logging.INFO)

	def do_login(self, line):
		"login <username> <password>"
		username, password = line.split(' ', 1)
		self.session.login(username, password, remember_me=True)
		self.logged_in.wait()

	def do_exit(self, line):
		"Exit"
		if self.logged_in.is_set():
			print('Logging out...')
			self.session.logout()
			self.logged_out.wait()
		self.event_loop.stop()
		print('')
		return True

	def do_playlists(self, line):
		"print playlsits"
		print("Playlists")
		self.container_root = self.session.playlist_container
		self.container_root.load()	
		#print(container_root)
		i = 0
		for playlist in self.container_root:
			if( type(playlist) == spotify.playlist.Playlist):
				a = i, playlist.name.encode('utf-8')
				print(a)
				i += 1

	def do_list(self, line):
		"Print contents of a playlist"
		playlistnumber = line.split(' ', 0)
		playlistnumber = int(playlistnumber[0])
		playlist = self.container_root[playlistnumber]
		playlist.load()

		for track in playlist.tracks:
			print( track.artists[0].name.encode('utf-8') , "-", track.name.encode('utf-8'))

	def do_playp(self, line):
		"Play selected playlist"
		playlistnumber = line.split(' ', 0)
		playlistnumber = int(playlistnumber[0])
		playlist = self.container_root[playlistnumber]
		playlist.load()

		self.play(playlist.tracks[0])

	def do_search(self, line):
		"Search for a song"

	def do_ls(self, line):
		"alias for playlists"
		self.do_playlists(line)

	def play(self, track):
		track.load()
		self.session.player.load(track)
		self.session.player.play()
		print("Playing: ", track.artists[0].name.encode('utf-8') , 
			"-", track.name.encode('utf-8'))

	def load_root_container(self):
		self.container_root = self.session.playlist_container
		self.container_root.load()

# do the cmd loop
if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	Commander().cmdloop()