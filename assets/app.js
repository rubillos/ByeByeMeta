var version = "v1.2"

const hasTouch = 'ontouchstart' in window;

var yearsReady = false;
var entryCount = 0;
var navOffsets = [];
var yearOffsets = [];
var adjustedYearOffsets = [];
var searchMode = false;
var searchString = "";
var currentUser = -1;

const search = new URLSearchParams(window.location.search);
let showMemories = search.has('memories');
let currentDate = new Date();
if (search.has('day')) {
	const days = search.get('day').replaceAll('-', '/').split('/');
	if (days.length == 2) {
		currentDate = new Date(currentDate.getFullYear(), parseInt(days[0]) - 1, parseInt(days[1]));
	}
}

function makeMonthDay() {
	monthDayID = `d${(currentDate.getMonth() + 1) * 100 + currentDate.getDate()}`;
}

makeMonthDay();

var showIndexes = window.numSrcFiles === undefined;
if (window.showIndexes !== undefined) {
	showIndexes = showIndexes || window.showIndexes;
}
if (search.has('indexes')) {
	showIndexes = true;
}

function interpolate(value, inputValues, outputValues) {
	if (value <= inputValues[0]) return outputValues[0];
	if (value >= inputValues[inputValues.length - 1]) return outputValues[outputValues.length - 1];

	for (let i = 0; i < inputValues.length - 1; i++) {
		if (value >= inputValues[i] && value <= inputValues[i + 1]) {
			const t = (value - inputValues[i]) / (inputValues[i + 1] - inputValues[i]);
			return outputValues[i] + t * (outputValues[i + 1] - outputValues[i]);
		}
	}
}

function makeAdjustedYearOffsets() {
	adjustedYearOffsets = [];
	for (let i = 0; i < yearOffsets.length; i++) {
		adjustedYearOffsets.push(yearOffsets[i] - (yearOffsets[i] / yearOffsets[yearOffsets.length-1]) * window.innerHeight);
	}
}

function getNavForOffset(offset) {
	return interpolate(offset, adjustedYearOffsets, navOffsets);
}

function getOffsetForNav(nav) {
	return interpolate(nav, navOffsets, adjustedYearOffsets);
}

function isYearMark(element) {
	return element.classList.contains('year-mark');
}

function visibleElements(classes = '.year-mark, ._a6-g') {
	const elements = document.querySelectorAll(classes);
	const visList = [];
	for (let i = 0; i < elements.length; i++) {
		if (elements[i].style.display != "none") {
			visList.push(elements[i]);
		}
	}
	return visList;
}

function cleanHeadings() {
	const visList = visibleElements();
	for (let i = visList.length - 2; i >= 0; i--) {
		if (isYearMark(visList[i]) && isYearMark(visList[i + 1])) {
			visList[i].style.display = "none";
			visList.splice(i, 1);
		}
	}
	return visList;
}

function hideShowMemories(containerDiv) {
	if (showMemories) {
		for (const element of containerDiv.children) {
			const classes = element.classList;
			if (!classes.contains('year-mark') && !classes.contains(monthDayID)) {
				element.style.display = "none";
			}
		}
		cleanHeadings();
	}
}

function reFlow() {
	updateMemories();
	setMemoryTitle();
	updateIndicatorPosition();
}

var searchTimer = null;

function cancelSearchTimer() {
	if (searchTimer) {
		clearTimeout(searchTimer);
		searchTimer = null;
	}
}

function doUpdateSearch() {
	searchString = document.getElementById('find').value.toLowerCase();
	reFlow();
}

function updateSearch(useTimer = false) {
	if (useTimer) {
		cancelSearchTimer();
		searchTimer = setTimeout(doUpdateSearch, 300);
	}
	else {
		doUpdateSearch();
	}
}

function changeBy(dayOffset) {
	currentDate = new Date(currentDate.getTime() + dayOffset * 24 * 60 * 60 * 1000);
	makeMonthDay();
	reFlow();
}

function setMemoryTitle(useCount = true) {
	const title = document.querySelector('#title');

	if (title != null) {
		const banner = title.parentElement;

		banner.querySelectorAll('.arrow').forEach(element => {
			element.style.display = (showMemories) ? "block" : "none";
		});

		if (showMemories) {
			const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
			const month = monthNames[currentDate.getMonth()];
			const day = currentDate.getDate();
			const memoryCount = visibleElements(classes = '._a6-g').length;
			if (useCount) {
				title.textContent = `${memoryCount} ${(memoryCount==1) ? "Memory":"Memories"} for ${month} ${day}`;
			}
			else {
				title.textContent = `Memories - ${month} ${day}`;
			}
		}
		else if (banner.getAttribute('txt') != null) {
			let titleStr = banner.getAttribute('txt');
			if (window.userNames !== undefined && window.userNames.length > 1) {
				if (currentUser == -1) {
					const userCount = window.userNames.length;
					const joinStr = (userCount == 2) ? " & " : ", ";
					if (userCount == 1) {
						titleStr = titleStr.replace("{users}", window.userNames[0]);
					}
					else {
						const firstNames = [];
						for (user in window.userNames) {
							firstNames.push(window.userNames[user].split(' ')[0]);
						}
						titleStr = titleStr.replace("{users}", firstNames.join(', '));
					}
				}
				else {
					titleStr = titleStr.replace("{users}", window.userNames[currentUser]);
				}		
			}
			title.textContent = titleStr;
		}
	}
}

