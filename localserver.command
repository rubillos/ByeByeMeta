#!python

import subprocess, os, platform
from http.server import HTTPServer, CGIHTTPRequestHandler
import socket
import webbrowser

def getFolder(message):
	path = None

	if platform.system() == "Windows":
		from filedialogs import open_folder_dialog # type: ignore   - for MacOS
		path = open_folder_dialog(title=message)
	else:
		command = f"folderPath=$(osascript -e \'choose folder with prompt \"{message}\"'); if [ -z \"$folderPath\" ]; then exit 1; fi; echo \"$folderPath\""
		result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		
		results = result.stdout.decode("utf-8").split("\n")
		if len(results) > 1:
			if not "User canceled." in results[1]:
				path = results[1].removeprefix("alias ")
				path = "/"+"/".join(path.split(":")[1:-1])
	
	return path

path = getFolder("Select the folder to serve")
if path is None:
    exit()
	
print(f'Serving {path} at {socket.gethostname()}')

os.chdir(path)
server_object = HTTPServer(server_address=('', 80), RequestHandlerClass=CGIHTTPRequestHandler)

webbrowser.open('http://localhost/index.html')

server_object.serve_forever()
