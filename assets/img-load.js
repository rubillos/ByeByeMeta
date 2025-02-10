document.addEventListener("DOMContentLoaded", function() {
	const urlParams = new URLSearchParams(window.location.search);
	const mainImg = document.getElementById('main-img');
    const cacheImg = document.createElement("img");
    var imgSrc = ""

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

	document.querySelector('.close-x').addEventListener('click', function(e) {
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

	mainImg.addEventListener('click', function(e) {
		e.preventDefault();
		nextImage();
	});

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
			} else if (nextKeys.includes(event.key)) {
				nextImage();
			}
		}
	});

	mainImg.addEventListener('touchstart', handleTouchStart, false);
	mainImg.addEventListener('touchend', handleTouchEnd, false);

	var xDown = null;
	var yDown = null;

	function getTouches(e) {
		return e.touches || e.originalEvent.touches;
	}

	function handleTouchStart(e) {
		e.preventDefault();
		const firstTouch = getTouches(e)[0];
		xDown = firstTouch.clientX;
		yDown = firstTouch.clientY;
	}

	function handleTouchEnd(e) {
		e.preventDefault();
		if (!xDown || !yDown) {
			return;
		}

		var touches = e.changedTouches;

		if (touches.length == 1) {
			const xDiff = xDown - touches[0].clientX;
			const yDiff = yDown - touches[0].clientY;
            const dist = Math.sqrt(xDiff * xDiff + yDiff * yDiff);

            if (dist > 10) {
                let angle = Math.atan2(yDiff, xDiff) * 180 / Math.PI;
                let direction = Math.round((angle + 360) / 45) % 8;
                switch (direction) {
                    case 2: // up
                    case 4: // right
                        previousImage();
                        break;
                    case 6: // down
                        window.close();
                        break;
                    case 0: // left
                        nextImage();
                        break;
                }
            }
            else {
                nextImage();
            }
		}

		xDown = null;
		yDown = null;
	}
});
