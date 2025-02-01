#!python3

# pip3 install --upgrade pip
# pip3 install beautifulsoup4
# pip3 install dateutil
# pip3 install requests
# pip3 install Pillow
# pip3 install opencv-python

from bs4 import BeautifulSoup, NavigableString
import re
from dateutil.parser import parse
from enum import Enum
import subprocess, sys, os, shutil
import requests
import argparse
from PIL import Image
import cv2

assetsFolder = "assets"
entryFolder = "entries"
mediaFolder = "media"
staticImageFolder = "static"
indexName = "index.html"
entryName = "entries{}.html"
appName = "app.js"
styleName = "style.css"

fbFolderName = "your_facebook_activity"
igFolderName = "your_instagram_activity"

postsFolder = "posts"
mainPostsName = "your_posts__check_ins__photos_and_videos_1.html"
otherPostsName = "your_uncategorized_photos.html"
yourPhotos = "your_photos.html"
yourVideos = "your_videos.html"
albumsFolderName = "album"

contentFolder = "content"
igPostsName = "posts_1.html"

staticPrefix = "https://static."

parser = argparse.ArgumentParser(description='Process FB Data Download')

parser.add_argument("-i", dest="srcFolder", help="Path to <your_facebook_activity folder>", type=str, default=None)
parser.add_argument("-o", dest="dstFolder", help="Path to output folder", type=str, default=None)

parser.add_argument("-b", "--birthdays", dest="birthdays", help="Include birthday posts", action="store_true")

group = parser.add_argument_group("exclusion options")
parser.add_argument("-x", "--exclude", dest="exclude", help="List of comma separated numbers to exclude", type=str, default="")
parser.add_argument("-xfb", "--exclude-fb", dest="excludefb", help="List of comma separated numbers to exclude from Facebook data", type=str, default="")
parser.add_argument("-xig", "--exclude-ig", dest="excludeig", help="List of comma separated numbers to exclude from Instagram data", type=str, default="")

args = parser.parse_args()

scriptPath = os.path.abspath(os.path.dirname(sys.argv[0]))

def getFolder(message):
	command = f"folderPath=$(osascript -e \'choose folder with prompt \"{message}\"'); if [ -z \"$folderPath\" ]; then exit 1; fi; echo \"$folderPath\""
	result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	
	results = result.stdout.decode("utf-8").split("\n")
	if len(results) > 1:
		if "User canceled." in results[1]:
			path = None
		else:
			path = results[1].removeprefix("alias ")
			path = "/"+"/".join(path.split(":")[1:-1])
	else:
		path = None
	
	return path

def pluralize(string, count, pad=False):
	return "{:d} {}{}".format(count, string, "s" if count!=1 else " " if pad else "")

def fileExists(path):
	return os.path.isfile(path)

def createFolder(path):
	if "." in path:
		path = os.path.dirname(path)
	try:
		os.makedirs(path, exist_ok=True)
		return True
	except OSError as e:
		print(f"Error creating folder '{path}': {e}")
		return False

def copyFile(srcPath, dstPath):
	if not os.path.isfile(dstPath) or os.path.getsize(srcPath) != os.path.getsize(dstPath):
		try:
			os.makedirs(os.path.dirname(dstPath), exist_ok=True)
			shutil.copy(srcPath, dstPath)
			return True
		except OSError as e:
			print(f"Error copying '{srcPath}' to '{dstPath}' - {e}")
			return False
	else:
		return False

