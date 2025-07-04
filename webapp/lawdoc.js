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
		// string/text handling

		if (typeof markup === "string") {
			let el = document.createElement('SPAN');
			el.classList.add('LawDoc');
			el.classList.add('LawDocSpan');
			el.innerText = markup;
			return el;
		}

		const head = markup[0].trim().split(/\s+/), tail = markup.slice(1),
				infoStr = markup[0].replace(/^\s*\S+\s*/, ''),
				tag = head[0], info = head.slice(1);

		function genElement(htmlTag, lawDocTag=null) {
			let el = document.createElement(htmlTag);
			el.classList.add('LawDoc');
			el.classList.add('LawDoc' + (lawDocTag === null ? tag : lawDocTag));
			return el;
		}

		if (tag == "Anm") {
			let el = genElement('I');
			tail.forEach(item => { el.appendChild(render(item)); });
			return el;
		}

		if (tag == "Head" || tag == "Title" || tag == "Text") {
			let el = genElement(tag == "Head" ? 'H2' : tag == "Title" ? 'H3' : 'DIV');
			info.forEach(item => { el.classList.add('LawDoc' + item); });
			tail.forEach(item => { el.appendChild(render(item)); });
			return el;
		}

		// -----------------------------------------------------------------------
		// structure handling

		if (tag == "Par" || tag == "Item") {
			let el = genElement(tag == "Item" ? 'DD' : 'DIV'), sp;
			if (tag == "Par") {
				sp = genElement('SPAN', tag + 'Name');
				sp.innerText = infoStr;
				el.appendChild(sp);
			} else {
				dt = genElement('DT', tag + 'Name');
				dt.innerText = infoStr;
				el.appendChild(dt);
			}
			tail.forEach(item => {
				c = render(item);
				if (c.tagName == 'H3') {
					sp.innerText = sp.innerText + " ";
					c.prepend(sp);
				}
				el.appendChild(c);
			});
			return el;
		}

		if (tag == "List") {
			let el = genElement('DL');
			info.forEach(item => { el.classList.add('LawDoc' + item); });
			tail.forEach(item => {
				c = render(item);
				if (c.firstElementChild.tagName == 'DT')
					el.appendChild(c.firstElementChild);
				el.appendChild(c);
			});
			return el;
		}

		let el = genElement('TT');
		el.innerText = JSON.stringify(markup);
		return el;
	}

	// -----------------------------------------------------------------------
	return { zip, onLoad, render };
})();