function toggleSearch(e) {
	if (!e.defaultPrevented) {
		e.preventDefault();
		cancelSearchTimer();
		searchMode = !searchMode;
		const find = document.getElementById('find');
		const title = document.getElementById('title');
		if (searchMode) {
			showMemories = false;
			reFlow();
			find.style.display = "block";
			title.style.display = "none";
			find.focus();
		}
		else {
			find.style.display = "none";
			title.style.display = "block";
			find.blur();
			find.value = "";
			searchString = "";
			reFlow();
		}
	}
}

function toggleMemories(e) {
	if (!e.defaultPrevented) {
		e.preventDefault();
		cancelSearchTimer();
		showMemories = !showMemories;
		searchMode = false;
		document.getElementById('title').style.display = "block";
		const find = document.getElementById('find')
		find.blur();
		find.style.display = "none";
		searchString = "";
		find.value = "";
		const search = document.getElementById('search');
		search.style.display = (showMemories) ? "none" : "block";
		reFlow();
	}
}

function changeUser(e) {
	const userPopup = document.getElementById('popup');
	const user = e.target.style.getPropertyValue('--user');

	currentUser = user == null ? -1 : parseInt(user);
	userPopup.style.setProperty('--cur-user', currentUser);

	reFlow();
}

function hidePopup() {
	const userPopup = document.getElementById('popup');

	if (userPopup && userPopup.classList.contains('show')) {
		userPopup.classList.remove('show');
		window.removeEventListener('click', clickOutsideUser, true);
	}
}

function clickOutsideUser(e) {
	if (!e.target.closest("#popup")) {
		e.preventDefault();
		e.stopPropagation();
		hidePopup();
	}
}

function setupMemories() {
	const banner = document.querySelector('.banner');
	if (banner) {
		if (banner.getAttribute('txt') == null) {
			let titleStr = banner.textContent;

			if (window.userNames !== undefined && window.userNames.length > 1) {
				const allUsers = window.userNames.join(', ');
				titleStr = titleStr.replace(allUsers, "{users}")
			}
			banner.setAttribute('txt', titleStr);
			banner.textContent = '';

			let left = document.createElement('div');
			left.textContent = "⬅️";
			left.classList.add('text-button', 'arrow');
			left.id = 'left';
			banner.appendChild(left);
			left.addEventListener('click', (e) => {
				e.preventDefault();
				changeBy(-1);
			});

			let search = document.createElement('div');
			search.textContent = "🔍";
			search.classList.add('text-button');
			search.id ='search';
			banner.appendChild(search);
			search.addEventListener('click', toggleSearch);

			let find = document.createElement('input');
			find.id = 'find';
			find.style.display = "none";
			banner.appendChild(find);
			find.addEventListener('input', (e) => {
				if (!hasTouch) {
					e.preventDefault();
					e.stopPropagation();
					updateSearch(true);
				}
			});
			find.addEventListener('keydown', (e) => {
				if (e.key === 'Enter') {
					find.blur();
					if (find.value == "") {
						toggleSearch(e);
					}
					else if (hasTouch) {
						find.classList.add('outline');
						setTimeout(() => {
							updateSearch();
							find.classList.remove('outline');
						}, 10);
					}
					e.preventDefault();
					e.stopPropagation();
				}
				else if (e.key === 'Escape') {
					toggleSearch(e);
				}
			});

			let title = document.createElement('div');
			title.id = 'title';
			banner.appendChild(title);
			title.addEventListener('click', toggleMemories);

			if (window.userNames !== undefined && window.userNames.length > 1) {
				let chooseUser = document.createElement('div');
				chooseUser.textContent = "👤";
				chooseUser.classList.add('text-button');
				chooseUser.id = 'user';
				banner.appendChild(chooseUser);

				function addUser(dropdown, name, index) {
					let user = document.createElement('div');
					user.textContent = name;
					user.style.setProperty('--user', index);
					dropdown.appendChild(user);
					user.addEventListener('click', (e) => {
						e.preventDefault();
						chooseUser.classList.remove('show');
						changeUser(e);
					});
				}

				let userPopup = document.createElement('div');
				userPopup.id = 'popup';
				userPopup.classList.add('dropdown');
				userPopup.style.setProperty('--cur-user', currentUser);

				addUser(userPopup, "All", -1);
				window.userNames.forEach((name, index) => {
					addUser(userPopup, name, index);
				});
				chooseUser.appendChild(userPopup);

				chooseUser.addEventListener('click', (e) => {
					e.preventDefault();
					if (userPopup.classList.contains('show')) {
						hidePopup();
					}
					else {
						userPopup.classList.add('show');
						window.addEventListener('click', clickOutsideUser, true);
					}
				});
			}

			let memories = document.createElement('div');
			memories.textContent = "🗓️";
			memories.classList.add('text-button');
			memories.id = 'memories';
			banner.appendChild(memories);
			memories.addEventListener('click', toggleMemories);

			let right = document.createElement('div');
			right.textContent = "➡️";
			right.classList.add('text-button', 'arrow');
			right.id = 'right';
			banner.appendChild(right);
			right.addEventListener('click', (e) => {
				e.preventDefault();
				changeBy(1);
			});

			setMemoryTitle(false);
		}
	}
}

