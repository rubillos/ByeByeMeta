#!python3

#*********************************************************************************
#  MIT License
#  
#  Copyright (c) 2025 Randy Ubillos
#  
#  https://github.com/rubillos/ByeByeMeta
#  
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#  
#*******************************************************************************/

# pip3 install --upgrade pip
# pip3 install beautifulsoup4
# pip3 install lxml
# pip3 install dateutil
# pip3 install requests
# pip3 install Pillow
# pip3 install opencv-python
# pip3 install rich

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
import webbrowser
import traceback

version = "v1.1"

assetsFolder = "assets"
entryFolder = "entries"
mediaFolder = "media"
staticImageFolder = "static"
indexName = "index.html"
excludedName = "excluded.html"
entryName = "entries{}.html"
appName = f"app.js?{version}"
styleName = f"style.css?{version}"
excludesListName = "excludes.txt"

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
parser.add_argument("-#", "--hashtags", dest="hashtags", help="Remove hashtags in headings", action="store_true")
parser.add_argument("-si", "--show-indexes", dest="showIndexes", help="Always show the index numbers for entries", action="store_true")
parser.add_argument("-xl", "--exclude-list", dest="exlist", help="Generate an html page with the excluded entries", action="store_true")
parser.add_argument("-s", "--show-result", dest="showResult", help="Show the page in your browser", action="store_true")

group = parser.add_argument_group("exclusion list")
group.add_argument("-x", "--excludes", dest="excludes", help="Comma separated list of entry numbers to exclude", type=str, default="")
group.add_argument("-xfb", "--excludes-fb", dest="excludesfb", help="Comma separated list of entry numbers to exclude from Facebook data", type=str, default="")
group.add_argument("-xig", "--excludes-ig", dest="excludesig", help="Comma separated list of entry numbers to exclude from Instagram data", type=str, default="")

group.add_argument("-ux", "--existing-excludes", dest="useExcludesFile", help="Use any existing excludes list file", action="store_true")

extendList = None
extendCmds = ["-xx", "--extend-excludes"]
group.add_argument(extendCmds[0], extendCmds[1], dest="extendExcludes", help="Comma separated list of entry numbers to add or remove from the existing excludes list. Positive numbers are added, negative numbers are removed.", type=str, default="")

group = parser.add_argument_group("banner options")
group.add_argument("-nb", "--no-banner", dest="noBanner", help="Suppress banner at top of entry list", type=str, default="")
group.add_argument("-u", "--user-name", dest="userName", help="Name for banner, if omitted will be inferred from data. (Put double quotes around)", type=str, default="")
group.add_argument("-bf", "--banner-format", dest="bannerFormat", help=f"Banner format string, use $N for name, $M for facebook/instagram, $S for start date, $E for end date - defaults to '{bannerFormat}'", type=str, default=bannerFormat)

for i in range(len(sys.argv)-1):
	if sys.argv[i] in extendCmds:
		extendList = sys.argv[i+1]
		del sys.argv[i+1]
		del sys.argv[i]
		break

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
			})

prog_description = "[progress.description]{task.description}"
prog_percentage = "[progress.percentage]{task.percentage:>3.0f}% "

console = Console(theme=theme)

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
	
lastOperation = ""
lastSubOperation = ""

def startOperation(name, print=True):
	global lastOperation, lastSubOperation
	if print:
		console.print(name)
	lastOperation = name
	lastSubOperation = ""

def startSubOperation(name, print=True):
	global lastSubOperation
	if print:
		console.print(f"  {name}")
	lastSubOperation = name

