#!python

# pip install --upgrade pip
# pip install beautifulsoup4
# pip install dateutil
# pip install pyqt6
# pip install pyface
# pip install requests

from bs4 import BeautifulSoup, NavigableString
import re
from dateutil.parser import parse
from enum import Enum
import subprocess, sys, os, shutil
import requests

assetsFolder = "assets"
entryFolder = "entries"
mediaFolder = "media"
staticImageFolder = "static"
indexName = "index.html"
entryName = "entries{}.html"
appName = "app.js"
styleName = "style.css"

postsFolder = "posts"
mainPostsName = "your_posts__check_ins__photos_and_videos_1.html"
otherPostsName = "your_uncategorized_photos.html"

def getFolder(message):
	command = f"folderPath=$(osascript -e \'choose folder with prompt \"{message}\"'); if [ -z \"$folderPath\" ]; then exit 1; fi; echo \"$folderPath\""
	result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	
	results = result.stdout.decode("utf-8").split("\n")
	if len(results) > 1:
		path = results[1].removeprefix("alias ")
		path = "/"+"/".join(path.split(":")[1:-1])
	else:
		path = None
		
	return path

def processData():
	srcFolder = getFolder("Select the <your_facebook_activity folder>:")
	if srcFolder == None:
		return
	dstFolder = getFolder("Select the destination folder:")
	if dstFolder == None:
		return

	print(f"src={srcFolder}\ndst={dstFolder}")

	print("Open Main FB Data File")

	mainSrcFile = os.path.join(srcFolder, postsFolder, mainPostsName) 
	with open(mainSrcFile) as fp:
		soup = BeautifulSoup(fp, 'lxml')

	otherSrcFile = os.path.join(srcFolder, postsFolder, otherPostsName) 
	with open(otherSrcFile) as fp:
		soup2 = BeautifulSoup(fp, 'lxml')

	def pluralize(string, count, pad=False):
		return "{:d} {}{}".format(count, string, "s" if count!=1 else " " if pad else "")

	def fileExists(path):
		return os.path.isfile(path)

	def createFolder(path):
		try:
			if "." in path:
				path = os.path.dirname(path)
			os.makedirs(path, exist_ok=True)
		except OSError as e:
			print(f"Error creating folder '{path}': {e}")

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

	scriptPath = os.path.abspath(os.path.dirname(sys.argv[0]))
	
	print("Cleaning destination folder...")
	foldersRemoved = 0
	filesRemoved = 0
	for name in os.listdir(dstFolder):
		path = os.path.join(dstFolder, name)
		if name==entryFolder or name==assetsFolder:
			shutil.rmtree(path)
			foldersRemoved += 1
		elif name==indexName:
			os.remove(path)
			filesRemoved += 1
	if filesRemoved>0 or foldersRemoved>0:
		print(" removed {} and {}.".format(pluralize("folder", foldersRemoved), pluralize("file", filesRemoved)))
	else:
		print(" done.")

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

	print("Merge Other elements")

	mainEntries = soup.find("div", class_="_a6-g").parent

	otherList = list(soup2.find("div", class_="_a6-g").parent.children)
	for entry in otherList:
		entry.extract()
		tab = entry.find('table')
		if (tab != None):
			tab.decompose()
		newDiv = soup2.new_tag("div")
		newDiv.string = " "
		newDiv['class'] = ["_2ph_", "_a6-h", "_a6-i"]
		entry.insert(0, newDiv)
		mainEntries.append(entry)

	print("Remove unneeded elements")

	del soup.head.base['href']

	upstrs = soup.find_all("div", string="Mobile uploads")
	for updiv in upstrs:
		updiv.decompose()

	pdescs = soup.find_all("div", class_="_3-95")
	for pdsc in pdescs:
		pdsc.decompose()

	print("Remove Facebook links")

	fblinks = soup.find_all("a", href=re.compile(".*facebook\.com"))
	for flink in fblinks:
		p = flink.parent
		flink.unwrap()
		p.smooth()

	def isAPlace(tag):
		if (tag.name == "div"):
			kids = list(tag.children)
			if len(kids) == 1 and isinstance(kids[0], NavigableString):
				if tag.string.startswith("Place: "):
					return True
		return False

	print("Remove GPS coordinates")

	places = soup.find_all(isAPlace)
	for place in places:
		place.string = re.sub(" \(-?\d+.?\d*, ?-?\d+.?\d*\)", "", place.string).replace("Place: ", "")
		place.unwrap()

	print("Remove Addresses")

	addresses = soup.find_all("div", string=re.compile("^Address: "))
	for address in addresses:
		address.decompose()

	def addClass(tag, c):
		classes = tag['class']
		if c not in classes:
			classes.append(c)
			tag['class'] = classes

	def removeClass(tag, c):
		classes = tag['class']
		try:
			classes.remove(c)
			tag['class'] = classes
		except KeyError:
			return

	def convertToDatetime(dateStr, parserinfo=None):
		return parse(dateStr, parserinfo=parserinfo)

	print("Reformat entries")

	entries = soup.find_all("div", class_="_a6-g")
	entryOuter = entries[0].parent
	for entry in entries:
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
		entry.extract()

	print("Sort entries")

	entries.sort(key=lambda x: x.itemdate, reverse=True)
	entryOuter.extend(entries)

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

	print("Clean up tags")

	cleanTag(soup.body)

	print("Remove duplicate tags")

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
				for string in div1.strings:
					if re.match("^happy birthday.*", string, re.IGNORECASE):
						toDelete.append(entry)
						break
	for item in toDelete:
		item.decompose()
		entries.remove(item)

	print("Deleted", len(toDelete), "birthday entries")

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

	print("Split into multiple blocks")

	yearCounts = {}

	fileRename = {}
	allNewNames = set()
	oldNameTotal = 0
	newNameTotal = 0

	print("Renaming and organizing media files", end="", flush=True)

	createFolder(os.path.join(dstFolder, mediaFolder))
	srcMediaPath = "/".join(srcFolder.split("/")[:-1])
	copyCount = 0

	for entry in entries:
		date = entry.itemdate
		yearMonth = date.year*100 + date.month
		if date.year in yearCounts:
			yearCounts[date.year] += 1
		else:
			yearCounts[date.year] = 1

		imgs = entry.find_all(["img", "video"])
		if (len(imgs) > 0):
			for i, tagimg in enumerate(imgs):
				oldName = tagimg['src']
				if not oldName.startswith("http"):
					extension = oldName.split(".")[-1]
					if i>0:
						suffix = str(i)
					else:
						suffix = ""
					newDateStr = os.path.join(str(yearMonth), str(date.day*1000000 + date.hour*10000 + date.minute*100 + date.second) + suffix)
					newName = "{}.{}".format(os.path.join(mediaFolder, newDateStr), extension)
					index = 2
					while newName in allNewNames:
						newName = "{}-{}.{}".format(os.path.join(mediaFolder, newDateStr), index, extension)
						index += 1
					allNewNames.add(newName)
					fileRename[oldName] = newName
					tagimg['src'] = newName
					taga = entry.find("a")
					if taga != None:
						taga['href'] = newName
					if copyFile(os.path.join(srcMediaPath, oldName), os.path.join(dstFolder, newName)):
						print(f"Copied {oldName} to {newName}")
						copyCount += 1
						if copyCount % 10 == 1:
							print(".", end="", flush=True)
					oldNameTotal += len(oldName)
					newNameTotal += len(newName)

	print("")
	print("Copied", copyCount, "files")

	print("Retrieve static graphics")

	staticPrefix = "https://static."

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
			else:
				print("Unknown static image type:", src)
		elif src.startswith("http"):
			print("External file:", src)

	print("Split entries into blocks")

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

	def removeStyle(selector, property):
		nonlocal styleDict
		try:
			item = styleDict[selector]
			item.pop(property)
		except KeyError:
			pass

	def addStyle(selector, property, value):
		nonlocal styleDict
		try:
			item = styleDict[selector]
		except KeyError:
			item = {}
			styleDict[selector] = item
		item[property] = value

	removeStyle("._2pin", "padding-bottom")
	removeStyle("._a7nf", "padding-left")
	removeStyle("._a72d", "padding-bottom")
	removeStyle("._a7ng", "padding-right")
	removeStyle("._3-96", "margin-bottom")

	addStyle("._a6-g", "margin-top", "12px")
	addStyle("._a6-g", "border-radius", "16px")
	addStyle("._a7nf", "column-gap", "12px")
	addStyle("._bot4", "padding-bottom", "4px")
	addStyle("._top0", "padding-top", "0px")

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

	print("Add styles")

	linkTag = soup.new_tag("link", href=os.path.join(assetsFolder, styleName))
	linkTag['rel'] = "stylesheet"
	soup.head.append(linkTag)

	print("Add computed values")

	years = sorted(yearCounts.keys())
	yearCounts = [yearCounts[year] for year in years]

	years = ",".join(map(str, years))
	yearCounts = ",".join(map(str, yearCounts))

	scripttag = soup.new_tag("script")
	varString = f"var numSrcFiles = {str(len(htmlBlocks)-1)};" \
				f"var allYears = [{years}];" \
				f"var yearCounts = [{yearCounts}];" \
				f"var numEntries = {str(len(entries))};"
	
	scripttag.append(varString)
	soup.head.append(scripttag)

	print("Add scripts")

	scripttag = soup.new_tag("script")
	scripttag['src'] = os.path.join(assetsFolder, appName)
	soup.head.append(scripttag)

	print("Write files")
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