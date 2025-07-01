// RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
// Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

function logElementTreeWithIds(root, indent = "") {
	if (!(root instanceof Element)) return;

	if (root.id) {
		const tag = root.tagName.toLowerCase();
		const classes = [...root.classList].map(cls => `.${cls}`).join("");
		console.log(`${indent}${tag}${classes}#${root.id}`);
	}

	for (const child of root.children) {
		logElementTreeWithIdsOnly(child, indent + "	 ");
	}
}

function inCls(el, ...args) {
	if (!(el instanceof Element)) return false;
	for (let arg of args)
		if (el.classList.contains(arg))
			return true;
	return false;
}

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

function prettyJSON(data, indent="", autofold=false, addFinalNewline=true) {
	if (autofold && typeof data === "string" && data.length > 80) {
		let lines = [];
		for (let line of foldSoftPreserve(data))
			lines.push(indent + JSON.stringify(line))
		return lines.join(",\n");
	}

	if (!Array.isArray(data) || !data.length ||
			(autofold && JSON.stringify(data).length < 80))
		return indent + JSON.stringify(data);

	if (typeof data[0] == "string" &&
			(data[0] == "Text" || data[0].startsWith("Text ")))
		autofold = true;

	let s = [indent + "[" + JSON.stringify(data[0])];
	for (let i = 1; i < data.length; i++)
		s.push(",\n" + prettyJSON(data[i],
				indent + "    ", autofold, false));
	s.push(addFinalNewline ? "]\n" : "]");

	return s.join("");
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

risParList = [];
risContentBlocks = {};
_rex_initialize = () => {
	document.querySelectorAll("div.document > div.documentContent").forEach(el => {
		const parName = el.querySelector(":scope > h2.onlyScreenreader:first-child").
				textContent.trimStart().trimEnd();
		// if (parName != "§ 31") return;
		risContentBlocks[parName] = el;
		risParList.push(parName);
	});
	_rex_initialize = () => undefined;
};

class RisExAST {
	risClsToRisExTyp = (() => {
		let tab = {
			"Head": {
				"Erl": ["ErlUeberschrL"],
				"Art": ["UeberschrArt"],
				"": ["UeberschrG1", "UeberschrG1-",
				     "UeberschrG2","UeberschrG1-AfterG2" ]
			},
			"Title": {
				"": ["UeberschrPara"]
			},
			"Text": {
				"Aufz": ["AufzaehlungE0", "AufzaehlungE1", "AufzaehlungE2"],
				"End": ["SchlussteilE0", "SchlussteilE1", "SchlussteilE2",
					"SchlussteilE0_5", "SatznachNovao"],
				"Erl": ["ErlText"],
				"": ["Abs", "Abs_small_indent"]
			},
			"": ["AlignCenter", "AlignJustify"]
		};
		tab["SubHdr"] = tab["Head"];
		let db = {};
		for (let tag in tab) {
			if (tag == "")
				continue;
			db[tag] = {};
			for (let typ in tab[tag]) {
				for (let cls of tab[""])
					db[tag][cls] = "";
				for (let cls of tab[tag][typ])
					db[tag][cls] = typ;
			}
		}
		return db;
	})();

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

	typeIn(...args) {
		return args.indexOf(this.get("type")) >= 0;
	}

	visitElement(el) {
		if (el.tagName == "H5" && inCls(el, "GldSymbol"))
			return;

		if (el.tagName == "DIV" && inCls(el, "MarginTop4"))
			return el.querySelectorAll(":scope > *").
					forEach(child => this.visitElement(child));

		let ast = new RisExAST(this, el);

		if (el.tagName == "H4" || inCls(el, "UeberschrG2")) {
			if (inCls(el, "UeberschrPara"))
				return ast.parseTitle();
			return ast.parseHeading();
		}

		if (el.tagName == "DIV" || el.tagName == "P") {
			if (inCls(el, "ParagraphMitAbsatzzahl"))
				return ast.parseAbsLst();
			if (inCls(el, "Abs", "Abs_small_indent", "SatznachNovao", "ErlText",
					"AufzaehlungE0", "AufzaehlungE1", "AufzaehlungE2",
					"SchlussteilE0", "SchlussteilE1", "SchlussteilE2",
					"SchlussteilE0_5"))
				return ast.parseText();
			if (inCls(el, "AbbildungoderObjekt"))
				return ast.parseMedia();
		}

		if (el.tagName == "OL" && inCls(el, "wai-list", "wai-absatz-list"))
			return ast.parseLst();

		if (inCls(el, "Abstand"))
			return ast.set("type", "Break");

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
		if (inCls(el, "SymE1", "SymE2") &&
				el?.firstElementChild?.firstElementChild)
			this.set("sym", el.firstElementChild.firstElementChild.textContent);

		el = this.baseElement?.firstChild?.firstChild;
		if (inCls(el, "Absatzzahl"))
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

	parseMedia() {
		this.set("type", "Media");
		for (let el = this.baseElement.firstChild; el; el = el.nextSibling) {
			if (el.nodeType === 3 && el.nodeValue.trim() != "") {
				let ast = new RisExAST(this, el);
				ast.set("type", "Text");
				ast.text = [el.nodeValue.trim()];
			}
			if (el.nodeType === 1) {
				if (el.tagName == "IMG") {
					let ast = new RisExAST(this, el);
					ast.set("type", "Img");
					ast.text.push(el.getAttribute("src"));
				}
			}
		}

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
			if (this.typeIn("Par"))
				tag = "Par " + this.get("par");

			if (this.typeIn("Head", "Title", "Text")) {
				let inParPretext = true;
				for (let c of this.parentObj.children) {
					if (c === this)
						break;
					if (c.typeIn("Head", "Title"))
						continue;
					inParPretext = false;
					break;
				}

				tag = this.get("type");
				if (tag == "Text" && this.text.length == 0)
					return null;

				let tagTyp = "";
				let isHeaderOrTitle = this.typeIn("Head", "Title");
				if (isHeaderOrTitle && !inParPretext)
					tag = "SubHdr";
				this.baseElement?.classList?.forEach(cls => {
					if (cls in this.risClsToRisExTyp[tag]) {
						let typ = this.risClsToRisExTyp[tag][cls];
						if (typ != "") tagTyp += " " + typ;
					} else
						tagTyp += " ?" + cls;
				});
				tag += tagTyp;
				color = "cyan";
			}

			if (this.typeIn("AbsLst", "NumLst", "LitLst", "Lst",
			                "Break", "Media", "Img")) {
				tag = this.get("type");
				if (tag == "AbsLst") tag = "List Abs";
				if (tag == "NumLst") tag = "List Num";
				if (tag == "LitLst") tag = "List Lit";
				if (tag == "Lst") tag = "List";
				color = null;
			}

			if (this.typeIn("Item")) {
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

		for (let child of this.children) {
			let c = child.getJSON(verbose, annotate);
			if (c !== null) s.push(c);
		}

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
	return ["Meta FassungVom", document.querySelector("#Title").textContent.
			replace(/.*, Fassung vom /s, "").trim()];
}

function getMetaLastChange() {
	let lastChange;
	document.querySelectorAll("div#content > div.document > div.documentContent:first-child h3").
			forEach(el => { if (el.textContent == "Änderung") lastChange = el.nextElementSibling.
			firstElementChild.lastElementChild.textContent; })
	return ["Meta LastChange", lastChange];
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
		id = el.querySelector(":scope > div.embeddedContent").id;
		data.push(p + " #" + id);

		if (p === stopPar)
			break;
	}

	id = el.nextElementSibling?.querySelector(":scope > div.embeddedContent")?.id;
	data.push("END #" + (id ?? "footer"));
	return data;
}

function getMetaLocalChanges() {
	return ["Meta LocalChanges" /* none applied yet */ ];
}

function getMetaPromulgation() {
	return ["Meta Promulgation", document.querySelector(".PromKlEinlSatz")?.textContent ?? ""];
}

function risExtractor(parName=null, stopPar=null, docName=null, verbose=false, annotate=false) {
	_rex_initialize();
	if (!parName) {
		let doc = ["LawDoc" + (docName ? " " + docName : "")];
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
	// window.dbgAst = ast;
	ast.set("par", parName);
	ast.parsePar();
	return ast.getJSON(verbose, annotate);
}

const isNode = typeof process !== 'undefined' &&
               process.versions != null &&
               process.versions.node != null;

if (isNode) {
	const originalConsoleError = console.error;
	console.error = (...args) => {
		if (args[0]?.includes?.("Could not parse CSS @import URL")) return;
		originalConsoleError(...args);
	};
	const fs = require("fs");
	const { JSDOM, ResourceLoader } = require("jsdom");
	const src = process.argv[2];
	const html = fs.readFileSync(src, "utf-8");
	class NoopResourceLoader extends ResourceLoader {
		fetch() { return null; /* block everything */ }
	};
	const dom = new JSDOM(html, {
		resources: new NoopResourceLoader(),
		runScripts: "outside-only"
	});
	global.document = dom.window.document; // make it global if your code expects it
	global.Element = dom.window.Element;
	process.stdout.write(prettyJSON(risExtractor()))
}
