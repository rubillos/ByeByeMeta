console.log("Load remaining entries");

async function loadAndInsertDivsSequentially(filePaths, domDone) {
	var activeTask = null;
	var index = 1;
	var checkDom = true;

	for (const filePath of filePaths) {
		// Parse the content in a separate asynchronous task
		const parseTask = async (htmlText, priorTask, index) => {
			const parser = new DOMParser();
			const doc = parser.parseFromString(htmlText, 'text/html');
			const divChildren = doc.querySelector('div');
			const targetDiv = document.querySelector('._a706');

			if (priorTask !== null) {
				await priorTask;
			}
			
			if (checkDom) {
				await domDone;
				checkDom = false;
			}

			targetDiv.appendChild(divChildren);
			console.log(index, "Add complete");
		};

		const response = await fetch(filePath);
		const text = await response.text();

		activeTask = parseTask(text, activeTask, index);
		index += 1;
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
  
if (typeof window.numSrcFiles !== 'undefined') {
	var filePaths = [];
	for (var i = 1; i <= window.numSrcFiles; i++) {
		filePaths.push('../entries' + i + '.html');
	}
	loadAndInsertDivsSequentially(filePaths, domReady());
}