function cleanupMemories() {
	const visList = cleanHeadings();
	if (visList.length >= 1 && isYearMark(visList[visList.length - 1])) {
		visList[visList.length - 1].style.display = "none";
	}
	if (visList.length == 1 && isYearMark(visList[0])) {
		visList[0].style.display = "none";
	}
	setMemoryTitle();
}

function updateMemories() {
	var elements = document.querySelectorAll('.year-mark');
	for (let i = 0; i < elements.length; i++) {
		elements[i].style.display = "block";
	}

	re = new RegExp(searchString, "i");
	elements = document.querySelectorAll('._a6-g');
	for (let i = 0; i < elements.length; i++) {
		const element = elements[i];
		const classes = element.classList;
		let uid = element.getAttribute('uid');
		uid = (uid == null) ? 0 : parseInt(uid);

		if (currentUser != -1 && currentUser != uid) {
			element.style.display = "none";
		}
		else if (showMemories && !classes.contains(monthDayID)) {
			element.style.display = "none";
		}
		else if (searchMode && searchString != "" && !re.test(element.innerText)) {
			element.style.display = "none";
		}
		else {
			element.style.display = "block";
		}
	}
	cleanupMemories();
	computeNavInfo();
}

function createRoundedRectPath(x, y, width, height, llRadius, lrRadius, vOffset) {
	const w = parseInt(width);
	const h = parseInt(height);
	const ll = parseInt(Math.min(llRadius, height));
	const lr = parseInt(Math.min(lrRadius, height));
	return (
		`M${x},${(y-vOffset)}h${w}v${(h+vOffset-lr)}a${lr},${lr} 0 0 1 ${-lr},${lr}h${(lr + ll - w)}a${-ll},${-ll} 0 0 1 ${-ll},${-ll}v${(ll-vOffset-h)}z`
	);
}

function updateYearBackground(durationMS) {
	if (yearsReady) {
		const background = document.getElementById('year-background');
		const numEntries = parseInt(window.numEntries);
		if (background.offsetHeight == 0) {
			background.style.height = "100%";
		}
		const height = entryCount/numEntries*background.offsetHeight;
		const path = createRoundedRectPath(0, 0, background.offsetWidth, height, 30, 40, 10);
		background.style.transition = `clip-path ${(durationMS / 1000.0)}s linear`;
		background.style.clipPath = `path('${path}')`;
	}
}

function finishYearBackground() {
	const yearBack = document.getElementById('year-background');
	const yearBackTop = document.getElementById('year-back-top');
	const yearBackBottom = document.getElementById('year-back-bottom');

	yearBack.style.transition = 'background-image 0.3s';
	yearBackTop.style.transition = 'background-image 0.3s';
	yearBackBottom.style.transition = 'display 0.3s';

	yearBack.style.setProperty('--bar-display', 'none');
	yearBack.style.removeProperty('clip-path');
	yearBack.classList.remove('back-blue');
	yearBack.classList.add('back-gray');
	yearBackTop.classList.remove('back-blue');
	yearBackTop.classList.add('back-gray');
	yearBackBottom.style.display = "block";
}

function computeNavInfo() {
	const navColumn = document.getElementById('year-column');
	const columnHeight = navColumn.offsetHeight;
	const navDivs = navColumn.children;
	const yearMarks = document.querySelectorAll('.year-mark');
	let visYearCount = 0;
	yearMarks.forEach((yearMark, i) => {
		if (yearMark.style.display == 'none') {
			navDivs[i].style.display = 'none';
		}
		else {
			visYearCount += 1;
			navDivs[i].style.removeProperty('display');
		}
	});
	for (let i=0, index=0; i<navDivs.length; i++) {
		if (navDivs[i].style.display != "none") {
			navDivs[i].style.setProperty('--pos', `${(index + 0.5) / visYearCount}`);
			index += 1;
		}
	}

	navOffsets = [];
	yearOffsets = [];
	yearMarks.forEach((mark, index) => {
		if (mark.style.display != "none") {
			yearOffsets.push(mark.offsetTop);
			navOffsets.push(navDivs[index].offsetTop / columnHeight);
		}
	});
	yearOffsets.push(document.body.scrollHeight);
	navOffsets.push(1);
	makeAdjustedYearOffsets();
}

