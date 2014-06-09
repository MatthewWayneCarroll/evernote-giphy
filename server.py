from flask import Flask, render_template, request
import requests
from evernote.api.client import EvernoteClient
import hashlib
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.ttypes as NoteStoreTypes
import evernote.edam.notestore.NoteStore as NoteStore
#from evernote.edam.notestore.ttypes import NotesMetadataResultSpec
import binascii

giphy_api_key="dc6zaTOxFJmzC" #public beta key
evernote_auth_token = "insert evernote auth token here"

app=Flask(__name__)

@app.route("/", methods=['POST','GET'])
def main():
	""" GET: gets random gif from giphy and displays it along with the option to see another gif and to 
	save the gif to their evernote account"""
	if request.method == "GET":	
		#get random gif from giphy api
		response=requests.get("http://api.giphy.com/v1/gifs/random?api_key="+giphy_api_key).json()
		if not response['meta']['msg']=='OK':
			return "error with connection to giphy"

		#get random image url and id from giphy api response
		giphy_url=response['data']['image_url']
		giphy_id=response['data']['id']

		#get tags and pass them to the page because the giphy api only show tags for random images
		giphy_tags=''
		for tag in response['data']['tags']:
			giphy_tags+=tag+', '
		giphy_tags=giphy_tags[:-2]

		return render_template("index.html", giphy_url=giphy_url, giphy_id=giphy_id, giphy_tags=giphy_tags) 
	
	"""POST: shows confomation of evernote gif save and presents option 
	to return to main page or see the note in evernote"""
	if request.method == 'POST':
		if request.form['giphy_id'] and request.form['giphy_tags']:
			giphy_id=request.form['giphy_id']
			giphy_tags=request.form['giphy_tags']
			response=requests.get("http://api.giphy.com/v1/gifs/"+giphy_id+"?api_key="+giphy_api_key).json()
			giphy_url=response['data']['images']['original']['url']

			client = EvernoteClient(token=evernote_auth_token, sandbox=True)
			user_store = client.get_user_store()
			note_store = client.get_note_store()
			notebooks = note_store.listNotebooks()
			
			
			#check if giphy notebook exists
			for notebook in notebooks:
				if notebook.name=="Giphy":
					giphyNotebookGuid=notebook.guid
					break
			#if not create it
			try: 
				giphyNotebookGuid
			except NameError:
				notebook=Types.Notebook()
				notebook.name="Giphy"
				notebook=note_store.createNotebook(notebook)
				giphyNotebookGuid=notebook.guid

			#create note title with user name + giphy id for unique identifier
			note_title=response['data']['username']+"-"+response['data']['id']
			
			#check if not for gif already exists
			'''
			notebook_filter=NoteStoreTypes.NoteFilter()
			notebook_filter.guid=giphyNotebookGuid
			result_spec = NotesMetadataResultSpec(includeTitle=True)
			noteList    = note_store.findNotesMetadata(evernote_auth_token, notebook_filter,0 , 4000, result_spec)

			
			print noteList
			print type(noteList)

			# note is an instance of NoteMetadata
			# result_list is an instance of NotesMetadataList
			for note in noteList:
			    print note.title



			for note in noteList.notes:
				if note.title==note_title:
					return render_template("saved.html", giphy_url=giphy_url, evernote_url=evernote_url)
					'''

			image= requests.get(giphy_url, stream=True).content
			md5 = hashlib.md5()
			md5.update(image)
			gif_hash = md5.digest()

			data = Types.Data()
			data.size = len(image)
			data.bodyHash = gif_hash
			data.body = image

			resource = Types.Resource()
			resource.mime = 'image/gif'
			resource.data = data

			hash_hex = binascii.hexlify(gif_hash)

			
			note = Types.Note()
			note.notebookGuid=giphyNotebookGuid #create note for our Giphy notebook
			
			note.title=note_title #name based on Giphy username and id
			note.content = '<?xml version="1.0" encoding="UTF-8"?>'
			note.content += '<!DOCTYPE en-note SYSTEM ' \
			    '"http://xml.evernote.com/pub/enml2.dtd">'
			note.content += '<en-note>'+giphy_tags+'<br/>' #add tags to note contents
			note.content += '<en-media type="image/png" hash="' + hash_hex + '"/>'
			note.content += '</en-note>'
			
			note.resources = [resource] # Now, add the new Resource to the note's list of resources

			note=note_store.createNote(note) # create the note

			evernote_url="http://www.matthewwaynecarroll.com"
			return render_template("saved.html", giphy_url=giphy_url, evernote_url=evernote_url)
		else:
			return "error finding the gif"

	else:
		return "server error"




if __name__=="__main__":
	app.run(debug=True)
