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

function isVisible(el) {
	if (!el) return false;
	const style = window.getComputedStyle(el);
	const rect = el.getBoundingClientRect();
	return (
		style.display !== "none" &&
		style.visibility !== "hidden" &&
		style.opacity !== "0" &&
		rect.width > 0 &&
		rect.height > 0 &&
		rect.bottom > 0 &&
		rect.right > 0 &&
		el.offsetParent !== null
	);
}

function getVisibleTextTree(el) {
	if (el.nodeType == 3)
		return el.nodeValue.length ? [el.nodeValue] : [];

	if (el.nodeType != 1 || !isVisible(el))
		return [];

	if (el.classList.contains("GldSymbol"))
		return [];

	let tag = null, snippets = [];
	for (let child of el.childNodes) {
		for (let snip of getVisibleTextTree(child))
			snippets.push(snip);
	}

	if (el.classList.contains("Absatzzahl")) {
		tag = "AbsZ";
		snippets.push(" ");
	}

	if (el.classList.contains("Kursiv")) {
		tag = "Anm";
		snippets.push(" ");
	}

	if (tag !== null)
		snippets = [[tag].concat(snippets)];
	console.log(snippets);
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
			let ast = new RisExAST(this, el);
			if (el.classList.contains("UeberschrPara"))
				return ast.parseParHeading(pState);
			return ast.parseHeading(pState);
		}

		let ast = new RisExAST(this, el);
		ast.set("type", "unknown");
		ast.set("text", getVisibleTextTree(el));
		ast.set("tag", el.tagName);
		ast.set("class", el.getAttribute("class"));
		return ast;
	}

	parseHeading(pState) {
		this.set("type", "heading");
		this.set("text", getVisibleTextTree(this.baseElement));
	}

	parseParHeading(pState) {
		this.set("type", "par-heading");
		this.set("text", getVisibleTextTree(this.baseElement));
	}

	parseBlock(pState) {
		this.set("type", "block");
		this.contentElement = this.baseElement.querySelector(
				":scope > div.embeddedContent > div > div.contentBlock");
		this.contentElement.querySelectorAll(":scope > *").forEach(item =>
				this.visitBlockListItem(pState, item));
	}

	getTextTree(a, indent="", skipFirstSpace=false) {
		let s = ["["];
		for (let t of a) {
			s.push(",\n  " + indent);
			if (Array.isArray(t))
				s.push(this.getTextTree(t, indent + "  ", true))
			else
				s.push("\"" + t + "\"");
		}
		s.push("\n" + indent + "]");

		s = s.join("");
		if (skipFirstSpace)
			s = s.replace("[,\n  " + indent, "[");
		s = s.replaceAll("[,", "[");
		if (skipFirstSpace && (a+"").length < 60) {
			s = s.replaceAll(",\n  " + indent, ", ");
			s = s.replaceAll("\n" + indent + "]", "]");
		}
		return s;
	}

	getJSON(indent="") {
		let s = [indent + "{\"type\": \"" + this.get("type") + "\""];

		for (const key in this.properties) {
			if (key == "type") continue;
			if (key == "text") continue;
			s.push(", \"" + key + "\": \"" + this.properties[key] + "\"");
		}

		if ("text" in this.properties) {
			s.push(", \"text\": ");
			s.push(this.getTextTree(this.properties["text"], indent));
		}

		if (this.children.length) {
			s.push(", \"children\": [");
			for (const i in this.children) {
				const child = this.children[i];
				s.push(i ? ",\n" : "\n");
				s.push(child.getJSON(indent + "  "));
			}
			s.push("\n" + indent + "]");
		}

		s.push("}");
		return s.join("");
	}
}

function risExtractor(parName) {
	let pState = { "parName": parName };
	let el = risContentBlocks[parName];
	let ast = new RisExAST(null, el);
	ast.set("parName", parName);
	ast.parseBlock(risExtractor.pState, 1);
	risExtractor.debugData = [ast, pState];
	return ast.getJSON();
}
