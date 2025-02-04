#!python3

# pip3 install --upgrade pip
# pip3 install beautifulsoup4
# pip3 install lxml
# pip3 install dateutil
# pip3 install requests
# pip3 install Pillow
# pip3 install opencv-python
# pip3 install rich
# pip3 install textual textual-dev

# for Windows only:
# pip3 install windows-filedialogs

from bs4 import BeautifulSoup, NavigableString, Tag
import re
from dateutil.parser import parse
from enum import Enum
import subprocess, sys, os, shutil
import requests
import argparse
from PIL import Image
import cv2
import platform
import copy
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, Task
from rich.text import Text
from rich.padding import Padding
from rich.theme import Theme
from rich.panel import Panel

from textual.app import App, ComposeResult, RenderResult
from textual.screen import Screen
from textual.widgets import Button, Digits, Footer, Header, Label, ProgressBar, Input, Placeholder, Static, Checkbox, Switch
from textual.containers import Horizontal, Vertical
from textual.widget import Widget

assetsFolder = "assets"
entryFolder = "entries"
mediaFolder = "media"
staticImageFolder = "static"
indexName = "index.html"
excludedName = "excluded.html"
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

bannerFormat = "$N - $M Posts - $S to $E"

parser = argparse.ArgumentParser(description='Process FB Data Download')

parser.add_argument("-i", dest="srcFolder", help="Path to <your_facebook_activity folder>", type=str, default=None)
parser.add_argument("-o", dest="dstFolder", help="Path to output folder", type=str, default=None)

parser.add_argument("-b", "--birthdays", dest="birthdays", help="Include birthday posts", action="store_true")
parser.add_argument("-si", "--show-indexes", dest="showIndexes", help="Always show the index numbers for entries", action="store_true")
parser.add_argument("-xl", "--exclude-list", dest="exlist", help="Generate an html page with the excluded entries", action="store_true")

group = parser.add_argument_group("exclusion list")
group.add_argument("-x", "--exclude", dest="exclude", help="Comma separated list of numbers to exclude", type=str, default="")
group.add_argument("-xfb", "--exclude-fb", dest="excludefb", help="Comma separated list of numbers to exclude from Facebook data", type=str, default="")
group.add_argument("-xig", "--exclude-ig", dest="excludeig", help="Comma separated list of numbers to exclude from Instagram data", type=str, default="")

group = parser.add_argument_group("banner options")
group.add_argument("-nb", "--no-banner", dest="noBanner", help="Suppress banner at top of entry list", type=str, default="")
group.add_argument("-u", "--user-name", dest="userName", help="Name for banner, if omitted will be inferred from data", type=str, default="")
group.add_argument("-bf", "--banner-format", dest="bannerFormat", help=f"Banner format string, use $N for name, $M for facebook/instagram, $S for start date, $E for end date - defaults to '{bannerFormat}'", type=str, default=bannerFormat)

args = parser.parse_args()

scriptPath = os.path.abspath(os.path.dirname(sys.argv[0]))

theme = Theme({
			"progress.percentage": "white",
			"progress.remaining": "green",
			"progress.elapsed": "cyan",
			"bar.complete": "green",
			"bar.finished": "green",
			"bar.pulse": "green",
			"repr.ellipsis": "white",
			"repr.number": "white",
			"repr.path": "white",
			"repr.filename": "white"
			# "progress.data.speed": "white",
			# "progress.description": "none",
			# "progress.download": "white",
			# "progress.filesize": "white",
			# "progress.filesize.total": "white",
			# "progress.spinner": "white",
			})

prog_description = "[progress.description]{task.description}"
prog_percentage = "[progress.percentage]{task.percentage:>3.0f}% "

console = Console(theme=theme)

def pluralize(str, count, pad=False):
	return "{:d} {}{}".format(count, str, "s" if count!=1 else " " if pad else "")

def printNow(str):
	console.print(str, end="")

