// RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
// Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

function getCssSelector(el) {
	if (!(el instanceof Element)) return null;
	const path = [];

	while (el && el.nodeType === 1 && el.tagName.toLowerCase() !== "html") {
		let selector = el.tagName.toLowerCase();

		if (el.id) {
			selector += `#${el.id}`;
			path.unshift(selector);
			break; // ID is unique in the document
		} else {
			const siblings = Array.from(el.parentNode.children)
					.filter(e => e.tagName === el.tagName);
			if (siblings.length > 1) {
				const index = siblings.indexOf(el) + 1;
				selector += `:nth-of-type(${index})`;
			}
			path.unshift(selector);
			el = el.parentElement;
		}
	}

	return path.join(" > ");
}

function injectLabelStyle(s, c="red") {
	let cssTemplate = `
.@name@ {
		border: 2px solid @color@;
		position: relative;
		padding: 5px;
		margin: 5px;
}

.@name@::after {
		content: "@label@";
		color: @color@;
		font-weight: bold;
		position: absolute;
		top: var(--@name@-label-top, 0);
		left: var(--@name@-label-left, 100%);
		white-space: nowrap;
}
`;

	const n = s.toLowerCase().replaceAll(" ", "-") + "-highlight-" + c;

	if (!document.getElementById("css-" + n)) {
		let css = cssTemplate;
		css = css.replaceAll(/@name@/g, n);
		css = css.replaceAll(/@label@/g, s);
		css = css.replaceAll(/@color@/g, c);
		const style = document.createElement("style");
		style.setAttribute("id", "css-" + n);
		style.textContent = css;
		document.head.appendChild(style);
	}

	return n;
}

function highlightElement(el, s, c="red") {
	if (!(el instanceof Element)) return;
	const className = injectLabelStyle(s, c);
	if (!el.classList.contains(className)) {
		el.classList.add(className);
		requestAnimationFrame(() => {
			const page = document.getElementById("page");
			if (!page) return;
			const pageRect = page.getBoundingClientRect();
			const elRect = el.getBoundingClientRect();
			const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
			const labelLeft = pageRect.right + scrollLeft + parseFloat(getComputedStyle(document.documentElement).fontSize || "16") * 1;
			const offsetLeft = labelLeft - (elRect.left + scrollLeft);
			el.style.setProperty(`--${className}-label-left`, `${offsetLeft}px`);
			el.style.setProperty(`--${className}-label-top`, `0px`);
		});
	}
}

function foldSoftPreserve(str, maxWidth = 80) {
	const lines = [];
	let lineStart = 0;
	let lastBreak = -1;

	for (let i = 0; i < str.length; i++) {
		const char = str[i];

		// Record last possible break point (after a space)
		if (char === ' ') lastBreak = i;

		// If current line exceeds maxWidth
		if (i - lineStart >= maxWidth) {
			if (lastBreak > lineStart) {
				lines.push(str.slice(lineStart, lastBreak + 1));
				lineStart = lastBreak + 1;
				i = lineStart - 1; // restart from next char
			} else {
				// No space found, hard-break
				lines.push(str.slice(lineStart, i));
				lineStart = i;
				lastBreak = -1;
			}
		}
	}

	// Add remaining text
	if (lineStart < str.length)
		lines.push(str.slice(lineStart));

	return lines;
}

function prettyJSON(data, indent="", autofold=false) {
	if (autofold && typeof data === "string" && data.length > 80) {
		let lines = [];
		for (let line of foldSoftPreserve(data))
			lines.push(indent + JSON.stringify(line))
		return lines.join(",\n");
	}

	if (!Array.isArray(data) || !data.length ||
			(autofold && JSON.stringify(data).length < 80))
		return indent + JSON.stringify(data);

	if (data[0] == "Text")
		autofold = true

	let s = [indent + "[" + JSON.stringify(data[0])];
	for (let i = 1; i < data.length; i++)
		s.push(",\n" + prettyJSON(data[i],
				indent + "    ", autofold));
	s.push("]");

	return s.join("")
}

function isVisible(el) {
	if (!el) return false;
	if (el.classList.contains("sr-only"))
		return false;
	return true;
}