async function loadAndInsertDivsSequentially(filePaths, domDone) {
	let activeTask = null;
	let index = 1;
	let checkDom = true;
	let startTime = Date.now();

	for (const filePath of filePaths) {
		const parseTask = async (htmlText, priorTask, index) => {
			const startTrim = "<div>".length;
			const endTrim = "</div>".length;
			const entriesDiv = document.createElement('div');
			entriesDiv.innerHTML = htmlText.slice(startTrim, -endTrim);

			if (checkDom) {
				await domDone;
				checkDom = false;
			}

			const targetDiv = document.querySelector('._a706');
			if (index == 1) {
				setupMemories();
				hideShowMemories(targetDiv);
			}

			if (priorTask !== null) {
				await priorTask;
			}
			
			hideShowMemories(entriesDiv);
			targetDiv.appendChild(entriesDiv);
			entryCount += entriesDiv.children.length;
			const curTime = Date.now();
			updateYearBackground((index<filePaths.length) ? (curTime - startTime) * 0.8 : 0.2);
			startTime = curTime;
		};

		const response = await fetch(filePath);
		const text = await response.text();

		activeTask = parseTask(text, activeTask, index);
		index += 1;
	}

	await activeTask;

	finishYearBackground();
	cleanupMemories();
	computeNavInfo();

	indicator.style.removeProperty("display");
	updateIndicatorPosition();
	setupEvents();
}

function setSrc(img, intersect, src, sxx, noDelete=false) {
	if (intersect) {
		if (img.getAttribute(sxx)) {
			img.setAttribute(src, img.getAttribute(sxx));
			img.removeAttribute(sxx);
		}
	} else {
		if (img.getAttribute(src)) {
			img.setAttribute(sxx, img.getAttribute(src));
			if (!noDelete) {
				img.removeAttribute(src);
			}
		}
	}
}
  
function getImgSrc(img) {
	return img.getAttribute('src') || img.getAttribute('sxx');
}

function setupEvents() {
	if (showIndexes) {
		addAllIndexes();
	}
	else {
		document.querySelectorAll('._a6-g').forEach(element => {
			element.onmouseenter = showEIndex;
		});
	}

	document.querySelectorAll('img._a6_o').forEach(img => {
		const parentDiv = img.closest('div._a6-g');
		if (parentDiv && parentDiv.style.display !== "none") {
			img.onclick = showImage;
		}
	});

	const wrapper = document.querySelector('_a706');
	if (wrapper) {
		wrapper.onclick = function(e) {
			if (e.target.tagName === 'IMG') {
				showImage(e);
			}
		}
	}

	window.addEventListener('resize', makeAdjustedYearOffsets);

	document.addEventListener('keypress', function(event) {
		hidePopup();
	});
	
	document.addEventListener('keydown', function(event) {
		if (!viewerVisible()) {
			if (event.key === 'Enter' || event.key === 'ArrowRight') {
				if (event.target.tagName !== 'INPUT') {
					const images = document.querySelectorAll('img._a6_o');
					const middleY = window.innerHeight / 2;
					let closestImage = null;
					let closestDistance = Infinity;

					images.forEach(img => {
						const rect = img.getBoundingClientRect();
						if (rect.height > 0) {
							const imgMiddleY = rect.top + rect.height / 2;
							const distance = Math.abs(imgMiddleY - middleY);

							if (distance < closestDistance) {
								closestDistance = distance;
								closestImage = img;
							}
						}
					});

					if (closestImage) {
						showImage({ currentTarget: closestImage });
					}
				}
			}
		}
	});

	const io = new IntersectionObserver(entries => {
		entries.forEach(entry => {
			const img = entry.target;
			if (img != mainImg) {
				if (img.nodeName == "VIDEO") {
					setSrc(img, entry.isIntersecting, 'poster', 'xpost', true);
				}
				setSrc(img, entry.isIntersecting, 'src', 'sxx');
			}
		});
	}, { rootMargin: `${window.innerHeight}px 0px ${window.innerHeight}px 0px` });
	  
	document.querySelectorAll('img, video').forEach((img) => {
	  io.observe(img);
	});
}

function addIndexTo(element) {
	const tooltip = document.createElement('div');
	tooltip.className = 'tooltip';
	tooltip.textContent = element.getAttribute('eix');
	element.appendChild(tooltip);
	return tooltip;
}

function addAllIndexes() {
	if (showIndexes) {
		document.querySelectorAll('._a6-g').forEach(element => {
			addIndexTo(element);
		});
	}
}

function showEIndex(event) {
	if (event.altKey) {
		const element = event.currentTarget;
		const tooltip = addIndexTo(element);

		element.onmouseleave = () => {
			element.removeChild(tooltip);
			element.onmouseleave = null;
		};
	}
}

