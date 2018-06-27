import sys
import os
import time
import configparser
import torrent_parser as tp
from qbittorrent import Client

strict_mode = True

# Checks whether a local folder fully matches a torrent's file structure (by name only)
def assert_valid(torrent_file_list, folder):
	file_list = []

	for path, _, files in os.walk(folder):
		for f in files:
			file_list.append(path.replace(folder, '').split('\\')[1::] + [f])
	
	return all(x in file_list for x in torrent_file_list) # Allow for extra content in the structure

def find_path(torrent_file, search_path):
	# Get a list of files in the torrent
	torrent = tp.parse_torrent_file(torrent_file)
	torrent_files = []

	if 'files' in torrent['info']:
		for tf in torrent['info']['files']:
			torrent_files.append(tf['path'])
	else: # If the torrent contains only a single file, the format is a bit different
		torrent_files.append([torrent['info']['name']])

	# Search for a file matching (by filename) any defined in the torrent
	torrent_files_only = []

	# Get a list of just the files in the torrent, ignoring structure
	for f in torrent_files:
		torrent_files_only.append(f[len(f) - 1])

	for path, _, files in os.walk(search_path):
		for f in files:
			if f in torrent_files_only:
				folder_depth = len(torrent_files[0]) - 1
				root = path[::-1][path[::-1].replace('\\', 'x', folder_depth - 1).find('\\') + 1:][::-1]
				
				if (not strict_mode) or assert_valid(torrent_files, root):
					return root
				else:
					return 'partial'

def add_torrent(torrent_file, dl_path):
	torrent = tp.parse_torrent_file(torrent_file)
	head, tail = os.path.split(dl_path)

	if ('files' in torrent['info']): # Torrent contains a folder, rather than a single file
		# Ensure that the torrent's root folder name is the same as the local folder's name
		torrent['info']['name'] = tail
		tp.create_torrent_file(torrent_file, torrent)

		# Adjust the DL path to be one folder up, so that it matches up correctly
		dl_path = head

	config = configparser.ConfigParser()
	config.read('config.ini')

	if not 'qBittorrent' in config:
		print('Torrent Loader requires that qBittorrent WebUI is enabled.')
		address = input('Address of WebUI (e.g. http://localhost:8080/): ')
		secured = input('Does WebUI require a login? (y/n) ')

		username = 'admin'
		password = 'admin'
		
		if secured == 'y':
			username = input('Username: ')
			password = input('Password: ')

		config['qBittorrent'] = {
			'address': address,
			'secured': secured,
			'username': username,
			'password': password
		}

		print()

	with open('config.ini', 'w') as config_file:
		config.write(config_file)

	qb = Client(config['qBittorrent']['address'])
	if config['qBittorrent']['secured'] == 'y':
		qb.login(config['qBittorrent']['username'], config['qBittorrent']['password'])

	try:
		qb.download_from_file(open(torrent_file, 'rb'), savepath=dl_path)
		print('Added "' + torrent_file + '", content found in "' + dl_path + '"')
	except:
		print('An error occurred; the torrent probably already exists (' + torrent_file + ')')

def monitor_folder(folder, search_path):
	for path, _, files in os.walk(folder):
		for f in files:
			_, ext = os.path.splitext(f)
			
			if ext == '.torrent':
				file_path = path + '\\' + f
				found_path = find_path(file_path, search_path)

				if not found_path:
					print('Couldn\'t find any matching file(s) for "' + file_path + '"')
				elif found_path == 'partial':
					print('Found only partial matching file(s) for "' + file_path + '"')
				else:
					add_torrent(file_path, found_path)

				os.remove(file_path) # Remove the torrent so that it isn't processed again

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print('Usage: torrent_loader.py torrent_file search_path [-l]')
		print('       torrent_loader.py -m monitor_folder search_path [-l]')
		print()
		print('  -l   Lenient: Adds torrents even if their content is only partially found.')
		sys.exit()

	if '-l' in sys.argv: # Lenient
		strict_mode = False

	if sys.argv[1] == '-m': # Monitor folder mode
		print('Monitoring "' + sys.argv[2] + '" for torrent files...\n')

		while True:
			monitor_folder(sys.argv[2], sys.argv[3])
			time.sleep(5)
	else:
		found_path = find_path(sys.argv[1], sys.argv[2])

		if not found_path:
			print('Couldn\'t find any matching file(s)')
		elif found_path == 'partial':
			print('Found only partial matching file(s). Use -l to add as torrent anyway. Note that missing content will be downloaded!')
		else:
			add_torrent(sys.argv[1], found_path)
