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

class RisExAST {
	constructor(baseEl, bodyEl) {
		this.baseElement = baseEl;
		this.bodyElement = bodyEl;
		this.properties = {};
		this.children = [];
	}

	set(key, value) {
		this.properties[key] = value;
	}

	addChild(child) {
		this.children.push(child);
		return child;
	}
}

function runRisExtractor(blkIndex) {
	blk = document.querySelector("div.document > div.documentContent:nth-of-type("+blkIndex+")");
	blkId = blk.querySelector(":scope > div.embeddedContent").getAttribute("id");
	blkBody = blk.querySelector(":scope > div.embeddedContent > div > div.contentBlock");
	ast = new RisExAST(blk, blkBody);

	items = blkBody.querySelectorAll(":scope > *")
	for (let i = 0; i < items.length; i++) {
		child = ast.addChild(new RisExAST(items[i], items[i]));
	}

	return ast;
}