function getVisibleTextTree(el) {
	if (el.nodeType == 3)
		return el.nodeValue.length ? [el.nodeValue] : [];

	if (el.nodeType != 1 || !isVisible(el))
		return [];

	if (el.tagName == "BR")
		return ["\n"];

	if (el.classList.contains("GldSymbol"))
		return [];

	let tag = null, snippets = [], visitChildren = true;

	function addSnippet(s) {
		if (Array.isArray(s) || !snippets.length ||
				Array.isArray(snippets[snippets.length-1]))
			snippets.push(s);
		else
			snippets[snippets.length-1] += s;
	}

	if (el.classList.contains("Absatzzahl"))
		visitChildren = false;

	if (el.classList.contains("Kursiv"))
		tag = "Anm";

	if (visitChildren) {
		for (let child of el.childNodes) {
			for (let snip of getVisibleTextTree(child))
				addSnippet(snip);
		}
	}

	if (tag !== null)
		snippets = [[tag].concat(snippets)];
	return snippets;
}

risParList = []
risContentBlocks = {}
document.querySelectorAll("div.document > div.documentContent").forEach(el => {
	const parName = el.querySelector(":scope > h2.onlyScreenreader:first-child").
			textContent.trimStart().trimEnd();
	risContentBlocks[parName] = el;
	risParList.push(parName);
});

class RisExAST {
	constructor(parentObj, baseElement) {
		this.parentObj = parentObj;
		if (this.parentObj !== null)
			this.parentObj.children.push(this);
		this.baseElement = baseElement;
		this.properties = {};
		this.children = [];
		this.text = [];
		// this.set("path", getCssSelector(baseElement));
	}

	set(key, value) {
		this.properties[key] = value;
	}

	get(key, defaultValue=undefined) {
		if (key in this.properties)
			return this.properties[key];
		return defaultValue;
	}

	visitElement(el) {
		if (el.tagName == "H5" && el.classList.contains("GldSymbol"))
			return;

		if (el.tagName == "DIV" && el.classList.contains("MarginTop4"))
			return el.querySelectorAll(":scope > *").
					forEach(child => this.visitElement(child));

		let ast = new RisExAST(this, el);

		if (el.tagName == "H4") {
			if (el.classList.contains("UeberschrPara"))
				return ast.parseTitle();
			return ast.parseHeading();
		}

		if (el.tagName == "DIV" || el.tagName == "P") {
			if (el.classList.contains("ParagraphMitAbsatzzahl"))
				return ast.parseAbsLst();
			if (el.classList.contains("Abs_small_indent") ||
					el.classList.contains("AufzaehlungE1") ||
					el.classList.contains("SchlussteilE0_5") ||
					el.classList.contains("Abs"))
				return ast.parseText();
		}

		if (el.tagName == "OL" && el.classList.contains("wai-list"))
			return ast.parseLst();

		ast.set("type", "Unknown");
		ast.set("path", getCssSelector(el));
		ast.set("tag", el.tagName);
		ast.set("class", el.getAttribute("class"));
		ast.text = getVisibleTextTree(el);
	}

	parseHeading() {
		let s = getVisibleTextTree(this.baseElement)[0].split("\n");
		this.set("type", "Head");
		this.text = [s[0]];

		for (let i = 1; i < s.length; i++) {
			let ast = new RisExAST(this.parentObj, this.baseElement);
			ast.set("type", "Head");
			ast.text = [s[i]];
		}
	}

	parseTitle() {
		this.set("type", "Title");
		this.text = getVisibleTextTree(this.baseElement);
	}

	parseItem() {
		this.set("type", "Item");

		let el = this.baseElement?.previousSibling;
		if (el?.classList?.contains("SymE1") && el?.firstElementChild?.firstElementChild)
			this.set("sym", el.firstElementChild.firstElementChild.textContent);

		el = this.baseElement?.firstChild?.firstChild;
		if (el?.classList?.contains("Absatzzahl"))
			this.set("sym", el.textContent);

		this.baseElement.querySelectorAll(":scope > *").
				forEach(el => this.visitElement(el));
	}

	parseAbsLst() {
		this.set("type", "AbsLst");
		this.baseElement.querySelectorAll(":scope > ol > li > div.content").
				forEach(el => {
			let ast = new RisExAST(this, el);
			ast.parseItem();
		});
	}

