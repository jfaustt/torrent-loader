import sys
import os
import torrent_parser as tp

def find_path(torrent_file, search_path):
	# Get a list of files in the torrent
	torrent = tp.parse_torrent_file(torrent_file)
	torrent_files = []

	for tf in torrent['info']['files']:
		torrent_files.append(tf['path'])

	# Search for a file matching (by filename) the first in the list
	target = torrent_files[0][len(torrent_files[0]) - 1]

	for path, _, files in os.walk(search_path):
		for f in files:
			if f == target:
				folder_depth = len(torrent_files[0]) - 1
				root = path[::-1][path[::-1].replace('\\', 'x', folder_depth - 1).find('\\') + 1:][::-1]

				return root

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('Usage: torrent_loader.py torrent_file search_path')
		exit()

	print(find_path(sys.argv[1], sys.argv[2]))
