from bs4 import BeautifulSoup, NavigableString
import re
from dateutil.parser import parse
from enum import Enum

print("Open FB Data File")

with open("your_posts.html") as fp:
	soup = BeautifulSoup(fp, 'lxml')

soup.head.base['href'] ="FB-Data/"

print("Remove unneeded elements")

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

def is_a_place(tag):
	if (tag.name == "div"):
		kids = list(tag.children)
		if len(kids) == 1 and isinstance(kids[0], NavigableString):
			if tag.string.startswith("Place: "):
				return True
	return False

print("Remove GPS coordinates")

places = soup.find_all(is_a_place)
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

def convert_to_datetime(input_str, parserinfo=None):
	return parse(input_str, parserinfo=parserinfo)

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
				kids[0].string.replace_with("\n".join(list(subkids[0].strings)))
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
	a701 = entry.find_all("div", class_="_a701")
	a72d = entry.find_all("div", class_="_a72d")
	if len(a72d) == 1:
		entry.itemdate = convert_to_datetime(str(a72d[0].string))
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
for entry in entries:
	pin2 = entry.find_all("div", class_="_2pin")
	for item in pin2:
		div1 = item.find("div")
		if div1 != None:
			divs = div1.find_all("div")
			if len(divs)==2:
				if str(divs[0].string)==str(divs[1].string):
					divs[1].decompose()

allClasses = []
allNames = []
allIDs = []
for item in soup.descendants:
	try:
		itemClasses = item['class']
		for c in itemClasses:
			if c not in allClasses:
				allClasses.append('.' + c)
	except:
		pass

	try:
		if item.name and item.name not in allNames:
			allNames.append(item.name)
	except:
		pass

	try:
		if item['id'] not in allIDs:
			allIDs.append(item['id'])
	except:
		pass

print("There are", len(allNames), "tags")
print("There are", len(allClasses), "classes")
print("There are", len(allIDs), "ids")

print("Split into multiple blocks")

firstYearMonth = 2100
lastYearMonth = 1900
currentYearMonth = 0

for entry in entries:
	yearMonth = entry.itemdate.year*100 + entry.itemdate.month
	if yearMonth < firstYearMonth:
		firstYearMonth = yearMonth
	if yearMonth > lastYearMonth:
		lastYearMonth = yearMonth
	if yearMonth > currentYearMonth:
		entry['id'] = str(yearMonth)
		currentYearMonth = yearMonth

entries = soup.find_all("div", class_="_a6-g")
entryCount = len(entries)
itemsPerBlock = 100
itemStartIndex = 40
htmlBlocks = [""]
blockCounts = [40]

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
	global styleDict
	try:
		item = styleDict[selector]
		item.pop(property)
	except KeyError:
		pass

def addStyle(selector, property, value):
	global styleDict
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
	list = []
	items = styleDict[key]
	for itemKey in items.keys():
		list.append(itemKey + ":" + items[itemKey])
	listStr = ";".join(list)
	styleList.append(key+"{"+listStr)

styleList.append("")
newStyle = "}".join(styleList)

styletag.string.replace_with(newStyle)

print("Add scripts")

scripttag = soup.new_tag("script")
scripttag.append("var numSrcFiles = " + str(len(htmlBlocks)-1) + ";")
soup.body.insert_before(scripttag)

scripttag = soup.new_tag("script")
scripttag['src'] = "../Assets/app.js"
soup.body.insert_before(scripttag)

print("Write files")
count = 0

with open("index.html", "w") as f:
	count += f.write(str(soup))

for i in range(1, len(htmlBlocks)):
	with open("entries" + str(i) + ".html", "w") as f:
		count += f.write(str(htmlBlocks[i]))

print("Wrote", count, "bytes")