	parseLst() {
		this.set("type", "Lst");
		this.baseElement.querySelectorAll(":scope > li > div.content").
				forEach(el => {
			let ast = new RisExAST(this, el);
			ast.parseItem();
			if (ast.get("sym")?.match(/^[0-9]+[a-z]*\.$/))
				this.set("type", "NumLst");
			if (ast.get("sym")?.match(/^[a-z]+[0-9]*\)$/))
				this.set("type", "LitLst");
		});
	}

	parseText() {
		this.set("type", "Text");
		this.text = getVisibleTextTree(this.baseElement);

		if (this.baseElement?.previousElementSibling?.classList?.contains("GldSymbol") &&
				this.text.length && typeof this.text[0] === "string")
			this.text[0] = this.text[0].trimStart();
	}

	parsePar() {
		this.set("type", "Par");
		this.contentElement = this.baseElement.querySelector(
				":scope > div.embeddedContent > div > div.contentBlock");
		this.contentElement.querySelectorAll(":scope > *").forEach(item =>
				this.visitElement(item));
	}

	getJSON(verbose=false, annotate=false) {
		let tag = this.properties, color = "blue", s = [];

		if (!verbose) {
			if (this.get("type") == "Par")
				tag = "Par " + this.get("par");

			if (this.get("type") == "Head" || this.get("type") == "Title") {
				tag = this.get("type");
				color = "cyan";
			}

			if (this.get("type") == "AbsLst" || this.get("type") == "NumLst" ||
					this.get("type") == "LitLst" || this.get("type") == "Text") {
				tag = this.get("type");
				color = null;
			}

			if (this.get("type") == "Item") {
				tag = "Item " + this.get("sym");
				color = "green";
			}
		}

		if (annotate && color !== null) {
			if (typeof tag !== "string") color = "red";
			highlightElement(this.baseElement, this.get("type"), color);
		}

		s.push(tag);

		for (let item of this.text)
			s.push(item);

		for (let child of this.children)
			s.push(child.getJSON(verbose, annotate));

		return s;
	}
}

function getMetaLangtitel() {
	let langtitel = null;
	document.querySelectorAll("h3").forEach(el => {
		if (langtitel === null && el.textContent == "Langtitel")
			langtitel = el.nextSibling.nodeValue.trim();
	});
	return ["Meta Langtitel", langtitel];
}

function getMetaFassungVom() {
	return ["Meta FassungVom", "..."];
}

function getMetaLastChange() {
	return ["Meta LastChange", "..."];
}

function getMetaRisSrcLink() {
	return ["Meta RisSrcLink", document.URL.split("#")[0]];
}

function getMetaParAnchors(stopPar) {
	let el, id, data = ["Meta ParAnchors"];

	for (let p of risParList) {
		if (p === "§ 0")
			continue;

		el = risContentBlocks[p];
		console.log(p, el);
		id = el.querySelector(":scope > div.embeddedContent").id;
		data.push(p + " #" + id);

		if (p === stopPar)
			break;
	}

	id = el.nextElementSibling.querySelector(":scope > div.embeddedContent").id;
	data.push("END #" + id);
	return data;
}

function getMetaLocalChanges() {
	return ["Meta LocalChanges" /* none applied yet */ ];
}

function getMetaPromulgation() {
	return ["Meta Promulgation", "..."];
}

function risExtractor(parName=null, stopPar=null, docName=null, verbose=false, annotate=false) {
	if (!parName) {
		let doc = ["RisDoc" + (docName ? " " + docName : "")];
		doc.push(getMetaLangtitel());
		doc.push(getMetaFassungVom());
		doc.push(getMetaLastChange());
		doc.push(getMetaRisSrcLink());
		doc.push(getMetaParAnchors(stopPar));
		doc.push(getMetaLocalChanges());
		doc.push(getMetaPromulgation());
		for (let p of risParList) {
			if (p !== "§ 0")
				doc.push(risExtractor(p, null, null, verbose, annotate));
			if (p === stopPar)
				break;
		}
		return doc;
	}
	let el = risContentBlocks[parName];
	let ast = new RisExAST(null, el);
	ast.set("par", parName);
	ast.parsePar();
	// risExtractor.debugAst = ast;
	return ast.getJSON(verbose, annotate);
}