def printError(*args, dest_console=console):
	message = args[0] if len(args) >= 1 else None
	item = args[1] if len(args) >= 2 else None
	error_message = args[2] if len(args) >= 3 else None

	if item and not isinstance(item, str):
		item = str(item)
	if error_message and not isinstance(error_message, str):
		error_message = str(error_message)

	error_color = "[bold red]"
	error_item_color = "[magenta]"
	error_message_color = "[yellow]"

	parts = []
	if message:
		parts.extend([error_color, message])
	if item:
		parts.extend([error_item_color, item])
	if error_message:
		if len(parts)>0:
			parts.extend([error_color, " - "]) 
		parts.extend([error_message_color, error_message]) 

	dest_console.print("".join(parts))

	# with Progress(prog_description, BarColumn(), prog_percentage, console=console) as progress:
		# with Progress(prog_description, BarColumn(), prog_percentage, StyledElapsedColumn(), prog_rate, console=console) as progress:
		# 	task = progress.add_task("Creating {}".format(pluralize("image", image_count)), total=image_count, ips=0, color="conceal")
		# 			image_rate = completed_count / (time.time() - image_process_start)
		# 			progress.update(task, advance=1, ips=image_rate, color="bright_green")
		# 	progress.update(task, refresh=True, color="conceal")

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
		console.print(f"Error creating folder '{path}': {e}")
		return False

