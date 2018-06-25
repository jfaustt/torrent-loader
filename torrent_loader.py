import sys
import os
import torrent_parser as tp
from qbittorrent import Client

def find_path(torrent_file, search_path):
	# Get a list of files in the torrent
	torrent = tp.parse_torrent_file(torrent_file)
	torrent_files = []

	if 'files' in torrent['info']:
		for tf in torrent['info']['files']:
			torrent_files.append(tf['path'])
	else: # If the torrent contains only a single file, the format is a bit different
		torrent_files.append([torrent['info']['name']])

	# Search for a file matching (by filename) the first in the list
	target = torrent_files[0][len(torrent_files[0]) - 1]

	for path, _, files in os.walk(search_path):
		for f in files:
			if f == target:
				folder_depth = len(torrent_files[0]) - 1
				root = path[::-1][path[::-1].replace('\\', 'x', folder_depth - 1).find('\\') + 1:][::-1]

				return root

def add_torrent(torrent_file, dl_path):
	torrent = tp.parse_torrent_file(torrent_file)
	head, tail = os.path.split(dl_path)

	if ('files' in torrent['info']): # Torrent contains a folder, rather than a single file
		# Ensure that the torrent's root folder name is the same as the local folder's name
		torrent['info']['name'] = tail
		tp.create_torrent_file(torrent_file, torrent)

		# Adjust the DL path to be one folder up, so that it matches up correctly
		dl_path = head

	qb = Client('http://127.0.0.1:8080/')
	qb.download_from_file(open(torrent_file, 'rb'), savepath=dl_path)

	print('Added "' + torrent_file + '", content found in "' + dl_path + '"')

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Usage: torrent_loader.py torrent_file search_path')
		sys.exit()

	found_path = find_path(sys.argv[1], sys.argv[2])

	if not found_path:
		print('Couldn\'t find any matching file(s)')
		sys.exit()

	add_torrent(sys.argv[1], found_path)
