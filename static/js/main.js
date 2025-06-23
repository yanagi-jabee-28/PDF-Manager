const fileInput = document.getElementById('file-input');
const pdfContainer = document.getElementById('pdf-container');
const canvas = document.getElementById('pdf-canvas');
const context = canvas.getContext('2d');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageNumSpan = document.getElementById('page-num');
const pageCountSpan = document.getElementById('page-count');

let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;

function renderPage(num) {
	pageRendering = true;
	pdfDoc.getPage(num).then((page) => {
		const viewport = page.getViewport({ scale: 1.5 });
		canvas.height = viewport.height;
		canvas.width = viewport.width;

		const renderContext = {
			canvasContext: context,
			viewport: viewport
		};
		const renderTask = page.render(renderContext);

		renderTask.promise.then(() => {
			pageRendering = false;
			if (pageNumPending !== null) {
				renderPage(pageNumPending);
				pageNumPending = null;
			}
		});
	});
	pageNumSpan.textContent = num;
}

function queueRenderPage(num) {
	if (pageRendering) {
		pageNumPending = num;
	} else {
		renderPage(num);
	}
}

function onPrevPage() {
	if (pageNum <= 1) {
		return;
	}
	pageNum--;
	queueRenderPage(pageNum);
}

function onNextPage() {
	if (pageNum >= pdfDoc.numPages) {
		return;
	}
	pageNum++;
	queueRenderPage(pageNum);
}

prevPageBtn.addEventListener('click', onPrevPage);
nextPageBtn.addEventListener('click', onNextPage);

fileInput.addEventListener('change', (e) => {
	const file = e.target.files[0];
	if (file.type !== 'application/pdf') {
		alert('Please select a PDF file.');
		return;
	}

	const fileReader = new FileReader();
	fileReader.onload = function () {
		const typedarray = new Uint8Array(this.result);
		pdfjsLib.getDocument(typedarray).promise.then((pdf) => {
			pdfDoc = pdf;
			pageCountSpan.textContent = pdf.numPages;
			renderPage(pageNum);
		});
	};
	fileReader.readAsArrayBuffer(file);
});