def copyFile(srcPath, dstPath):
	if not os.path.isfile(dstPath) or os.path.getsize(srcPath) != os.path.getsize(dstPath):
		try:
			os.makedirs(os.path.dirname(dstPath), exist_ok=True)
			shutil.copy(srcPath, dstPath)
			return True
		except OSError as e:
			console.print(f"Error copying '{srcPath}' to '{dstPath}' - {e}")
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

	console.print(f"src={srcFolder}\ndst={dstFolder}")

	# --------------------------------------------------
	console.print("Check Data Type")

	if os.path.basename(srcFolder) == fbFolderName:
		console.print("Processing Facebook Data")
		isFacebook = True
	elif os.path.basename(srcFolder) == igFolderName:
		console.print("Processing Instagram Data")
		isFacebook = False
	else:
		console.print("Unknown source data folder!")
		return

	# --------------------------------------------------
	console.print("Open Main Data File")

	srcDataCount = 0

	if isFacebook:
		mainSrcFile = os.path.join(srcFolder, postsFolder, mainPostsName)
	else:
		mainSrcFile = os.path.join(srcFolder, contentFolder, igPostsName)

	srcDataCount += os.path.getsize(mainSrcFile)
	with open(mainSrcFile) as fp:
		soup = BeautifulSoup(fp, 'lxml')

	# --------------------------------------------------
	console.print("Cleaning destination folder...")

	folderList = [entryFolder, assetsFolder, mediaFolder]
	fileList = [indexName, excludedName]
	foldersRemoved = 0
	filesRemoved = 0
	for name in os.listdir(dstFolder):
		path = os.path.join(dstFolder, name)
		if name in folderList:
			shutil.rmtree(path)
			foldersRemoved += 1
		elif name in fileList:
			os.remove(path)
			filesRemoved += 1
	if filesRemoved>0 or foldersRemoved>0:
		console.print(f"removed {foldersRemoved} folders and {filesRemoved} files.")
	else:
		console.print("done.")

	# --------------------------------------------------
	console.print("Copying Assets folder...")

	destAssetsPath = os.path.join(dstFolder, assetsFolder)
	if os.path.isdir(destAssetsPath):
		shutil.rmtree(destAssetsPath)
	if not os.path.isdir(destAssetsPath):
		srcAssetsPath = os.path.join(scriptPath, assetsFolder)
		try:
			shutil.copytree(srcAssetsPath, destAssetsPath)
			console.print(" done.")
		except OSError as e:
			console.print(f"\nError copying: {destAssetsPath}, {e}");

	# --------------------------------------------------
	console.print("Build used file list")

	usedFiles = set()

	mainEntries = soup.find("div", class_="_a6-g").parent
	for entry in mainEntries:
		imgs = entry.find_all(["img", "video"])
		for img in imgs:
			src = img['src']
			if not src.startswith("http"):
				usedFiles.add(src)

	# --------------------------------------------------

	def mergeAlbumSoup(albumSoup, name):
		firstDiv = albumSoup.find("div", class_="_a6-g")
		if firstDiv:
			albumList = list(firstDiv.parent.children)
			listCount = len(albumList)
			addedCount = 0
			for entry in albumList:
				skip = False
				imgs = entry.find_all(["img", "video"])
				for img in imgs:
					src = img['src']
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
					if len(entry.contents) == 2:
						newDiv = soup.new_tag("div")
						label = entry.find("div", class_= "_3-95")
						if label != None and label.string != None:
							newDiv.string = label.string
						else:
							newDiv.string = " "
						newDiv['class'] = ["_2ph_", "_a6-h", "_bot4"]
						entry.insert(0, newDiv)
					mainEntries.append(entry)
					addedCount += 1
			console.print(f"Added {addedCount} out of {listCount} entries from the album '{name}'")

	def mergeSoupFile(soupPath):
		nonlocal srcDataCount
		srcDataCount += os.path.getsize(soupPath)
		with open(soupPath) as fp:
			soup2 = BeautifulSoup(fp, 'lxml')
			mergeAlbumSoup(soup2, os.path.basename(soupPath))

	if isFacebook:
		console.print("Merge Photos")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, yourPhotos))

		console.print("Merge Videos")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, yourVideos))

		console.print("Merge Other Posts")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, otherPostsName))

		albumsFolder = os.path.join(srcFolder, postsFolder, albumsFolderName)
		albumFiles = [f for f in os.listdir(albumsFolder) if f.endswith(".html")]

		console.print(f"Merge {len(albumFiles)} albums")
		for albumFile in albumFiles:
			mergeSoupFile(os.path.join(albumsFolder, albumFile))

	# --------------------------------------------------
	console.print("Remove unneeded elements")

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
	console.print("Remove Facebook links")

	fblinks = soup.find_all("a", href=re.compile(".*facebook\.com"))
	for flink in fblinks:
		p = flink.parent
		flink.unwrap()
		p.smooth()

	# --------------------------------------------------
	console.print("Remove GPS coordinates")

	def isAPlace(tag):
		if (tag.name == "div"):
			if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
				if tag.string.startswith("Place: "):
					return True
		return False

	places = soup.find_all(isAPlace)
	for place in places:
		place.string = re.sub(" \(-?\d+.?\d*, ?-?\d+.?\d*\)", "", place.string).replace("Place: ", "")
		place.unwrap()

	# --------------------------------------------------
	console.print("Remove Addresses")

	addresses = soup.find_all("div", string=re.compile("^Address: "))
	for address in addresses:
		address.decompose()

	# --------------------------------------------------
	console.print("Reformat entries")

	def addClass(tag, c):
		if isinstance(c, list):
			for cls in c:
				addClass(tag, cls)
		else:
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

	firstDate = None
	lastDate = None

	entries = soup.find_all("div", class_="_a6-g")
	entryOuter = entries[0].parent
	for entry in entries:
		if isFacebook:
			kids = list(entry.children)
			if len(kids) == 3 and kids[0].string != None:
				twop = kids[1].find_all("div", class_="_2pin")
				if len(twop) == 2:
					if len(twop[1].contents) == 2 and isinstance(twop[1].contents[0], NavigableString):
						kids[0].string.replace_with(twop[1].contents[0])
						twop[1].contents[0].extract()
						# kids[0].string.replace_with(", ".join(list(twop[1].contents[0].strings)))
						# twop[1].decompose()
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
				if len(entry.contents) == 2:
					newDiv = soup.new_tag("div")
					newDiv.string = " "
					newDiv['class'] = ["_2ph_", "_a6-h"]
					entry.insert(0, newDiv)
				entry.insert(1, a6o[0].extract())
				if len(entry.contents) == 3:
					addClass(kids[0], "_top4")
					addClass(kids[2], "_top0")

		entry.extract()
		itemDate = entry.itemdate
		if firstDate == None or itemDate < firstDate:
			firstDate = itemDate
		if lastDate == None or itemDate > lastDate:
			lastDate = itemDate

	# --------------------------------------------------
	console.print("Sort entries")

	entries.sort(key=lambda x: x.itemdate, reverse=True)
	entryOuter.extend(entries)

	# --------------------------------------------------
	console.print("Remove unneeded headings")

	userName = args.userName

	patterns = [
		re.compile("(.*) shared a link\."),
		re.compile("(.*) updated .* status\."),
		re.compile("(.*) shared a post\."),
		re.compile("(.*) shared an album\."),
		re.compile("(.*) added a new video.*\."),
		re.compile("(.*) added a new photo.*\."),
		re.compile("(.*) shared a memory\."),
		re.compile("(.*) posted something via Facebook.*\.")
	]

	headings = soup.find_all("div", string=patterns)
	for heading in headings:
		if not args.noBanner and userName == "":
			for pattern in patterns:
				match = pattern.match(heading.string)
				if match:
					userName = match.group(1)
					break
		heading.string.replace_with("")

	# --------------------------------------------------
	didBanner = False

	if not args.noBanner:
		a706 = soup.find("div", class_="_a706")
		if a706 != None:
			console.print("Create banner")

			newDiv = soup.new_tag("div")
			newDiv['class'] = "banner"

			typeString = "Facebook" if isFacebook else "Instagram"
			startDate = firstDate.strftime("%b %d, %Y")
			endDate = lastDate.strftime("%b %d, %Y")
			format = args.bannerFormat

			bannerText = format.replace("$N", userName).replace("$M", typeString).replace("$S", startDate).replace("$E", endDate)
			newDiv.string = bannerText
			a706.insert_before(newDiv)
			didBanner = True

	# --------------------------------------------------
	console.print("Clean up tags")

	class Clean(Enum):
		Ok = 0
		Remove = 1
		Unwrap = 2
		Merge = 3

	simpleDivCount = 0

	def cleanTag(tag, indent=0):
		nonlocal simpleDivCount

		classCount = 0
		classes = tag.get('class')
		if classes:
			classCount = len(classes)
		for subTag in reversed(tag.contents):
			if not isinstance(subTag, NavigableString):
				result = cleanTag(subTag, indent+1)
				if result == Clean.Remove:
					subTag.decompose()
				elif result == Clean.Unwrap:
					subTag.unwrap()
		count = len(tag.contents)
		if tag.name == "div" and count == 0:
			return Clean.Remove
		elif tag.name == "div" and classCount == 0:
			return Clean.Unwrap
		elif tag.name == "div" and count == 1 and tag.contents[0].name == "div":
			simpleDivCount += 1
			addClass(tag, tag.contents[0]['class'])
			tag.contents[0].unwrap()			
			return Clean.Ok
		else:
			return Clean.Ok

	cleanTag(soup.body)
	console.print(f"Cleaned {simpleDivCount} simple divs")

	# --------------------------------------------------
	console.print("Add entry numbers")

	entries = soup.find_all("div", class_="_a6-g")
	for i, entry in enumerate(entries):
		entry['eix'] = str(i)

	# --------------------------------------------------
	console.print("Remove Updated... strings")

	isUpdated = re.compile("^Updated \w{3} \d{2}, \d{4} \d{1,2}:\d{2}:\d{2} [ap]m")
	pin2s = soup.find_all("div", class_="_2pin")
	for pin in pin2s:
		for string in reversed(list(pin.strings)):
			if isUpdated.match(string):
				string.extract()

	# --------------------------------------------------
	def removeEmptyStrings():
		console.print("Remove sequential and starting/ending empty strings")

		emptyStringCount = 0

		def isEmptyString(tag):
			if isinstance(tag, NavigableString):
				return tag.string == "" or tag.string == " "
			else:
				return tag.name and tag.name == "br"

		entries = soup.find_all("div", class_="_a6-g")
		for entry in entries:
			pin2s = entry.find_all("div", class_="_2pin")
			for pin in pin2s:
				for i in range(len(pin.contents)-2, 0, -1):
					if isEmptyString(pin.contents[i]) and isEmptyString(pin.contents[i+1]):
						pin.contents[i].extract()
						emptyStringCount += 1
						
				if len(pin.contents) > 0 and isEmptyString(pin.contents[0]):
					pin.contents[0].extract()
					emptyStringCount += 1
				if len(pin.contents) > 0 and isEmptyString(pin.contents[-1]):
					pin.contents[-1].extract()
					emptyStringCount += 1
		
		console.print(f"Removed {emptyStringCount} empty strings")

	removeEmptyStrings()

	# --------------------------------------------------
	console.print("Remove duplicate and birthday tags")

	isBirthday = re.compile("^ha+p{2,}y .*birthday.*", re.IGNORECASE)

	entries = soup.find_all("div", class_="_a6-g")
	deletedEntries = set()
	for entry in entries:
		pin2 = entry.find_all("div", class_="_2pin")
		for item in pin2:
			divs = item.find_all("div")
			if len(divs)==2:
				str1 = "".join(divs[0].stripped_strings)
				if len(str1) > 0:
					str2 = "".join(divs[1].stripped_strings)
					if str1 == str2:
						divs[1].decompose()
			if not args.birthdays:
				for string in item.strings:
					if isBirthday.match(string):
						deletedEntries.add(entry)
						break
		atags = entry.find_all("a")
		if len(atags) == 2:
			if atags[0].string and len(atags[0].string) > 0 and atags[0].string == atags[1].string:
				a0ParentString = "".join(atags[0].parent.stripped_strings)
				a1ParentString = "".join(atags[1].parent.stripped_strings)
				if len(a0ParentString) < len(a1ParentString):
					atags[0].parent.decompose()
				else:
					atags[1].parent.decompose()

	for item in deletedEntries:
		item.decompose()

	console.print(f"Deleted {len(deletedEntries)} birthday entries")

	# --------------------------------------------------
	console.print("Clean up titles")

	def tagIsEmpty(tag):
		if len(tag.contents) == 0:
			return True
		elif len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString) and tag.contents[0].string == "":
			return True
		else:
			return False

	if isFacebook:
		entries = soup.find_all("div", class_="_a6-g")
		for entry in entries:
			a6h = entry.find("div", class_="_a6-h")
			a6p = entry.find("div", class_="_a6-p")
			if a6h != None and a6p != None:
				if a6h.string == "" or a6h.string == " ":
					pin2s = entry.find_all("div", class_="_2pin")
					if len(pin2s) > 0 and len(pin2s) <= 2:
						foundStrings = []
						stringsToRemove = []
						foundTitle = ""
						for p2 in pin2s:
							p2.smooth()
							for string in list(p2.strings):
								if len(string) > 0 and string != " " and not string.startswith("http"):
									text = str(string)
									if foundTitle == "":
										foundTitle = text
										foundStrings.append(text)
										stringsToRemove.append(string)
									elif text in foundStrings:
										stringsToRemove.append(string)
									else:
										foundStrings.append(text)
						if foundTitle != "":
							a6h.string.replace_with(foundTitle)
							for string in stringsToRemove:
								string.extract()
				if tagIsEmpty(a6h) and tagIsEmpty(a6p):
					entry.decompose()
			else:
				if len(entry.contents) == 2:
					pin2s = entry.find_all("div", class_="_2pin")
					if len(pin2s) == 2 and pin2s[1].string != None:
						second = entry.contents[1]
						second.extract()
						entry.insert(0, second)
						newDiv = soup.new_tag("div")
						newDiv.string = pin2s[1].string
						newDiv['class'] = ["_2ph_", "_a6-h", "_bot4"]
						pin2s[1].decompose()
						entry.insert(0, newDiv)	

	removeEmptyStrings()

	# --------------------------------------------------
	console.print("Count tags")

	allClasses = set()
	allNames = set()
	allIDs = set()
	for item in soup.descendants:
		if isinstance(item, Tag):
			classes = item.get('class')
			if classes:
				if not isinstance(classes, list):
					classes = [classes]
				for c in classes:
					allClasses.add(f'.{c}')
			if item.name and item.name not in allNames:
				allNames.add(item.name)
			if item.get('id'):
				allIDs.add(item['id'])

	console.print(f"There are {len(allNames)} tags")
	console.print(f"There are {len(allClasses)} classes")
	console.print(f"There are {len(allIDs)} ids")

	# --------------------------------------------------
	console.print("Remove img/video <a> wrappers")

	alist = soup.find_all("a")
	for a in reversed(alist):
		imgs = a.find_all(["img", "video"])
		if len(imgs) == 1:
			img = imgs[0]
			if img.parent.name == "a":
				img.parent.unwrap()
		elif len(imgs) == 0 and (a.string == "" or a.string == " " or a.string == None):
			a.decompose()
		elif len(imgs) == 0 and a.get('href') != None and "your_facebook" in a['href']:
			a.decompose()

	# --------------------------------------------------
	yearCounts = {}

	fileRename = {}
	allNewNames = set()
	oldNameTotal = 0
	newNameTotal = 0

	createFolder(os.path.join(dstFolder, mediaFolder))

	srcMediaPath = os.path.dirname(srcFolder)
	
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

	def extractFirstFrameToFile(videoPath, posterPath):
		vidcap = cv2.VideoCapture(videoPath)

		fps = vidcap.get(cv2.CAP_PROP_FPS)
		frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
		durationMS = frame_count * 1000 / fps
		posterTimeMS = int(min(1000, durationMS / 2))
		vidcap.set(cv2.CAP_PROP_POS_MSEC, posterTimeMS)

		success, image = vidcap.read()
		if success:
			cv2.imwrite(posterPath, image)  # Save the frame as an image
			return True
		else:
			return False

	# --------------------------------------------------
	# Exclusion List

	deletedEntries = []
	xstring = ""

	if isFacebook:
		xstring = args.excludefb
	else:
		xstring = args.excludeig

	if xstring == "":
		xstring = args.exclude

	def excludeEntries():
		if xstring != "":
			console.print("Remove excluded entries")
			xlist = xstring.split(",")
			entries = soup.find_all("div", class_="_a6-g")
			for i, entry in enumerate(entries):
				if entry['eix'] in xlist:
					deletedEntries.append(entry)

			for item in deletedEntries:
				item.extract()

	if not args.exlist:
		excludeEntries()

	# --------------------------------------------------
	# console.print("Renaming and organizing media files")

	with Progress(prog_description, BarColumn(), prog_percentage, console=console) as progress:
		entries = soup.find_all("div", class_="_a6-g")
		task = progress.add_task("Organizing Media...", total=len(entries))

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
						posterName = newName.replace("mp4", "jpg")
						index = 2
						while newName in allNewNames or posterName in allNewNames:
							newName = "{}-{}.{}".format(os.path.join(mediaFolder, newDateStr), index, extension)
							posterName = newName.replace("mp4", "jpg")
							index += 1
						allNewNames.add(newName)
						fileRename[oldName] = newName
						tagimg['src'] = newName
						destPath = os.path.join(dstFolder, newName)
						copyFile(os.path.join(srcMediaPath, oldName), destPath)
						width = 0
						height = 0
						if tagimg.name == 'img':
							width, height = dimensionsOfImage(destPath)
							tagimg['loading'] = "lazy"
						elif tagimg.name == 'video':
							width, height = dimensionsOfVideo(destPath)
							width = int(width)
							height = int(height)
							if not extractFirstFrameToFile(destPath, os.path.join(dstFolder, posterName)):
								console.print(f"\nUnable to get poster frame for{destPath}\n")
							tagimg['preload'] = "none"
							tagimg['poster'] = posterName

						if width > 0:
							tagimg['width'] = width
							tagimg['style'] = f"aspect-ratio:{width}/{height};"
						copyCount += 1
						oldNameTotal += len(oldName)
						newNameTotal += len(newName)
			progress.update(task, advance=1)


	# console.print("")
	# console.print(f"Copied {copyCount} files")

	# --------------------------------------------------
	console.print("Retrieve static graphics")

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
						console.print(f"Downloaded {src} to {destPath}")
					else:
						console.print(f"Failed to download {src}")
				width, height = dimensionsOfImage(destPath)
				if width > 0:
					img['width'] = width
					img['style'] = f"aspect-ratio:{width}/{height};"
			else:
				console.print(f"Unknown static image type: {src}")
		elif src.startswith("http"):
			console.print(f"External file: {src}")

	# --------------------------------------------------
	if args.exlist:
		excludeEntries()

	# --------------------------------------------------
	console.print("Split entries into blocks")

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

	# --------------------------------------------------
	console.print("Fix styles")

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
	addStyle("._a705", 'padding-left', 'calc(var(--nav-width,0))', styleDict)

	if didBanner:
		addStyle(".banner", 'padding', '20px', styleDict)
		addStyle(".banner", 'text-align', 'center', styleDict)
		addStyle(".banner", 'font-weight', '600', styleDict)
		addStyle(".banner", 'font-size', '18px', styleDict)

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

	console.print(f"Removed {len(keysToDelete)} styles")

	styleList = []
	for key in styleDict.keys():
		itemList = []
		items = styleDict[key]
		for itemKey in items.keys():
			itemList.append(itemKey + ":" + items[itemKey])
		if len(itemList) > 0:
			listStr = ";".join(itemList)
			styleList.append(key+"{"+listStr)

	styleList.append("")
	newStyle = "}".join(styleList)

	styletag.string.replace_with(newStyle)

	# --------------------------------------------------
	console.print("Add style sheet")

	linkTag = soup.new_tag("link", href=os.path.join(assetsFolder, styleName))
	linkTag['rel'] = "stylesheet"
	soup.head.append(linkTag)

	# --------------------------------------------------
	excludeSoup = None
	if args.exlist:
		console.print("Copy structure for exluded entries page")
		excludeSoup = copy.copy(soup)

	# --------------------------------------------------
	console.print("Add computed values")

	years = sorted(yearCounts.keys())
	yearCounts = [yearCounts[year] for year in years]

	scripttag = soup.new_tag("script")
	varString = f"var numSrcFiles = {str(len(htmlBlocks)-1)};" \
				f"var allYears = [{','.join(map(str, years))}];" \
				f"var yearCounts = [{','.join(map(str, yearCounts))}];" \
				f"var numEntries = {str(len(entries))};" \
				
	if args.showIndexes:
		varString += f"var showIndexes = true;"
	
	scripttag.append(varString)
	soup.head.append(scripttag)

	# --------------------------------------------------
	console.print("Add scripts")

	def addMainScript(sp):
		scripttag = sp.new_tag("script")
		scripttag['src'] = os.path.join(assetsFolder, appName)
		sp.head.append(scripttag)

	addMainScript(soup)

	# --------------------------------------------------
	if args.exlist and excludeSoup != None:
		console.print("Create excluded entries page")
		addMainScript(excludeSoup)
		wrapper = excludeSoup.find("div", class_="_a706")
		if wrapper != None:
			for entry in reversed(wrapper.contents):
				entry.decompose()
			for entry in deletedEntries:
				wrapper.append(entry)
			with open(os.path.join(dstFolder, excludedName), "w") as f:
				f.write(str(excludeSoup))
		
	# --------------------------------------------------
	console.print("Write html files")
	totalBytes = 0

	with open(os.path.join(dstFolder, indexName), "w") as f:
		totalBytes += f.write(str(soup))

	if (len(htmlBlocks) > 0):
		entriesPath = os.path.join(dstFolder, entryFolder)
		createFolder(entriesPath)

		for i in range(1, len(htmlBlocks)):
			with open(os.path.join(entriesPath, entryName.format(str(i))), "w") as f:
				totalBytes += f.write(str(htmlBlocks[i]))

	console.print(f"Number of entries: {len(entries)}")
	console.print(f"Number of blocks: {len(htmlBlocks)}")
	console.print(f"Block counts: {blockCounts}")
	console.print(f"Media items: {len(fileRename)}")
	console.print(f"Total name usage went from {oldNameTotal}  to {newNameTotal}")

	console.print(f"Read {srcDataCount} bytes")
	console.print(f"Wrote {totalBytes} bytes")