function currentImgUrls() {
	const urls = [];
	document.querySelectorAll('img._a6_o').forEach(img => {
		let parentDiv = img.closest('div._a6-g');
		if (parentDiv && parentDiv.style.display !== "none") {
			const src = getImgSrc(img);
			if (!urls.includes(src)) {
				urls.push(src);
			}
		}
	});
	return urls;
}

function setViewerSrc(src) {
	if (src != null) {
		mainImg.src = src;
		viewerSrc = src;
	}
}

function showImage(e) {
	if (e instanceof Event) {
		e.preventDefault();
	}
	const element = e.currentTarget;
	const src = getImgSrc(element);

	imgUrls = currentImgUrls();

	if (imageViewer) {
		setViewerSrc(src);
		imageViewer.style.display = "block";
	}
}

function domReady() {
	return new Promise(resolve => {
		if (document.readyState === "complete") {
			resolve();
		} else {
			document.addEventListener("DOMContentLoaded", () => resolve());
		}
	});
}

function supportsTouchEvents() {
	return 'ontouchstart' in window || navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;
}
  
var mouseIsDown = false;

var imageViewer = null;
var touchDiv = null;
var mainImg = null;
var cacheImg = null;
var activeAnimation = null;
var imgUrls = null;
var viewerSrc = null;

function viewerVisible() {
	return imageViewer && imageViewer.style.display == "block";
}