def processData():
	if args.srcFolder != None:
		srcFolder = args.srcFolder
	else:
		srcFolder = getFolder("Select the <your_facebook/instagram_activity folder>:")

	if srcFolder == None:
		return None
	
	if args.dstFolder != None:
		dstFolder = args.dstFolder
	else:
		dstFolder = getFolder("Select the destination folder:")

	if dstFolder == None:
		return None

	console.print(f"src={srcFolder}\ndst={dstFolder}")

	# --------------------------------------------------
	startOperation("Check Data Type")

	if os.path.basename(srcFolder) == fbFolderName:
		console.print("Processing Facebook Data")
		isFacebook = True
	elif os.path.basename(srcFolder) == igFolderName:
		console.print("Processing Instagram Data")
		isFacebook = False
	elif os.path.isdir(os.path.join(srcFolder, fbFolderName)):
		console.print("Processing Facebook Data")
		isFacebook = True
		srcFolder = os.path.join(srcFolder, fbFolderName)
	elif os.path.isdir(os.path.join(srcFolder, igFolderName)):
		console.print("Processing Instagram Data")
		isFacebook = False
		srcFolder = os.path.join(srcFolder, igFolderName)
	else:
		console.print("Unknown source data folder type!")
		return None

	# --------------------------------------------------
	startOperation("Open Main Data File")

	srcDataCount = 0

	if isFacebook:
		mainSrcFile = os.path.join(srcFolder, postsFolder, mainPostsName)
	else:
		mainSrcFile = os.path.join(srcFolder, contentFolder, igPostsName)

	srcDataCount += os.path.getsize(mainSrcFile)
	with open(mainSrcFile) as fp:
		soup = BeautifulSoup(fp, 'lxml')

	# --------------------------------------------------
	def askToUseExcludesFile():
		while True:
			answer = input("Use the existing excludes file? (y/n): ").lower()
			if answer == "y":
				return True
			elif answer == "n":
				return False

	xstring = ""

	if isFacebook:
		xstring = args.excludesfb
	else:
		xstring = args.excludesig

	if xstring == "":
		xstring = args.excludes

	excludesPath = os.path.join(dstFolder, excludesListName)
	if xstring != "":
		with open(excludesPath, "w") as f:
			f.write(xstring)
		console.print(f"Exclusion list written to {excludesPath}")
	else:
		if os.path.isfile(excludesPath):
			if args.useExcludesFile or extendList != None or askToUseExcludesFile():
				with open(excludesPath) as f:
					xstring = f.read()
				console.print(f"Exclusion list read from {excludesPath}")
				if extendList != None:
					didExtend = False
					xlist = xstring.split(",")
					for item in extendList.replace("+", "").split(","):
						if item != "":
							if item[0] == "-":
								if item[1:] in xlist:
									xlist.remove(item[1:])
									didExtend = True
							else:
								if not item in xlist:
									xlist.append(item)
									didExtend = True
					if didExtend:
						xlist.sort(key=int)
						xstring = ",".join(xlist)
						with open(excludesPath, "w") as f:
							f.write(xstring)
						console.print(f"Exclusion list written to {excludesPath}")

	# --------------------------------------------------
	startOperation("Cleaning destination folder...")

	folderList = [entryFolder, assetsFolder]
	fileList = [indexName, excludedName]
	foldersRemoved = 0
	filesRemoved = 0
	for name in os.listdir(dstFolder):
		path = os.path.join(dstFolder, name)
		if name == mediaFolder:	# remove all files except the static image folder
			for mediaName in os.listdir(path):
				if mediaName != staticImageFolder:
					mediaPath = os.path.join(path, mediaName)
					if os.path.isdir(mediaPath):
						shutil.rmtree(mediaPath)
						foldersRemoved += 1
					else:
						os.remove(mediaPath)
						filesRemoved += 1
		elif name in folderList:
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
	startOperation("Copying Assets folder")

	destAssetsPath = os.path.join(dstFolder, assetsFolder)
	if os.path.isdir(destAssetsPath):
		shutil.rmtree(destAssetsPath)
	if not os.path.isdir(destAssetsPath):
		srcAssetsPath = os.path.join(scriptPath, assetsFolder)
		try:
			shutil.copytree(srcAssetsPath, destAssetsPath)
		except OSError as e:
			console.print(f"\nError copying: {destAssetsPath}, {e}");

	# --------------------------------------------------
	startOperation("Build used file list")

	usedFiles = set()

	mainEntries = soup.find("div", class_="_a6-g").parent
	for entry in mainEntries:
		imgs = entry.find_all(["img", "video"])
		for img in imgs:
			src = img.get('src', img.get('sxx'))
			if not src.startswith("http"):
				usedFiles.add(src)

	# --------------------------------------------------

	def mergeAlbumSoup(albumSoup, name):
		startSubOperation(f"Adding entries from the album '{name}'", print=False)
		firstDiv = albumSoup.find("div", class_="_a6-g")
		if firstDiv != None:
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
					if tab != None:
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
			console.log(f"Added {addedCount} out of {listCount} entries from the album '{name}'")

	def mergeSoupFile(soupPath):
		nonlocal srcDataCount
		srcDataCount += os.path.getsize(soupPath)
		if fileExists(soupPath):
			with open(soupPath) as fp:
				soup2 = BeautifulSoup(fp, 'lxml')
				mergeAlbumSoup(soup2, os.path.basename(soupPath))

	if isFacebook:
		startOperation("Merge Photos")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, yourPhotos))

		startOperation("Merge Videos")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, yourVideos))

		startOperation("Merge Other Posts")
		mergeSoupFile(os.path.join(srcFolder, postsFolder, otherPostsName))

		albumsFolder = os.path.join(srcFolder, postsFolder, albumsFolderName)
		albumFiles = [f for f in os.listdir(albumsFolder) if f.endswith(".html")]

		startOperation(f"Merge {len(albumFiles)} albums")
		for albumFile in albumFiles:
			mergeSoupFile(os.path.join(albumsFolder, albumFile))

	# --------------------------------------------------
	startOperation("Remove unneeded elements")

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
	startOperation("Remove Facebook links")

	fblinks = soup.find_all("a", href=re.compile(".*facebook\.com"))
	for flink in fblinks:
		p = flink.parent
		flink.unwrap()
		p.smooth()

	# --------------------------------------------------
	startOperation("Remove GPS coordinates")

	def isAPlace(tag):
		if tag.name == "div":
			if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
				if tag.string.startswith("Place: "):
					return True
		return False

	places = soup.find_all(isAPlace)
	for place in places:
		place.string = re.sub(" \(-?\d+.?\d*, ?-?\d+.?\d*\)", "", place.string).replace("Place: ", "")
		place.unwrap()

	# --------------------------------------------------
	startOperation("Remove Addresses")

	addresses = soup.find_all("div", string=re.compile("^Address: "))
	for address in addresses:
		address.decompose()

	# --------------------------------------------------
	startOperation("Reformat entries")

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
					addClass(entry.contents[0], "_top4")
					addClass(entry.contents[2], "_top0")

		entry.extract()
		itemDate = entry.itemdate
		if firstDate == None or itemDate < firstDate:
			firstDate = itemDate
		if lastDate == None or itemDate > lastDate:
			lastDate = itemDate

	# --------------------------------------------------
	startOperation("Sort entries")

	entries.sort(key=lambda x: x.itemdate, reverse=True)
	entryOuter.extend(entries)

	# --------------------------------------------------
	startOperation("Remove unneeded headings")

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
	if not args.noBanner:
		a706 = soup.find("div", class_="_a706")
		if a706 != None:
			startOperation("Create banner")

			newDiv = soup.new_tag("div")
			newDiv['class'] = "banner"

			typeString = "Facebook" if isFacebook else "Instagram"
			startDate = firstDate.strftime("%b %d, %Y")
			endDate = lastDate.strftime("%b %d, %Y")
			format = args.bannerFormat

			if userName == "":
				format = format.replace("$N - ", "")

			bannerText = format.replace("$N", userName).replace("$M", typeString).replace("$S", startDate).replace("$E", endDate)
			newDiv.string = bannerText
			a706.insert_before(newDiv)

	# --------------------------------------------------
	startOperation("Clean up tags")

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
		if classes != None:
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
	startOperation("Add entry numbers")

	entries = soup.find_all("div", class_="_a6-g")
	for i, entry in enumerate(entries):
		entry['eix'] = str(i)

	# --------------------------------------------------
	startOperation("Remove Updated... strings")

	isUpdated = re.compile("^Updated \w{3} \d{2}, \d{4} \d{1,2}:\d{2}:\d{2} [ap]m")
	pin2s = soup.find_all("div", class_="_2pin")
	for pin in pin2s:
		for string in reversed(list(pin.strings)):
			if isUpdated.match(string):
				string.extract()

	# --------------------------------------------------
	if args.hashtags:
		startOperation("Remove hashtags")

		hashtag = re.compile("#[a-zA-Z0-9_]+")
		separators = re.compile("[\n\t \u2028.]{2,}")
		startSpace = re.compile("^[\n\t \u2028]+")

		pim2s = soup.find_all("div", class_="_2pim")
		for pim2 in pim2s:
			if pim2.string:
				s = pim2.string
				if hashtag.search(s):
					s = hashtag.sub("", s)
					s = separators.sub(" ", s)
					s = startSpace.sub("", s)
					pim2.string.replace_with(s)

	# --------------------------------------------------
	def removeEmptyStrings():
		startOperation("Remove sequential and starting/ending empty strings")

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
	startOperation("Remove duplicate and birthday tags")

	birthdayMatches = [re.compile("^ha+p{2,}y .*birth.*y.*", re.IGNORECASE),
			   re.compile("^joy.*x an+ivers.*re.*", re.IGNORECASE),
			   re.compile("^bon an+ivers.*re.*", re.IGNORECASE),
			   re.compile("^gefelicite+rd.*", re.IGNORECASE),
			   re.compile("^feliz cu.*lea.*os.*", re.IGNORECASE)]

	def isBirthdayString(string):
		for match in birthdayMatches:
			if match.match(string):
				return True
		return False

	entries = soup.find_all("div", class_="_a6-g")
	deletedEntries = set()
	for entry in entries:
		pin2 = entry.find_all("div", class_="_2pin")
		for item in pin2:
			divs = item.find_all("div")
			if len(divs)==2:
				str1 = " ".join(divs[0].stripped_strings)
				if len(str1) > 0:
					str2 = " ".join(divs[1].stripped_strings)
					if str1 == str2:
						divs[1].decompose()
			if not args.birthdays:
				for string in item.strings:
					if isBirthdayString(string):
						deletedEntries.add(entry)
						break
		atags = entry.find_all("a")
		if len(atags) == 2:
			if atags[0].string and len(atags[0].string) > 0 and atags[0].string == atags[1].string:
				a0ParentString = " ".join(atags[0].parent.stripped_strings)
				a1ParentString = " ".join(atags[1].parent.stripped_strings)
				if len(a0ParentString) < len(a1ParentString):
					atags[0].parent.decompose()
				else:
					atags[1].parent.decompose()

	for item in deletedEntries:
		item.decompose()

	console.print(f"Deleted {len(deletedEntries)} birthday entries")

	# --------------------------------------------------
	startOperation("Clean up titles")

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
	if isFacebook:
		startOperation("Clean up Traveling tags")

		wasTraveling = re.compile(".* was traveling .*")

		entries = soup.find_all("div", class_="_a6-g")
		for entry in entries:
			a6h = entry.find("div", class_="_a6-h")
			if a6h != None:
				if wasTraveling.match(a6h.string):
					a6p = entry.find("div", class_="_a6-p")
					if a6p != None:
						pin2s = a6p.find_all("div", class_="_2pin")
						if len(pin2s) == 2:
							pin2s[0].decompose()

	# --------------------------------------------------
	startOperation("Remove img/video <a> wrappers")

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
		if image != None:
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

	def excludeEntries():
		if xstring != "":
			startOperation("Remove excluded entries")
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
	startOperation("Renaming and organizing media files", print=False)

	srcCount = 0

	def srcAttr(forPoster=False):
		nonlocal srcCount
		if forPoster:
			return 'poster' if srcCount < 5 else 'xpost'
		else:
			srcCount += 1
			return 'src' if srcCount < 5 else 'sxx'
	
	with Progress(prog_description, BarColumn(), prog_percentage, console=console) as progress:
		entries = soup.find_all("div", class_="_a6-g")
		task = progress.add_task("Organizing Media...", total=len(entries))

		for entry in entries:
			date = entry.itemdate
			yearMonth = (date.year % 100) * 100 + date.month
			if date.year in yearCounts:
				yearCounts[date.year] += 1
			else:
				yearCounts[date.year] = 1
				entry.insert_before(yearDivWithYear(date.year))
			addClass(entry, "d" + str(date.month*100 + date.day))

			imgs = entry.find_all(["img", "video"])
			if len(imgs) > 0:
				for i, tagimg in enumerate(imgs):
					oldName = tagimg.get('src', tagimg.get('sxx'))
					if not oldName.startswith("http"):
						startSubOperation(f"Processing '{oldName}'", print=False)
						
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
						del tagimg['src']
						tagimg[srcAttr()] = newName

						destPath = os.path.join(dstFolder, newName)
						copyFile(os.path.join(srcMediaPath, oldName), destPath)
						width = 0
						height = 0
						if tagimg.name == 'img':
							width, height = dimensionsOfImage(destPath)
						elif tagimg.name == 'video':
							width, height = dimensionsOfVideo(destPath)
							width = int(width)
							height = int(height)
							tagimg['preload'] = "none"
							if extractFirstFrameToFile(destPath, os.path.join(dstFolder, posterName)):
								del tagimg['poster']
								tagimg[srcAttr(True)] = posterName
							else:
								console.print(f"\nUnable to get poster frame for{destPath}\n")

						if width > 0:
							tagimg['width'] = width
							tagimg['height'] = height
						copyCount += 1
						oldNameTotal += len(oldName)
						newNameTotal += len(newName)
			progress.update(task, advance=1)

	# --------------------------------------------------
	startOperation("Retrieve static graphics")

	staticIndex = 1
	staticRename = {}

	for img in soup.find_all("img"):
		src = img.get('src', img.get('sxx'))
		if src.startswith(staticPrefix):
			ext = os.path.splitext(src)[1]
			if ext in [".gif", ".png"]:
				if src in staticRename:
					newName = staticRename[src]
				else:
					newName = f"{staticIndex}{ext}"
					staticRename[src] = newName
					staticIndex += 1
				newSrc = os.path.join(mediaFolder, staticImageFolder, newName)
				destPath = os.path.join(dstFolder, newSrc)
				if not fileExists(destPath):
					startSubOperation(f"Downloading '{src}'", print=False)
					response = requests.get(src)
					if response.status_code == 200:
						createFolder(destPath)
						with open(destPath, 'wb') as f:
							f.write(response.content)
						console.print(f"Downloaded {src} to {destPath}")
					else:
						console.print(f"Failed to download {src}")
				# del img['src']
				img['src'] = ""
				img[srcAttr()] = newSrc
				# addClass(tagimg, "hide")
				width, height = dimensionsOfImage(destPath)
				if width > 0:
					img['width'] = width
					img['height'] = height
			else:
				console.print(f"Unknown static image type: {src}")
		elif src.startswith("http"):
			console.print(f"External file: {src}")

	# --------------------------------------------------
	if args.exlist:
		excludeEntries()

	# --------------------------------------------------
	startOperation("Count tags")

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
			if item.name != None and item.name not in allNames:
				allNames.add(item.name)
			if item.get('id'):
				allIDs.add(item['id'])

	console.print(f"There are {len(allNames)} tags")
	console.print(f"There are {len(allClasses)} classes")
	console.print(f"There are {len(allIDs)} ids")

	# --------------------------------------------------
	startOperation("Split entries into blocks")

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
	startOperation("Fix styles")

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
	addStyle("._a6_o", 'height', 'auto', styleDict)

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
	startOperation("Add style sheet")

	linkTag = soup.new_tag("link", href=os.path.join(assetsFolder, styleName))
	linkTag['rel'] = "stylesheet"
	soup.head.append(linkTag)

	# --------------------------------------------------
	excludeSoup = None
	if args.exlist:
		startOperation("Copy structure for exluded entries page")
		excludeSoup = copy.copy(soup)

	# --------------------------------------------------
	startOperation("Add computed values")

	years = sorted(yearCounts.keys())
	yearCounts = [yearCounts[year] for year in years]

	scripttag = soup.new_tag("script")
	varString = f"var numSrcFiles = {str(len(htmlBlocks)-1)};" \
				f"var numImages = {str(len(allNewNames))};" \
				f"var allYears = [{','.join(map(str, years))}];" \
				f"var yearCounts = [{','.join(map(str, yearCounts))}];" \
				f"var numEntries = {str(len(entries))};" \
				
	if args.showIndexes:
		varString += f"var showIndexes = true;"
	
	scripttag.append(varString)
	soup.html.append(scripttag)

	# --------------------------------------------------
	startOperation("Add scripts")

	def addMainScript(sp):
		scriptPath = os.path.join(assetsFolder, appName)

		linktag = sp.new_tag("link")
		linktag['rel'] = "preload"
		linktag['href'] = scriptPath
		linktag['as'] = "script"
		sp.head.append(linktag)

		scripttag = sp.new_tag("script")
		scripttag['src'] = scriptPath
		sp.html.append(scripttag)

	addMainScript(soup)

	# --------------------------------------------------
	if args.exlist and excludeSoup != None:
		startOperation("Create excluded entries page")
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
	startOperation("Write html files")
	totalBytes = 0

	with open(os.path.join(dstFolder, indexName), "w") as f:
		totalBytes += f.write(str(soup))

	if len(htmlBlocks) > 0:
		entriesPath = os.path.join(dstFolder, entryFolder)
		createFolder(entriesPath)

		for i in range(1, len(htmlBlocks)):
			with open(os.path.join(entriesPath, entryName.format(str(i))), "w") as f:
				totalBytes += f.write(str(htmlBlocks[i]))

	result = []
	result.append(f"Number of entries: {len(entries)}")
	result.append(f"Number of blocks: {len(htmlBlocks)}")
	result.append(f"Block counts: {blockCounts}")
	result.append(f"Media items: {len(fileRename)}")
	result.append(f"Total name usage went from {oldNameTotal} to {newNameTotal}")
	result.append(f"Read {srcDataCount} bytes of html, wrote {totalBytes} bytes - saved {((srcDataCount - totalBytes) / srcDataCount) * 100:.2f}%")

	if args.showResult:
		destUrl = "file://" + os.path.join(dstFolder, indexName)
		webbrowser.open(destUrl)
	
	return result

if __name__ == '__main__':
	console.print(Panel("[green]Begin ByeByeMeta..."))

	msgs = []

	def doRun():
		result = processData()
		if result == None:
			msgs.append("[orange1]Cancelled")
		else:
			msgs.append("[green]ByeByeMeta Finished.")
			if isinstance(result, list):
				msgs.append("[white]")
				msgs.extend(result)

	if ('debugpy' in sys.modules and sys.modules['debugpy'].__file__.find('/.vscode/extensions/') > -1):
		doRun()
	else:
		try:
			doRun()
		except KeyboardInterrupt:
			msgs.append("[orange1]Cancelled")
		except Exception as err:
			msgs.append(f"[red]ByeByeMeta encountered an error!")
			msgs.append("[orange1]")
			msgs.append(f"Process: {lastOperation}")
			if lastSubOperation != "":
				msgs.append(f"SubProcess: {lastSubOperation}")
			msgs.append("[yellow]")
			msgs.append(traceback.format_exc().rstrip("\n"))
			msgs.append("[white]")
			msgs.append("You can email the developer at [green]randy@mac.com[white]. Please include a copy of this error box in your message.")

	console.print(Panel("\n".join(msgs)))