class DirectoryPicker(Widget):
	DEFAULT_CSS = """
	DirectoryPicker {
		height: 1;
	}
	DirectoryPicker Button {
		height: 1;
		border: hidden;
		padding: 0;
		width: 12;
		text-align: right;
		padding-right: 2;
	}
	DirectoryPicker Label {
		background: #337;
		# color: white;
		padding: 0;
		height: 1;
		width: 1fr;
		margin-left: 2;
	}
	"""
	def __init__(self, label: str, message: str = "", path: str = None) -> None:
		self.label = label
		self.message = message
		self.path = None
		super().__init__()

	def compose(self) -> ComposeResult:
		with Horizontal():
			yield Button(self.label)
			yield Label(self.path if self.path else "<no directory selected>")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		self.path = getFolder(self.message)
		display = self.query_one(Label)
		display.update(self.path)

class LabeledString(Widget):
	DEFAULT_CSS = """
	LabeledString {
		width: 1fr;
		height: 1;
		margin: 1;
	}
	LabeledString Label {
		padding: 0;
		height: 1;
		width: 16;
		text-align: right;
	}
	LabeledString Input {
		background: #333;
		# color: white;
		width: 1fr;
		height: 1;
		border: hidden;
		margin-left: 2;
		margin-right: 4;
		padding: 0;
	}
	"""

	def __init__(self, label: str, value: str = "") -> None:
		self.label = label
		self.value = value
		super().__init__()

	def compose(self) -> ComposeResult:  
		with Horizontal():
			yield Label(self.label)
			yield Input(self.value)