function setupNavigation() {
	fetch(`assets/extra.html?${version}`)
		.then(response => response.text())
		.then(data => {
			const parser = new DOMParser();
			const doc = parser.parseFromString(data, 'text/html');
			const content = doc.getElementById('content');
			if (content) {
				const fragment = document.createDocumentFragment();
				while (content.lastChild) {
					fragment.insertBefore(content.lastChild, fragment.firstChild);
				}
				document.body.insertBefore(fragment, document.body.firstChild);
				setupYears();
				setupViewer();
				window.addEventListener('scroll', () => {
					if (viewerVisible()) {
						hidePopup();
						updateIndicatorPosition();
					}
				});

				const nav = document.getElementById('navigator');

				if (supportsTouchEvents()) {
					nav.ontouchstart = touchStart;
					nav.ontouchmove = touchMove;
					nav.ontouchend = touchEnd;
				}
				else {
					nav.onmousedown = navMouseDown;
					document.onmouseup = endDrag;		
				}
			}
		})
	.catch(error => console.error('Error loading extra.html:', error));

	function setupViewer() {
		imageViewer = document.getElementById('image-viewer');
		touchDiv = document.getElementById('touch-div');
		mainImg = document.getElementById('main-img');
		cacheImg = document.createElement("img");

		cacheImg.style = "position:absolute;z-index:-1000;max-width:100px;max-height:100px;opacity:0;";
		document.body.appendChild(cacheImg);

		function preloadNext() {
			const src = nextSrc();
			if (src) {
				cacheImg.src = src;
			}
		}

		mainImg.addEventListener('load', preloadNext);

		function closeImageViewer(lastUrl) {
			cacheImg.src = "";
			setViewerSrc("");
			imageViewer.style.display = "none";
			if (lastUrl) {
				const img = document.querySelector(`img[src="${lastUrl}"], img[sxx="${lastUrl}"]`);
				if (img) {
					setTimeout(() => {
						const rect = img.getBoundingClientRect();
						if (rect.top > 0) {
							window.scrollTo(0, window.scrollY + rect.top + rect.height / 2 - window.innerHeight / 2);
						}
					}, 0);
				}
			}
		};

		document.querySelector('#close-x').addEventListener('click', function(e) {
			e.preventDefault();
			closeImageViewer(viewerSrc);
		});

		function nextSrc() {
			if (imgUrls) {
				const currentIndex = imgUrls.indexOf(viewerSrc);
				if (currentIndex < imgUrls.length - 1) {
					return imgUrls[currentIndex + 1];
				}
			}
			return null;
		}

		function previousSrc() {
			if (imgUrls) {
				const currentIndex = imgUrls.indexOf(viewerSrc);
				if (currentIndex > 0) {
					return imgUrls[currentIndex - 1];
				}
			}
			return null;
		}

		function nextImage() {
			setViewerSrc(nextSrc());
		}

		function previousImage() {
			setViewerSrc(previousSrc());
		}

		document.addEventListener('keydown', function(e) {
			if (viewerVisible()) {
				const closeKeys = ['Escape', 'Enter'];
				const nextKeys = ['ArrowDown', 'ArrowRight', ' '];
				const prevKeys = ['ArrowUp', 'ArrowLeft'];

				if (closeKeys.includes(e.key)) {
					closeImageViewer(viewerSrc);
				}
				else if (imgUrls) {
					if (prevKeys.includes(e.key)) {
						previousImage();
						performSlideback(true);
					}
					else if (nextKeys.includes(e.key)) {
						nextImage();
						performSlideback(true);
					}
				}
			}
		});

		if (hasTouch) {		
			touchDiv.addEventListener('touchstart', handleTouchStart, { passive: false });
			touchDiv.addEventListener('touchmove', handleTouchMove, { passive: false });
			touchDiv.addEventListener('touchend', handleTouchEnd, { passive: false });
		}
		else {
			touchDiv.addEventListener('click', function(e) {
				e.preventDefault();
				nextImage();
				performSlideback(true);
			});
		}

		const slideDuration = 200;
		const springFactor = 0.5;

		var imgXForm = { x:0, y:0, scale:1.0 };

		var startSize = null;
		var startOne = null;
		var startTwo = null;
		var centerTwo = null;
		var startDist = null;
		var startTime = null;
		var startXForm = null;

		var lastOne;

		function updateImage() {
			mainImg.style.transform = `translate(${imgXForm.x}px,${imgXForm.y}px) scale(${imgXForm.scale})`;
		}

		function imageSize() {
			const imgAspect = mainImg.naturalWidth / mainImg.naturalHeight;
			const windowAspect = window.innerWidth / window.innerHeight;
			var imgWidth = mainImg.clientWidth;
			var imgHeight = mainImg.clientHeight;

			if (imgAspect > windowAspect) {
				imgHeight = imgWidth / imgAspect;
			}
			else {
				imgWidth = imgHeight * imgAspect;
			}
			return { width:imgWidth, height:imgHeight };
		}

		function clamp(num, lower, upper) {
			return Math.min(Math.max(num, lower), upper);
		}
		
		function relativeCenter(pt) {
			const size = imageSize();
			const midX = window.innerWidth / 2.0;
			const midY = window.innerHeight / 2.0;
			const left = midX - (size.width / 2.0) * imgXForm.scale + imgXForm.x;
			const top = midY - (size.height / 2.0) * imgXForm.scale + imgXForm.y;
			const width = size.width * imgXForm.scale;
			const height = size.height * imgXForm.scale;
			const x = (pt.x - left) / width;
			const y = (pt.y - top) / height;
			return { x:0.5-clamp(x, 0, 1.0), y:0.5-clamp(y, 0, 1.0) };
		}

		function touchCenter(e) {
			const x = (e.targetTouches[0].clientX + e.targetTouches[1].clientX) / 2;
			const y = (e.targetTouches[0].clientY + e.targetTouches[1].clientY) / 2;
			return { x:x, y:y };
		}

		function touchDist(e) {
			if (e.targetTouches.length == 2) {
				const xDiff = e.targetTouches[0].clientX - e.targetTouches[1].clientX;
				const yDiff = e.targetTouches[0].clientY - e.targetTouches[1].clientY;
				return Math.sqrt(xDiff * xDiff + yDiff * yDiff);
			}
			else {
				return 1.0;
			}
		}

		function touchScale(e, startDist) {
			if (e.scale) {
				return e.scale;
			}
			else {
				return touchDist(e) / startDist;
			}
		}

		function touchPoint(e) {
			return { x:e.targetTouches[0].clientX, y:e.targetTouches[0].clientY };
		}

		function handleTouchStart(e) {
			e.preventDefault();
			cancelAnimation();

			if (e.targetTouches.length == 1) {
				startOne = touchPoint(e);
				startXForm = { ...imgXForm };
				lastOne = { ...startOne };
				startTime = Date.now();
			}
			else if (e.targetTouches.length == 2) {
				startTwo = touchCenter(e);
				startDist = touchDist(e);
				centerTwo = relativeCenter(startTwo);
				startSize = imageSize();
				startXForm = { ...imgXForm };
				startTime = Date.now();
			}
		}

		function handleTouchMove(e) {
			e.preventDefault();

			if (startTwo==null && e.targetTouches.length == 1) {
				const pt = touchPoint(e);
				imgXForm.x = startXForm.x + pt.x - startOne.x;
				imgXForm.y = startXForm.y + pt.y - startOne.y;
				lastOne = pt;
				imgXForm = clampXForm(imgXForm, false, true);
				updateImage();
			}
			else if (e.targetTouches.length == 2) {
				const pt = touchCenter(e);
				imgXForm.scale = startXForm.scale * touchScale(e, startDist);
				const scaleChange = imgXForm.scale - startXForm.scale;
				const xChange = scaleChange * startSize.width;
				const yChange = scaleChange * startSize.height;
				imgXForm.x = startXForm.x + (pt.x - startTwo.x) + xChange * centerTwo.x;
				imgXForm.y = startXForm.y + (pt.y - startTwo.y) + yChange * centerTwo.y;
				imgXForm = clampXForm(imgXForm, false, true);
				updateImage();
			}
		}

		function handleTouchEnd(e) {
			if (!startTime) {
				return;
			}

			e.preventDefault();
			const duration = Date.now() - startTime;

			if (e.targetTouches.length == 0) {
				var resetScale = false;
				var slideBack = true;

				if (startOne && startTwo==null && duration < 200 && (!e.scale || e.scale == 1) && (!e.rotation || e.rotation == 0)) {
					const xDiff = startOne.x - lastOne.x;
					const yDiff = startOne.y - lastOne.y;
					const dist = Math.sqrt(xDiff * xDiff + yDiff * yDiff);

					if (dist > 10) {
						let angle = Math.atan2(yDiff, xDiff) * 180 / Math.PI;
						let direction = Math.round((angle + 360) / 45) % 8;
						switch (direction) {
							case 2: // up
							case 4: // right
								previousImage();
								resetScale = true;
								break;
							case 6: // down
								window.close();
								slideBack = false;
								break;
							case 0: // left
								nextImage();
								resetScale = true;
								break;
						}
					}
					else {
						nextImage();
						resetScale = true;
					}
				}

				if (slideBack) {
					performSlideback(resetScale);
				}

				startTime = null;
				startOne = null;
				startTwo = null;
			}
		}

		function clampXForm(xform, resetScale, springy = false) {
			var newXForm = { ...xform };

			if (!springy) {
				newXForm.scale = (resetScale) ? 1.0 : clamp(xform.scale, 1.0, 5.0);
			}

			if (newXForm.scale > 1.0) {
				const size = imageSize();
				const maxX = Math.max(0, (size.width * newXForm.scale - window.innerWidth) / 2.0);
				const maxY = Math.max(0, (size.height * newXForm.scale - window.innerHeight) / 2.0);

				if (springy) {
					if (xform.x < -maxX) {
						newXForm.x = -maxX + (xform.x + maxX) * springFactor;
					}
					else if (xform.x > maxX) {
						newXForm.x = maxX + (xform.x - maxX) * springFactor;
					}
					if (xform.y < -maxY) {
						newXForm.y = -maxY + (xform.y + maxY) * springFactor;
					}
					else if (xform.y > maxY) {
						newXForm.y = maxY + (xform.y - maxY) * springFactor;
					}
				}
				else {
					newXForm.x = clamp(xform.x, -maxX, maxX);
					newXForm.y = clamp(xform.y, -maxY, maxY);
				}
			}
			else {
				if (springy) {
					newXForm.x = xform.x * springFactor;
					newXForm.y = xform.y * springFactor;
				}
				else {
					newXForm.x = 0;
					newXForm.y = 0;
				}
			}

			return newXForm;
		}

		function performSlideback(resetScale) {
			cancelAnimation();
			const newXForm = clampXForm(imgXForm, resetScale);
			if (newXForm.x != imgXForm.x || newXForm.y != imgXForm.y || newXForm.scale != imgXForm.scale) {
				animateImgTo(newXForm);
			}
		}

		function cancelAnimation() {
			if (activeAnimation != null) {
				cancelAnimationFrame(activeAnimation);
				activeAnimation = null;
			}
		}

		function animateImgTo(newXForm) {
			function easeInOut(t) {
				const t2 = t * t;
				const t3 = t2 * t;
				return t3 / (t2 + (1 - t) * (1 - t));
			}

			function interpolate(start, end, t) {
				return start + (end - start) * easeInOut(t);
			}

			cancelAnimation();

			const startTime = Date.now();
			const oldXForm = { ...imgXForm };

			function animate() {
				const fraction = (Date.now() - startTime) / slideDuration;

				activeAnimation = null;

				if (fraction < 1.0) {
					imgXForm.x = interpolate(oldXForm.x, newXForm.x, fraction);
					imgXForm.y = interpolate(oldXForm.y, newXForm.y, fraction);
					imgXForm.scale = interpolate(oldXForm.scale, newXForm.scale, fraction);
					updateImage();
					activeAnimation = requestAnimationFrame(animate);
				}
				else {
					imgXForm = newXForm;
					updateImage();
				}
			}

			animate();
		}

		if (!hasTouch) {
			function relativeScaleAdjust(oldScale, newScale, pt) {
				if (newScale != oldScale) {
					const relCenter = relativeCenter(pt);
					const scaleChange = newScale - oldScale;
					const size = imageSize();
					const xChange = scaleChange * size.width;
					const yChange = scaleChange * size.height;
					imgXForm.x += xChange * relCenter.x;
					imgXForm.y += yChange * relCenter.y;
				}
			}
			
			document.addEventListener('wheel', event => {
				if (viewerVisible()) {
					event.preventDefault();
					cancelAnimation();

					const oldScale = imgXForm.scale;
				
					if (event.ctrlKey || event.altKey) {
						imgXForm.scale *= Math.exp(-event.deltaY/100);
					}
					else{
						imgXForm.x -= event.deltaX;
						imgXForm.y -= event.deltaY;
					}
					
					imgXForm = clampXForm(imgXForm, false);
					relativeScaleAdjust(oldScale, imgXForm.scale, { x:event.clientX, y:event.clientY });
					updateImage();
				}
			}, {
				passive: false
			});

			var lastGestureX = 0;
			var lastGestureY = 0;
			var lastGestureScale = 1.0;

			function onGesture(event) {
				if (viewerVisible()) {
					event.preventDefault();
					
					if (event.type === 'gesturestart') {
						cancelAnimation();
					}
					else if (event.type === 'gesturechange') {
						const oldScale = imgXForm.scale;

						imgXForm.x += event.screenX - lastGestureX;
						imgXForm.y += event.screenY - lastGestureY;

						imgXForm.scale *= 1.0 + (event.scale - lastGestureScale);
						imgXForm.scale = clamp(imgXForm.scale, 0.3, 8.0);

						relativeScaleAdjust(oldScale, imgXForm.scale, { x:event.clientX, y:event.clientY });
						updateImage();
					}
					else if (event.type === 'gestureend') {
						performSlideback(false);
					}
					
					lastGestureX = event.screenX;
					lastGestureY = event.screenY;
					lastGestureScale = event.scale;
				}
			}
			
			document.addEventListener('gesturestart', onGesture);
			document.addEventListener('gesturechange', onGesture);
			document.addEventListener('gestureend', onGesture);
		}
	}

	function setupYears() {
		const yearColumn = document.getElementById('year-column');
		const years = window.allYears.reverse();
		const yearCount = window.yearCounts.length;
	
		years.forEach((year, index) => {
			const yearDiv = document.createElement('div');
			yearDiv.className = 'year-div';

			const innerDiv = document.createElement('div');
			innerDiv.className = 'year-text';
			innerDiv.textContent = year;

			yearDiv.appendChild(innerDiv);
			yearDiv.style.setProperty('--pos', `${(index + 0.5) / yearCount}`);
			yearColumn.appendChild(yearDiv);
		});	

		yearsReady = true;
		entryCount += document.querySelector('._a706').children.length;
		updateYearBackground();
	}

	function clampedIndicatorPosition(y) {
		return Math.max(10, Math.min(y, indicator.parentElement.offsetHeight + 10));
	}

	function moveIndicator(y) {
		y = clampedIndicatorPosition(y);
		indicator.style.top = (y - (indicator.offsetHeight / 2) - 10) + "px";
		const scrollPosition = getOffsetForNav((indicator.offsetTop+indicator.offsetHeight/2) / indicator.parentElement.offsetHeight);
		window.scrollTo(0, scrollPosition);		
		updateIndicatorVar();
	}

	function navMouseDown(e) {
		if (!e.defaultPrevented) {
			e.preventDefault();
			moveIndicator(e.clientY);
			mouseIsDown = true;
			document.body.onmousemove = elementDrag;
		}
	}
  
	function elementDrag(e) {
		e.preventDefault();
		moveIndicator(e.clientY);
	}
  
	function endDrag(e) {
		e.preventDefault();
		document.body.onmousemove = null;
		mouseIsDown = false;
	}

	let scrollY = null;
	let nextScrollY;
	let scrollID = null;

	function scrollTimer() {
		scrollID = null;
		throttledScrollToY(nextScrollY);
	}

	function throttledScrollToY(y) {
		if (y != scrollY) {
			nextScrollY = y;
			if (scrollID == null) {
				moveIndicator(y);
				scrollY = y;
				scrollID = setTimeout(scrollTimer, 500);
			}
		}
	}
	
	function touchStart(e) {
		e.preventDefault();
		scrollID = null;
		scrollY = null;
		throttledScrollToY(e.touches[0].clientY);
		mouseIsDown = true;
	}
  
	function touchMove(e) {
		e.preventDefault();
		const newY = e.touches[0].clientY;
		if (newY == clampedIndicatorPosition(newY)) {
			throttledScrollToY(newY);
		}
	}
  
	function touchEnd(e) {
		e.preventDefault();
		mouseIsDown = false;
		if (scrollID) {
			clearInterval(scrollID);
			scrollID = null;
		}
	}
}

function updateIndicatorVar() {
	const yearColumn = document.getElementById('year-column');
	const position = (parseInt(indicator.style.top) + (indicator.offsetHeight / 2)) / indicator.parentElement.offsetHeight;
	yearColumn.style.setProperty('--indicator', position);
}

function updateIndicatorPosition() {
	if (!mouseIsDown) {
		const newTop = getNavForOffset(window.scrollY) * indicator.parentElement.offsetHeight - indicator.offsetHeight/2;
		indicator.style.top = newTop + "px";
		updateIndicatorVar();
	}
}

if (window.numSrcFiles !== undefined) {
	document.addEventListener("DOMContentLoaded", setupNavigation);

	const filePaths = [];
	for (var i = 1; i <= window.numSrcFiles; i++) {
		filePaths.push('entries/entries' + i + '.html');
	}
	loadAndInsertDivsSequentially(filePaths, domReady());
}
else {
	document.addEventListener("DOMContentLoaded", setupEvents);
}