def processData():
	if args.srcFolder != None:
		srcFolder = args.srcFolder
	else:
		srcFolder = getFolder("Select the <your_facebook/instagram_activity folder>:")

	if srcFolder == None:
		return
	
	if args.dstFolder != None:
		dstFolder = args.dstFolder
	else:
		dstFolder = getFolder("Select the destination folder:")

	if dstFolder == None:
		return

	print(f"src={srcFolder}\ndst={dstFolder}")

	# --------------------------------------------------
	print("Check Data Type")

	if os.path.basename(srcFolder) == fbFolderName:
		print("Processing Facebook Data")
		isFacebook = True
	elif os.path.basename(srcFolder) == igFolderName:
		print("Processing Instagram Data")
		isFacebook = False
	else:
		print("Unknown source data folder!")
		return

	# --------------------------------------------------
	print("Open Main Data File")

	if isFacebook:
		mainSrcFile = os.path.join(srcFolder, postsFolder, mainPostsName)
	else:
		mainSrcFile = os.path.join(srcFolder, contentFolder, igPostsName)

	with open(mainSrcFile) as fp:
		soup = BeautifulSoup(fp, 'lxml')

	# --------------------------------------------------
	print("Cleaning destination folder...")

	foldersRemoved = 0
	filesRemoved = 0
	for name in os.listdir(dstFolder):
		path = os.path.join(dstFolder, name)
		if name==entryFolder or name==assetsFolder or name==mediaFolder:
			shutil.rmtree(path)
			foldersRemoved += 1
		elif name==indexName:
			os.remove(path)
			filesRemoved += 1
	if filesRemoved>0 or foldersRemoved>0:
		print(" removed {} and {}.".format(pluralize("folder", foldersRemoved), pluralize("file", filesRemoved)))
	else:
		print(" done.")

	# --------------------------------------------------
	print("Copying Assets folder...")

	destAssetsPath = os.path.join(dstFolder, assetsFolder)
	if os.path.isdir(destAssetsPath):
		shutil.rmtree(destAssetsPath)
	if not os.path.isdir(destAssetsPath):
		srcAssetsPath = os.path.join(scriptPath, assetsFolder)
		try:
			shutil.copytree(srcAssetsPath, destAssetsPath)
			print(" done.")
		except OSError as e:
			print("\nError copying: ", destAssetsPath, e)

	# --------------------------------------------------
	print("Build used file list")

	usedFiles = set()

	mainEntries = soup.find("div", class_="_a6-g").parent
	for entry in mainEntries:
		imgs = entry.find_all(["img", "video"])
		for img in imgs:
			src = img['src']
			if not src.startswith("http"):
				usedFiles.add(os.path.basename(src))

	# --------------------------------------------------

	def mergeAlbumSoup(albumSoup):
		firstDiv =albumSoup.find("div", class_="_a6-g")
		if firstDiv:
			albumList = list(firstDiv.parent.children)
			for entry in albumList:
				skip = False
				imgs = entry.find_all(["img", "video"])
				for img in imgs:
					src = os.path.basename(img['src'])
					if src in usedFiles:
						skip = True
						break
					else:
						usedFiles.add(src)
				if not skip:
					entry.extract()
					tab = entry.find('table')
					if (tab != None):
						tab.decompose()
					if len(list(entry.children)) == 2:
						newDiv = soup2.new_tag("div")
						label = entry.find("div", class_= "_3-95")
						if label != None and label.string != None:
							newDiv.string = label.string
						else:
							newDiv.string = " "
						newDiv['class'] = ["_2ph_", "_a6-h", "_bot4"]
						entry.insert(0, newDiv)
					mainEntries.append(entry)

	if isFacebook:
		print("Merge Photos")
		photosSrcFile = os.path.join(srcFolder, postsFolder, yourPhotos) 
		with open(photosSrcFile) as fp:
			soup2 = BeautifulSoup(fp, 'lxml')
			mergeAlbumSoup(soup2)

		print("Merge Videos")
		videosSrcFile = os.path.join(srcFolder, postsFolder, yourVideos) 
		with open(videosSrcFile) as fp:
			soup2 = BeautifulSoup(fp, 'lxml')
			mergeAlbumSoup(soup2)

		print("Merge Other Posts")
		otherSrcFile = os.path.join(srcFolder, postsFolder, otherPostsName) 
		with open(otherSrcFile) as fp:
			soup2 = BeautifulSoup(fp, 'lxml')
			mergeAlbumSoup(soup2)

		albumsFolder = os.path.join(srcFolder, postsFolder, albumsFolderName)
		albumFiles = [f for f in os.listdir(albumsFolder) if f.endswith(".html")]

		print("Merge", len(albumFiles), "albums")

		for albumFile in albumFiles:
			albumSrcFile = os.path.join(albumsFolder, albumFile)
			with open(albumSrcFile) as fp:
				soup4 = BeautifulSoup(fp, 'lxml')
				mergeAlbumSoup(soup4)

	# --------------------------------------------------
	print("Remove unneeded elements")

	del soup.head.base['href']

	upstrs = soup.find_all("div", string="Mobile uploads")
	for updiv in upstrs:
		updiv.decompose()

	if isFacebook:
		pdescs = soup.find_all("div", class_="_3-95")
		for pdsc in pdescs:
			pdsc.decompose()
	else:
		table = soup.find("table")
		if table != None:
			table.decompose()
		heading = soup.find("div", class_="_3-8y")
		if heading != None:
			heading.decompose()

	# --------------------------------------------------
	print("Remove Facebook links")

	fblinks = soup.find_all("a", href=re.compile(".*facebook\.com"))
	for flink in fblinks:
		p = flink.parent
		flink.unwrap()
		p.smooth()

	# --------------------------------------------------
	print("Remove GPS coordinates")

	def isAPlace(tag):
		if (tag.name == "div"):
			kids = list(tag.children)
			if len(kids) == 1 and isinstance(kids[0], NavigableString):
				if tag.string.startswith("Place: "):
					return True
		return False

	places = soup.find_all(isAPlace)
	for place in places:
		place.string = re.sub(" \(-?\d+.?\d*, ?-?\d+.?\d*\)", "", place.string).replace("Place: ", "")
		place.unwrap()

	# --------------------------------------------------
	print("Remove Addresses")

	addresses = soup.find_all("div", string=re.compile("^Address: "))
	for address in addresses:
		address.decompose()

	# --------------------------------------------------
	print("Reformat entries")

	def addClass(tag, c):
		classes = tag['class']
		if c not in classes:
			classes.append(c)
			tag['class'] = classes

	def removeClass(tag, c):
		classes = tag['class']
		if c in classes:
			classes.remove(c)
			tag['class'] = classes

	def convertToDatetime(dateStr, parserinfo=None):
		return parse(dateStr, parserinfo=parserinfo)

	firstDiv = soup.body.find("div")
	removeClass(firstDiv, "clearfix")
	removeClass(firstDiv, "_ikh")
	secondDiv = firstDiv.find("div")
	removeClass(secondDiv, "_4bl9")
	thirdDiv = secondDiv.find("div")
	removeClass(thirdDiv, "_li")

	entries = soup.find_all("div", class_="_a6-g")
	entryOuter = entries[0].parent
	for entry in entries:
		if isFacebook:
			kids = list(entry.children)
			if len(kids) == 3 and kids[0].string != None:
				twop = kids[1].find_all("div", class_="_2pin")
				if len(twop) == 2:
					subkids = list(twop[1].children)
					if len(subkids) == 2:
						kids[0].string.replace_with(", ".join(list(subkids[0].strings)))
						twop[1].decompose()
				removeClass(kids[0], "_a6-i")
				addClass(kids[0], "_bot4")
				addClass(kids[1], "_3-94")
				addClass(kids[1], "_top0")
				addClass(kids[2], "_a6-o")
				kids[0].parent.insert(1, kids[2].extract())
				a7ng = entry.find_all("div", class_="_a7ng")
				for item in a7ng:
					div1 = item.find("div")
					if div1 != None:
						div2 = div1.find("div")
						if div2 != None:
							div2.decompose()
			if kids[0].string == " ":
				kids[0].string.replace_with("")
			a701 = entry.find_all("div", class_="_a701")
			a72d = entry.find_all("div", class_="_a72d")
			if len(a72d) == 1:
				entry.itemdate = convertToDatetime(str(a72d[0].string))
			if len(a701) == 1 and len(a72d) == 1:
				newStr = str(a72d[0].string) + " with " + str(a701[0].string).replace("You tagged ", "")
				a72d[0].string.replace_with(newStr)
				a701[0].decompose()
		else:
			a6ps = entry.find_all("div", class_="_a6-p")
			if len(a6ps) == 1:
				tables = a6ps[0].find_all("table")
				for table in reversed(tables):
					table.decompose()
				a6o = entry.find_all("div", class_="_a6-o")
				if len(a6o) == 1:
					entry.itemdate = convertToDatetime(str(a6o[0].string))
				kids = list(entry.children)
				if len(kids) == 2:
					newDiv = soup.new_tag("div")
					newDiv.string = " "
					newDiv['class'] = ["_2ph_", "_a6-h"]
					entry.insert(0, newDiv)
					kids = list(entry.children)
				entry.insert(1, a6o[0].extract())
				if len(kids) == 3:
					addClass(kids[0], "_top4")
					addClass(kids[2], "_top0")

		entry.extract()

	# --------------------------------------------------
	print("Sort entries")

	entries.sort(key=lambda x: x.itemdate, reverse=True)
	entryOuter.extend(entries)

	# --------------------------------------------------
	print("Remove unneeded headings")

	headings = soup.find_all("div", string=[
		re.compile(".* shared a link\."),
		re.compile(".* updated .* status\."),
		re.compile(".* shared a post\."),
		re.compile(".* shared an album\."),
		re.compile(".* added a new video.*\."),
		re.compile(".* added a new photo.*\."),
		re.compile(".* shared a memory\.")
	])
	for heading in headings:
		heading.string.replace_with("")

	# --------------------------------------------------
	print("Clean up tags")

	class Clean(Enum):
		Ok = 0
		Remove = 1
		Unwrap = 2

	def cleanTag(tag, indent=0):
		kids = list(tag.children)
		classCount = 0
		try:
			classCount = len(tag['class'])
		except KeyError:
			pass
		haveString = False
		for subTag in reversed(kids):
			if isinstance(subTag, NavigableString):
				haveString = True
			else:
				result = cleanTag(subTag, indent+1)
				if result == Clean.Remove:
					subTag.decompose()
				elif result == Clean.Unwrap:
					subTag.unwrap()
		count = len(list(tag.children))
		if tag.name == "div" and count == 0 and classCount == 0:
			return Clean.Remove
		elif tag.name == "div" and count == 1  and classCount == 0 and not haveString:
			return Clean.Unwrap
		else:
			return Clean.Ok

	cleanTag(soup.body)

	# --------------------------------------------------
	print("Add entry numbers")

	xstring = ""

	if isFacebook:
		xstring = args.excludefb
	else:
		xstring = args.excludeig

	if xstring == "":
		xstring = args.exclude

	xlist = xstring.split(",")
	toDelete = []
	entries = soup.find_all("div", class_="_a6-g")
	for i, entry in enumerate(entries):
		entry['eix'] = i
		if str(i) in xlist:
			toDelete.append(entry)

	for item in toDelete:
		item.decompose()

	# --------------------------------------------------
	print("Remove duplicate and birthday tags")

	entries = soup.find_all("div", class_="_a6-g")
	toDelete = []
	for entry in entries:
		pin2 = entry.find_all("div", class_="_2pin")
		for item in pin2:
			div1 = item.find("div")
			if div1 != None:
				divs = div1.find_all("div")
				if len(divs)==2:
					if str(divs[0].string)==str(divs[1].string):
						divs[1].decompose()
				if not args.birthdays:
					for string in div1.strings:
						if re.match("^ha+p{2,}y .*birthday.*", string, re.IGNORECASE):
							toDelete.append(entry)
							break
	for item in toDelete:
		item.decompose()
		entries.remove(item)

	print("Deleted", len(toDelete), "birthday entries")

	# --------------------------------------------------
	print("Remove Updated... strings")

	pin2s = soup.find_all("div", string=re.compile("^Updated \w{3} \d{2}, \d{4} \d{1,2}:\d{2}:\d{2} [ap]m"))
	for pin in pin2s:
		pin.decompose()

	# --------------------------------------------------
	print("Clean up titles")

	if isFacebook:
		entries = soup.find_all("div", class_="_a6-g")
		for entry in entries:
			a6h = entry.find("div", class_="_a6-h")
			a6p = entry.find("div", class_="_a6-p")
			if a6h != None and a6p != None:
				if a6h.string == "" or a6h.string == " ":
					pin2s = a6p.find_all("div", class_="_2pin")
					if len(pin2s) > 0 and len(pin2s) <= 2:
						last = len(pin2s) - 1
						if pin2s[last].string != None:
							a6h.string.replace_with(pin2s[last].string)
							pin2s[last].decompose()
						else:
							newParts = []
							for string in list(pin2s[last].strings):
								if not string.startswith("http"):
									if len(string)>0 and string != " ":
										newParts.append(str(string))
									string.extract()
							if (len(newParts)):
								a6h.string.replace_with(" ".join(newParts))
							pin2s[last].decompose()
			else:
				clist = list(entry.children)
				if len(clist) == 2:
					pin2s = entry.find_all("div", class_="_2pin")
					if len(pin2s) == 2 and pin2s[1].string != None:
						second = clist[1]
						second.extract()
						entry.insert(0, second)
						newDiv = soup.new_tag("div")
						newDiv.string = pin2s[1].string
						newDiv['class'] = ["_2ph_", "_a6-h", "_bot4"]
						pin2s[1].decompose()
						entry.insert(0, newDiv)	

	# --------------------------------------------------
	print("Count tags")

	allClasses = set()
	allNames = set()
	allIDs = set()
	for item in soup.descendants:
		try:
			for c in item['class']:
				allClasses.add(f'.{c}')
		except:
			pass

		try:
			if item.name and item.name not in allNames:
				allNames.add(item.name)
		except:
			pass

		try:
			if item['id']:
				allIDs.add(item['id'])
		except:
			pass

	print("There are", len(allNames), "tags")
	print("There are", len(allClasses), "classes")
	print("There are", len(allIDs), "ids")

	# --------------------------------------------------
	print("Remove img href wrappers")

	alist = soup.find_all("a")
	for a in alist:
		imgs = a.find_all("img")
		if len(imgs) == 1:
			img = imgs[0]
			if img.parent.name == "a":
				img.parent.unwrap()

	# --------------------------------------------------
	print("Renaming and organizing media files", end="", flush=True)

	yearCounts = {}

	fileRename = {}
	allNewNames = set()
	oldNameTotal = 0
	newNameTotal = 0

	createFolder(os.path.join(dstFolder, mediaFolder))

	srcMediaPath = "/".join(srcFolder.split("/")[:-1])
	
	copyCount = 0

	def yearDivWithYear(year):
		yearDiv = soup.new_tag("div")
		yearDiv.string = str(year)
		yearDiv['class'] = "year-mark"
		return yearDiv
	
	def dimensionsOfImage(path):
		image = Image.open(path)
		if image is not None:
			return image.size
		else:
			return 0, 0
		
	def dimensionsOfVideo(path):
		cap = cv2.VideoCapture(path)
		if cap.isOpened():
			width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
			height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
			cap.release()
			return width, height
		else:
			return 0, 0

	for entry in entries:
		date = entry.itemdate
		yearMonth = date.year*100 + date.month
		if date.year in yearCounts:
			yearCounts[date.year] += 1
		else:
			yearCounts[date.year] = 1
			entry.insert_before(yearDivWithYear(date.year))
		addClass(entry, "d" + str(date.month*100 + date.day))

		imgs = entry.find_all(["img", "video"])
		if (len(imgs) > 0):
			for i, tagimg in enumerate(imgs):
				oldName = tagimg['src']
				if not oldName.startswith("http"):
					extension = oldName.split(".")[-1]
					newDateStr = os.path.join(str(yearMonth), str(date.day*1000000 + date.hour*10000 + date.minute*100 + date.second))
					newName = "{}.{}".format(os.path.join(mediaFolder, newDateStr), extension)
					index = 2
					while newName in allNewNames:
						newName = "{}-{}.{}".format(os.path.join(mediaFolder, newDateStr), index, extension)
						index += 1
					allNewNames.add(newName)
					fileRename[oldName] = newName
					tagimg['src'] = newName
					destPath = os.path.join(dstFolder, newName)
					copyFile(os.path.join(srcMediaPath, oldName), destPath)
						# print(f"Copied {oldName} to {newName}")
					width = 0
					height = 0
					if tagimg.name == 'img':
						width, height = dimensionsOfImage(destPath)
					elif tagimg.name == 'video':
						width, height = dimensionsOfVideo(destPath)
					if width > 0:
						tagimg['width'] = width
						tagimg['style'] = f"aspect-ratio:{width}/{height};"
						tagimg['loading'] = "lazy"
					copyCount += 1
					if copyCount % 10 == 1:
						print(".", end="", flush=True)
					oldNameTotal += len(oldName)
					newNameTotal += len(newName)

	print("")
	print("Copied", copyCount, "files")

	# --------------------------------------------------
	print("Retrieve static graphics")

	for img in soup.find_all("img"):
		src = img['src']
		if src.startswith(staticPrefix):
			if src.endswith(".gif") or src.endswith(".png"):
				newName = src.removeprefix(staticPrefix)
				newName = newName.replace("/", "_")
				nameParts = newName.split(".")
				extension = nameParts[-1]
				newName = "_".join(nameParts[:-1]) + "." + extension
				newSrc = os.path.join(mediaFolder, staticImageFolder, newName)
				destPath = os.path.join(dstFolder, newSrc)
				if not fileExists(destPath):
					createFolder(destPath)
					response = requests.get(src)
					if response.status_code == 200:
						with open(destPath, 'wb') as f:
							f.write(response.content)
						img['src'] = newSrc
						print(f"Downloaded {src} to {destPath}")
					else:
						print(f"Failed to download {src}")
				width, height = dimensionsOfImage(destPath)
				if width > 0:
					img['width'] = width
					img['style'] = f"aspect-ratio:{width}/{height};"
			else:
				print("Unknown static image type:", src)
		elif src.startswith("http"):
			print("External file:", src)

	# --------------------------------------------------
	print("Split entries into blocks")

	entries = soup.find_all("div", class_=["_a6-g", "year-mark"])

	entryCount = len(entries)
	itemsPerBlock = 200
	itemStartIndex = 40
	htmlBlocks = [""]
	blockCounts = [itemStartIndex]

	while itemStartIndex < entryCount:
		if itemStartIndex + itemsPerBlock * 1.5 > entryCount:
			itemsPerBlock = entryCount - itemStartIndex
		items = entries[itemStartIndex:itemStartIndex+itemsPerBlock]
		blockCounts.append(len(items))
		itemStartIndex += itemsPerBlock
		for item in items:
			item.extract()
		newdiv = soup.new_tag("div")
		newdiv.extend(items)
		htmlBlocks.append(newdiv)
	htmlBlocks[0] = soup

	print("Number of entries:", len(entries))
	print("Number of blocks:", len(htmlBlocks))
	print("Block counts:", blockCounts)
	print("Media items:", len(fileRename))
	print("Total name usage went from", oldNameTotal, "to", newNameTotal)

	# --------------------------------------------------
	print("Fix styles")

	styletag = soup.find("style")
	sstyle = str(styletag.string)
	styles = sstyle.split("}")

	styleDict = {}
	for i,style in enumerate(styles):
		parts = style.split("{")
		if len(parts) == 2:
			items = parts[1].split(";")
			itemDict = {}
			for item in items:
				pieces = item.split(":")
				itemDict[pieces[0]] = pieces[1]
			styleDict[parts[0]] = itemDict

	def removeStyle(selector, property, styleDict):
		if selector in styleDict:
			item = styleDict[selector]
			if property in item:
				item.pop(property)

	def addStyle(selector, property, value, styleDict):
		if selector in styleDict:
			item = styleDict[selector]
		else:
			item = {}
			styleDict[selector] = item
		item[property] = value

	removeStyle("._2pin", "padding-bottom", styleDict)
	removeStyle("._a7nf", "padding-left", styleDict)
	removeStyle("._a72d", "padding-bottom", styleDict)
	removeStyle("._a7ng", "padding-right", styleDict)
	removeStyle("._3-96", "margin-bottom", styleDict)
	removeStyle("._a706", "width", styleDict)
	removeStyle("._a706", "float", styleDict)

	if isFacebook:
		addStyle("._bot4", "padding-bottom", "4px", styleDict)
	else:
		removeStyle("._3-95", "margin-bottom", styleDict)
		removeStyle("._a6-i", "border-bottom", styleDict)
		removeStyle("._2ph_", "padding", styleDict)
		addStyle("._top4", "padding-top", "4px", styleDict)

	addStyle("._a6-g", "margin-top", "12px", styleDict)
	addStyle("._a6-g", "border-radius", "16px", styleDict)
	addStyle("._a6-g", "position", "relative", styleDict)
	addStyle("._a7nf", "column-gap", "12px", styleDict)
	addStyle("._top0", "padding-top", "0px", styleDict)
	addStyle("._a706", 'margin-top', '-12px', styleDict)
	addStyle("._a705", 'max-width', '800px', styleDict)

	keysToDelete = []
	for key in styleDict.keys():
		keepKey = False
		selectors = re.split('[ ,]', key)
		for selector in selectors:
			s = str(selector)
			if s.startswith("."):
				if selector in allClasses:
					keepKey = True
			elif s.startswith("#"):
				if selector in allIDs:
					keepKey = True
			elif selector in allNames:
				keepKey = True
		if not keepKey:
			keysToDelete.append(key)

	for key in keysToDelete:
		styleDict.pop(key)

	print("Removed", len(keysToDelete), "styles")

	styleList = []
	for key in styleDict.keys():
		itemList = []
		items = styleDict[key]
		for itemKey in items.keys():
			itemList.append(itemKey + ":" + items[itemKey])
		listStr = ";".join(itemList)
		styleList.append(key+"{"+listStr)

	styleList.append("")
	newStyle = "}".join(styleList)

	styletag.string.replace_with(newStyle)

	# --------------------------------------------------
	print("Add style sheet")

	linkTag = soup.new_tag("link", href=os.path.join(assetsFolder, styleName))
	linkTag['rel'] = "stylesheet"
	soup.head.append(linkTag)

	# --------------------------------------------------
	print("Add computed values")

	years = sorted(yearCounts.keys())
	yearCounts = [yearCounts[year] for year in years]

	scripttag = soup.new_tag("script")
	varString = f"var numSrcFiles = {str(len(htmlBlocks)-1)};" \
				f"var allYears = [{','.join(map(str, years))}];" \
				f"var yearCounts = [{','.join(map(str, yearCounts))}];" \
				f"var numEntries = {str(len(entries))};"
	
	scripttag.append(varString)
	soup.head.append(scripttag)

	# --------------------------------------------------
	print("Add scripts")

	scripttag = soup.new_tag("script")
	scripttag['src'] = os.path.join(assetsFolder, appName)
	soup.head.append(scripttag)

	# --------------------------------------------------
	print("Write html files")
	totalBytes = 0

	with open(os.path.join(dstFolder, indexName), "w") as f:
		totalBytes += f.write(str(soup))

	if (len(htmlBlocks) > 0):
		entriesPath = os.path.join(dstFolder, entryFolder)
		createFolder(entriesPath)

		for i in range(1, len(htmlBlocks)):
			with open(os.path.join(entriesPath, entryName.format(str(i))), "w") as f:
				totalBytes += f.write(str(htmlBlocks[i]))

	print("Wrote", totalBytes, "bytes")

if __name__ == '__main__':
	processData()
