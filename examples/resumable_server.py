'''
Created by Jiten Mehta on 10/22/2020.

An example server to aid in developing resumable uploads.

Directory structure:
	This server expects a folder named uploads to exist at the location
	where this script is invoked.

File nomenclature:
	- The server prepends the files with the client_token
	  Eg - 08932499-0570-4BD5-815D-1992F5F5C031_file

	- When the upload is complete, the server simply adds a '.completion' at
	  the end of the file indicating that the file has been uploaded to
	  completion

Running the server:
	To run the server:
	1. Set the environment variable $ export FLASK_APP=resumable_server.py
	2. $ python -m flask run

	Tip - If you want to change the ip address to a static ip, you can specify
	the --host and --port flag when invoking flask run

'''

#!/usr/bin/python

from flask import Flask
from flask import Response
from flask import stream_with_context
from flask import request
import requests
import os

app = Flask(__name__)

# Some constants
CHUNK_SIZE = 1024 * 1024 * 20 # 20 MB chunks

# HTTP header keys
HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY = "Client-Upload-Token"
HTTP_UPLOAD_RESUMPTION_OFFSET_KEY = "Upload-Resumption-offset"

'''
Internal function used to lookup files stored on the disk.

@return -It returns the filename and size if a file with a given
		token is found, else returns None
'''
def findFileWithToken(token):
	print 'Find file with token ' + token
	size = -1
	directory = 'uploads'
	for filename in os.listdir(directory):
		if not filename.endswith('completed'):
			fileToken = filename.split('_')[0]

			if fileToken == token:
				print "Found file for given token"
				size = os.stat(directory + "/" + filename).st_size
				return (filename, size)
			else:
				print "Did not find file for given token"
				return None


@app.route('/', methods=['GET'])
def defaultGET():
	headers = request.headers
	return "HTTP Method = GET. Headers " + str(headers)


'''
The HEAD verb is used to get the resumable offset of the file.
This server checks the uploads directory to find any files that have
this client token and are not prepended with '.completed'
'''
@app.route('/', methods=['HEAD'])
def getToken():
	headers = request.headers
	offset = 0
	# Check if the request headers carry the client token
	if HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY in headers:
		uploadToken = headers[HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY]
		result = findFileWithToken(uploadToken)
		# If we already have an incomplete file with this token, get the size
		if result is not None:
			fileName = result[0]
			fileSize = result[1]
			offset = (fileSize)

	resp = Response("HTTP/1.1 200 OK")
	resp.headers[HTTP_UPLOAD_RESUMPTION_OFFSET_KEY] = str(offset)
	return resp

'''
POST is used to receiving files with a new token. If a token is reused, this
server currently deletes the old file and simply creates a new one using
the same token
'''
@app.route('/file', methods=['POST'])
def storeNewData():
	headers = request.headers
	path = request.path

	if HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY in headers:
		uploadToken = headers[HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY]
		if uploadToken is not None:
			print "The client upload token = " + str(uploadToken)
			fileName = str(uploadToken) + "_" + path[1:]
			print "The filename = " + fileName
			filePath = "uploads/" + fileName
			with open(filePath, "w+b") as f:
				while True:
					chunk = request.stream.read(CHUNK_SIZE)
					if len(chunk) == 0:
						os.rename(filePath, filePath + ".completed")
						return "Finished receiving entire body"
					f.write(chunk)
		return 'HTTP Method = POST. Got request headers ' + str(headers)å
	else:
		return 'No client token provided'

'''
The client sends a PATCH request when it wants to append data to an existing
file. This function does not delete the old file but opens it in append mode 
and adds bytes to the existing file
'''
@app.route('/file', methods=['PATCH'])
def storePartialData():
	headers = request.headers
	path = request.path

	if HTTP_CLIENT_UPLOAD_TOKEN_HEADER_KEY in headers:
		uploadToken = headers['X-Client-Upload-Token']
		if uploadToken is not None:
			print "The client upload token = " + str(uploadToken)
			fileName = str(uploadToken) + "_" + path[1:]
			print "The filename = " + fileName
			filePath = "uploads/" + fileName
			with open(filePath, "ab") as f:
				while True:
					chunk = request.stream.read(CHUNK_SIZE)
					if len(chunk) == 0:
						return "Finished receiving entire body"
					f.write(chunk)
		return 'HTTP Method = POST. Got request headers ' + str(headers)
	else:
		return 'No client token provided'

if __name__ == '__main__':
	app.run()
