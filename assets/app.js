var yearsReady = false;
var entryCount = 0;
var navOffsets = [];
var yearOffsets = [];
var adjustedYearOffsets = [];

const search = new URLSearchParams(window.location.search);
const showMemories = search.has('memories');
let currentDate = new Date();
if (search.has('day')) {
	const days = search.get('day').replaceAll('-', '/').split('/');
	if (days.length == 2) {
		currentDate = new Date(currentDate.getFullYear(), parseInt(days[0]) - 1, parseInt(days[1]));
	}
}
else if (search.has('offset')) {
	const offset = parseInt(search.get('offset'));
	currentDate = new Date(currentDate.getTime() + offset * 24 * 60 * 60 * 1000);
}
const monthDayID = `d${(currentDate.getMonth() + 1) * 100 + currentDate.getDate()}`;

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

function initialMemoriesSetup() {
	const banner = document.querySelector('.banner');
	if (banner) {
		if (showMemories) {
			const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
			const month = monthNames[currentDate.getMonth()];
			const day = currentDate.getDate();
			banner.textContent = `Memories - ${month} ${day}`;
		}
		banner.addEventListener('click', () => {
			const url = new URL(window.location);
			if (url.searchParams.has('memories')) {
				url.searchParams.delete('memories');
			} else {
				url.searchParams.set('memories', 'true');
			}
			window.location.href = url.toString();
		});
		banner.style.cursor = "pointer";
	}
}

function finalMemoriesCleanup() {
	if (showMemories) {
		const visList = cleanHeadings();
		if (visList.length >= 1 && isYearMark(visList[visList.length - 1])) {
			visList[visList.length - 1].style.display = "none";
		}
		if (visList.length == 1 && isYearMark(visList[0])) {
			visList[0].style.display = "none";
		}
	}
}

function createRoundedRectPath(x, y, width, height, llRadius, lrRadius, vOffset) {
	width = parseInt(width);
	height = parseInt(height);
	llRadius = parseInt(Math.min(llRadius, height));
	lrRadius = parseInt(Math.min(lrRadius, height));
	return (
		`M${x},${(y-vOffset)}h${width}v${(height+vOffset-lrRadius)}a${lrRadius},${lrRadius} 0 0 1 ${-lrRadius},${lrRadius}h${(lrRadius + llRadius - width)}a${-llRadius},${-llRadius} 0 0 1 ${-llRadius},${-llRadius}v${(llRadius-vOffset-height)}z`
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
				initialMemoriesSetup();
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

	finalMemoriesCleanup();

	const navColumn = document.getElementById('year-column');
	const columnHeight = navColumn.offsetHeight;
	const navDivs = navColumn.children;
	const yearMarks = document.querySelectorAll('.year-mark');
	yearMarks.forEach((yearMark, i) => {
		navDivs[i].style.display = yearMark.style.display;
	});
	navOffsets = [];
	yearMarks.forEach((mark, index) => {
		if (mark.style.display != "none") {
			yearOffsets.push(mark.offsetTop);
			navOffsets.push(navDivs[index].offsetTop / columnHeight);
		}
	});
	yearOffsets.push(document.body.scrollHeight);
	navOffsets.push(1);
	makeAdjustedYearOffsets();

	indicator.style.display = "flex";
	updateIndicatorPosition();
	setupEntryEvents();
}

function setupEntryEvents() {
	if (showIndexes) {
		addAllIndexes();
	}
	else {
		document.querySelectorAll('._a6-g').forEach(element => {
			element.onmouseenter = showEIndex;
		});
	}

	const imgUrls = [];
	document.querySelectorAll('img._a6_o').forEach(img => {
		let parentDiv = img.closest('div._a6-g');
		if (parentDiv && parentDiv.style.display !== "none") {
			img.onclick = showImage;
			imgUrls.push(img.getAttribute('src'));
		}
	});
	localStorage.setItem('img_urls', imgUrls);
	localStorage.setItem('last_url', "");

	document.addEventListener('visibilitychange', function() {
		if (document.visibilityState === 'visible') {
			const lastUrl = localStorage.getItem('last_url');
			if (lastUrl) {
				const img = document.querySelector(`img[src="${lastUrl}"]`);
				if (img) {
					img.scrollIntoView({ behavior: 'instant', block: 'center' });
				}
				localStorage.setItem('last_url', "");
			}
		}
	});

	window.addEventListener('resize', makeAdjustedYearOffsets);

	document.addEventListener('keydown', function(event) {
		if (event.key === 'Enter' || event.key === 'ArrowRight') {
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

function showImage(event) {
	const element = event.currentTarget;
	const src = element.getAttribute('src');
	window.open(`assets/img-load.html?src=${encodeURIComponent(src)}`, '_blank');
}

var mouseIsDown = false;

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
  
function setupContent() {
	fetch('assets/extra.html')
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
				window.addEventListener('scroll', updateIndicatorPosition);

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

		document.documentElement.style.setProperty('--nav-width', `${(yearColumn.offsetWidth * 2.0)}px`);

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
	document.addEventListener("DOMContentLoaded", setupContent);

	const filePaths = [];
	for (var i = 1; i <= window.numSrcFiles; i++) {
		filePaths.push('entries/entries' + i + '.html');
	}
	loadAndInsertDivsSequentially(filePaths, domReady());
}
else {
	document.addEventListener("DOMContentLoaded", setupEntryEvents);
}
