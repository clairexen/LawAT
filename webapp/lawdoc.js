const lawdoc = (() => {
	// -----------------------------------------------------------------------
	// load dataset
	// -----------------------------------------------------------------------
	let zip, zipPromise = fetch('RisExData.json') .then(res => res.json())
			.then(json => { zip = json; lawdoc.zip = json; });

	// -----------------------------------------------------------------------
	// API
	// -----------------------------------------------------------------------
	function onLoad(callback) {
		zipPromise.then(callback);
	}

	function render(markup) {
		// -----------------------------------------------------------------------
		// content handling

		if (typeof markup === "string") {
			let el = document.createElement('SPAN');
			el.classList.add('LawSpan');
			el.innerText = markup;
			return el;
		}

		const head = markup[0].trim().split(/\s+/), tail = markup.slice(1),
				infoStr = markup[0].replace(/^\s*\S+\s*/, ''),
				tag = head[0], info = head.slice(1);

		if (tag == "Meta") {
			if (markup[0] == "Meta ParAnchors")
				markup = [markup[0] + " ..."];
			return document.createComment('LawDoc'+markup.join('\n')+' ');
		}

		function removePrefix(str, prefix) {
			return str.startsWith(prefix) ? str.slice(prefix.length) : str;
		}

		function genElement(htmlTag, lawDocTag=null) {
			let el = document.createElement(htmlTag);
			el.classList.add('Law' + removePrefix(lawDocTag === null ? tag : lawDocTag, "Law"));
			return el;
		}

		if (tag == "Anm") {
			let el = genElement('I');
			tail.forEach(item => { el.appendChild(render(item)); });
			return el;
		}

		if (tag == "Head" || tag == "Title" || tag == "Text") {
			let el = genElement(tag == "Head" ? 'H2' : tag == "Title" ? 'H3' : 'DIV');
			info.forEach(item => { el.classList.add('Law' + item); });
			tail.forEach(item => { el.appendChild(render(item)); });
			return el;
		}

		if (tag == "Break") {
			return genElement('P');
		}

		// -----------------------------------------------------------------------
		// structure handling

		if (tag == "LawDoc" || tag == "Par" || tag == "Item") {
			let el = genElement(tag == "Item" ? 'DD' : 'DIV'), sp;
			if (tag == "Item") {
				dt = genElement('DT', tag + 'Name');
				dt.innerText = infoStr;
				el.appendChild(dt);
			} else {
				sp = genElement('SPAN', tag + 'Name');
				sp.innerText = infoStr;
				el.appendChild(sp);
			}
			if (tag == "LawDoc") {
				let h1 = genElement('H1', tag + 'Title');
				h1.appendChild(sp);
				h1.appendChild(document.createTextNode(": " + markup[1][1]));
				el.appendChild(h1);
				sp = null;
			}
			tail.forEach(item => {
				if (el.children.length)
					el.appendChild(document.createTextNode("\n"));
				c = render(item);
				if (c.tagName == 'H3' && sp) {
					c.prepend(document.createTextNode(" "));
					c.prepend(sp);
					sp = null;
				} else
				if (c.tagName != 'H2' && sp) {
					let h3 = genElement('H3', tag + 'Title');
					h3.appendChild(sp);
					el.appendChild(h3);
					sp = null;
				}
				el.appendChild(c);
			});
			return el;
		}

		if (tag == "List") {
			let el = genElement('DL');
			info.forEach(item => { el.classList.add('Law' + item); });
			tail.forEach(item => {
				if (el.children.length)
					el.appendChild(document.createTextNode("\n"));
				c = render(item);
				if (c.firstElementChild.tagName == 'DT')
					el.appendChild(c.firstElementChild);
				el.appendChild(c);
			});
			return el;
		}

		let el = genElement('TT', 'Err');
		el.innerText = JSON.stringify(markup);
		return el;
	}

	// -----------------------------------------------------------------------
	return { zip, onLoad, render };
})();