class ExclusionList(Widget):
	DEFAULT_CSS = """
	ExclusionList {
		height: 3;
		padding: 0;
		border: hidden;
	}
	ExclusionList Label {
		padding: 0;
		width: 16;
		padding-right: 3;
		text-align: right;
		content-align: center middle;
	}
	ExclusionList Input {
		background: #333;
		# color: white;
		height: 3;
		border: hidden;
		margin-left: 2;
		margin-right: 4;
		padding: 0;
	}
	"""

	def __init__(self, value: str = None) -> None:
		self.value = value
		super().__init__()

	def compose(self) -> ComposeResult:  
		with Horizontal():
			yield Label("Exclude:")
			yield Input(self.value if self.value else "Add excluded entry numbers here...")

class ByeByeMeta(App):
	CSS = """
	Screen {
		align: center middle;
		padding: 0;
	}
	Header {
		height: 3;
		# background: blue;
		# color: white;
	}
	Footer {
		# background: blue;
		# color: white;
	}
	ExclusionList {
		width: 80%;
		margin: 1;
	}
	DirectoryPicker {
		margin: 1;
		margin-right: 8;
	}
	Checkbox {
		height: 1;
		width: auto;
		border: hidden;
		padding: 0;
		margin: 1;
		margin-left: 4;
	}
	#buttons {
		width: 30;
		margin: 0;
	}
	#buttons Button {
		width: 100%;
		height: 20%;
	}
	#box1 {
		margin: 1;
		margin-left: 14;
		margin-right: 40;
		# height: 1;
	}
	.divider1 {
		height: 2;
	}
	.margin1 {
		margin: 1;
	}
	"""

	def on_mount(self) -> None:
		self.theme = "textual-dark"
		# self.screen.styles.background = "#222"
		# self.screen.styles.border = ("hidden", "white")

	def compose(self) -> ComposeResult:
		with Vertical():
			yield Header()
			with Horizontal():
				with Vertical():
					yield DirectoryPicker(label="Source:", message="Select the source folder")
					yield DirectoryPicker(label="Output:", message="Select the output folder")
					yield ExclusionList()
					with Horizontal():
						with Vertical():
							yield LabeledString(label="User Name")
							yield LabeledString(label="Banner Format")
					with Horizontal(id="box1", classes="margin1"):
							with Vertical():
								yield Checkbox("Create Exclusion Page")
								yield Checkbox("Add Banner")
							with Vertical():
								yield Checkbox("Include Birthday Posts")
								yield Checkbox("Show Item Indexes")
				with Vertical(id="buttons"):
					yield Button("Process", variant="primary")
					yield Button.success("Open Browser")
					yield Button.error("Quit")
					yield Static("", id="divider1")
					yield Button.success("Show Log")
					yield Button.success("Show Controls")
			yield Footer()  

if __name__ == "__main__":
	app = ByeByeMeta()
	app.run()

# if __name__ == '__main__':
# 	console.print(Panel("[green]Begin ByeByeMeta"))
# 	processData()
