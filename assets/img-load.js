document.addEventListener("DOMContentLoaded", function() {
	const urlParams = new URLSearchParams(window.location.search);
	const touchDiv = document.getElementById('touch-div');
	const mainImg = document.getElementById('main-img');
	const cacheImg = document.createElement("img");
	const hasTouch = 'ontouchstart' in window;
	var activeAnimation = null;
	var imgSrc = "";
	
	cacheImg.style = "position:absolute;z-index:-1000;max-width:100px;max-height:100px;opacity:0;";
	document.body.appendChild(cacheImg);

	function preloadNext() {
		const src = nextSrc();
		if (src) {
			cacheImg.src = "../" + src;
		}
	}

	mainImg.addEventListener('load', preloadNext);

	setSrc(urlParams.get('src'));

	var imgUrls = localStorage.getItem('img_urls');
	if (imgUrls) {
		imgUrls = imgUrls.split(",");
	}

	document.querySelector('#close-x').addEventListener('click', function(e) {
		e.preventDefault();
		window.close();
	});

	function setSrc(src) {
		if (src) {
			mainImg.src = "../" + src;
			imgSrc = src;
			localStorage.setItem('last_url', imgSrc);
		}
	}

	function nextSrc() {
		if (imgUrls) {
			const currentIndex = imgUrls.indexOf(imgSrc);
			if (currentIndex < imgUrls.length - 1) {
				return imgUrls[currentIndex + 1];
			}
		}
		else {
			return null;
		}
	}

	function previousSrc() {
		if (imgUrls) {
			const currentIndex = imgUrls.indexOf(imgSrc);
			if (currentIndex > 0) {
				return imgUrls[currentIndex - 1];
			}
		}
		else {
			return null;
		}
	}

	function nextImage() {
		setSrc(nextSrc());
	}

	function previousImage() {
		setSrc(previousSrc());
	}

	document.addEventListener('keydown', function(event) {
		const closeKeys = ['Escape', 'Enter'];
		const nextKeys = ['ArrowDown', 'ArrowRight', ' '];
		const prevKeys = ['ArrowUp', 'ArrowLeft'];

		if (closeKeys.includes(event.key)) {
			window.close();
		}
		else if (imgUrls) {
			if (prevKeys.includes(event.key)) {
				previousImage();
				performSlideback(true);
			} else if (nextKeys.includes(event.key)) {
				nextImage();
				performSlideback(true);
			}
		}
	});

	if (hasTouch) {		
		touchDiv.addEventListener('touchstart', handleTouchStart, false);
		touchDiv.addEventListener('touchmove', handleTouchMove, false);
		touchDiv.addEventListener('touchend', handleTouchEnd, false);
	}
	else {
		touchDiv.addEventListener('click', function(e) {
			e.preventDefault();
			nextImage();
			performSlideback(true);
		});
	}

	var imgXForm = { x:0, y:0, scale:1.0 };

	var startSize = null;
	var startOne = null;
	var startTwo = null;
	var centerTwo = null;
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

	function touchPoint(e) {
		return { x:e.targetTouches[0].clientX, y:e.targetTouches[0].clientY };
	}

	function handleTouchStart(e) {
		e.preventDefault();
		cancelAnimation();

		if (e.targetTouches.length == 1) {
			startOne = touchPoint(e);
			lastOne = { ...startOne };
			startTime = Date.now();
		}
		else if (e.targetTouches.length == 2) {
			startTwo = touchCenter(e);
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
			imgXForm.x += pt.x - lastOne.x;
			imgXForm.y += pt.y - lastOne.y;
			lastOne = pt;
			updateImage();
		}
		else if (e.targetTouches.length == 2) {
			const pt = touchCenter(e);
			imgXForm.scale = startXForm.scale * e.scale;
			const scaleChange = imgXForm.scale - startXForm.scale;
			const xChange = scaleChange * startSize.width;
			const yChange = scaleChange * startSize.height;
			imgXForm.x = startXForm.x + (pt.x - startTwo.x) + xChange * centerTwo.x;
			imgXForm.y = startXForm.y + (pt.y - startTwo.y) + yChange * centerTwo.y;
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

			if (startOne && startTwo==null && duration < 200 && e.scale == 1 && e.rotation == 0) {
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

	function clampXForm(xform, resetScale) {
		var newXForm = { ...xform };

		newXForm.scale = (resetScale) ? 1.0 : clamp(xform.scale, 1.0, 5.0);

		if (newXForm.scale > 1.0) {
			const size = imageSize();
			const maxX = Math.max(0, (size.width * newXForm.scale - window.innerWidth) / 2.0);
			const maxY = Math.max(0, (size.height * newXForm.scale - window.innerHeight) / 2.0);

			newXForm.x = clamp(xform.x, -maxX, maxX);
			newXForm.y = clamp(xform.y, -maxY, maxY);
		}
		else {
			newXForm.x = 0;
			newXForm.y = 0;
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
		const duration = 250;
		const oldXForm = { ...imgXForm };

		function animate() {
			const now = Date.now();
			const fraction = (now - startTime) / duration;

			animationActive = null;

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
			event.preventDefault();
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
		}, {
			passive: false
		});

		var lastGestureX = 0;
		var lastGestureY = 0;
		var lastGestureScale = 1.0;

		function onGesture(event) {
			event.preventDefault();
			
			if (event.type === 'gesturestart') {
				lastGestureX = event.screenX;
				lastGestureY = event.screenY;
				lastGestureScale = event.scale;
			}
			else if (event.type === 'gesturechange') {
				imgXForm.x += event.screenX - lastGestureX;
				imgXForm.y += event.screenY - lastGestureY;
			}
			
			const oldScale = imgXForm.scale;

			imgXForm.scale *= 1.0 + (event.scale - lastGestureScale);
			imgXForm = clampXForm(imgXForm, false);
			relativeScaleAdjust(oldScale, imgXForm.scale, { x:event.clientX, y:event.clientY });
			updateImage();

			lastGestureX = event.screenX;
			lastGestureY = event.screenY;
			lastGestureScale = event.scale;
		}
		
		document.addEventListener('gesturestart', onGesture);
		document.addEventListener('gesturechange', onGesture);
		document.addEventListener('gestureend', onGesture);
	}
});
