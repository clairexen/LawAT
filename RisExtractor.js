// RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
// Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

// for debug annotations
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

risParList = []
risContentBlocks = {}
document.querySelectorAll("div.document > div.documentContent").forEach(el => {
	parName = el.querySelector(":scope > h2.onlyScreenreader:first-child").
			textContent.trimStart().trimEnd();
	risContentBlocks[parName] = el;
	risParList.push(parName);
})

class RisExAST {
	constructor(parentObj, baseElement) {
		this.parentObj = parentObj;
		if (this.parentObj !== null)
			this.parentObj.children.push(this);
		this.baseElement = baseElement;
		this.baseElementSelector = getCssSelector(baseElement);
		this.properties = {};
		this.preTokens = [];
		this.children = [];
		this.postTokens = [];
	}

	getBase() {
		// return document.querySelector(this.baseElementSelector);
		return this.baseElement;
	}

	set(key, value) {
		this.properties[key] = value;
	}

	get(key, defaultValue=null) {
		if (key in this.properties)
			return this.properties[key];
		return defaultValue;
	}

	visitBlockListItem(pState, el) {
		if (el.tagName == "H4") {
			ast = new RisExAST(this, el)
			if (el.classList.contains("UeberschrPara"))
				return ast.parseParHeading(pState);
			return ast.parseHeading(pState);
		}

		ast = new RisExAST(this, el);
		ast.set("type", "unknown");
		ast.set("text", el.textContent);
		return ast;
	}

	parseHeading(pState) {
		this.set("type", "heading");
		this.set("text", el.textContent);
	}

	parseParHeading(pState) {
		this.set("type", "par-heading");
		this.set("text", el.textContent);
	}

	parseBlock(pState) {
		this.set("type", "block");
		el = this.getBase();
		content = el.querySelector(":scope > div.embeddedContent > div > div.contentBlock");
		content.querySelectorAll(":scope > *").forEach(item =>
				this.visitBlockListItem(pState, item));
	}
}

function risExtractor(parName) {
	risExtractor.pState = { "parName": parName };
	// risExtractor.pState.fooBar = 0;
	el = risContentBlocks[parName];
	risExtractor.ast = new RisExAST(null, el);
	risExtractor.ast.set("parName", parName);
	risExtractor.ast.parseBlock(risExtractor.pState, 1);
	return risExtractor.ast;
}
