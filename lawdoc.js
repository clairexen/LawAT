const lawdoc = (() => {
	// -----------------------------------------------------------------------
	// load dataset
	// -----------------------------------------------------------------------
	let zip, zipPromise = fetch('webapp.json') .then(res => res.json())
			.then(json => { zip = json; lawdoc.zip = json; });

	// -----------------------------------------------------------------------
	// API
	// -----------------------------------------------------------------------
	function onLoad(callback) {
		zipPromise.then(callback);
	}

	function render(markup) {
		let refSuffix = "";
		let metaData = {};

		function worker(markup) {
			// -----------------------------------------------------------------------
			// content handling

			if (typeof markup === "string") {
				// let el = document.createElement('SPAN');
				// el.innerText = markup;
				let el = document.createTextNode(markup);
				return el;
			}

			const head = markup[0].trim().split(/\s+/), tail = markup.slice(1),
					infoStr = markup[0].replace(/^\s*\S+\s*/, ''),
					tag = head[0], info = head.slice(1);

			if (tag == "Meta") {
				metaData[markup[0].replace(/^Meta /, '')] = markup.slice(1);
				if (markup[0] == "Meta PartAnchors")
					markup = [markup[0] + " ..."];
				return document.createComment('LawDoc'+markup.join('\n')+' ');
			}

			function removePrefix(str, prefix) {
				return str.startsWith(prefix) ? str.slice(prefix.length) : str;
			}

			function genElement(htmlTag, lawDocTag=null) {
				if (lawDocTag === null) lawDocTag = tag;
				let el = document.createElement(htmlTag);
				if (lawDocTag == "LawDoc" || lawDocTag == "PartName" ||
						lawDocTag == "PartBody")
					el.classList.add(lawDocTag);
				else if (lawDocTag == "Part" || lawDocTag == "Text" ||
						lawDocTag == "Err" || lawDocTag == "Src" ||
						lawDocTag == "RS")
					el.classList.add("Law" + lawDocTag);
				// el.classList.add("_" + lawDocTag);
				return el;
			}

			if (tag == "Rem") {
				let el = genElement('I');
				tail.forEach(item => { el.appendChild(worker(item)); });
				return el;
			}

			if (tag == "Head" || tag == "Title" || tag == "Text") {
				let el = genElement(tag == "Head" ? 'H2' : tag == "Title" ? 'H3' : 'DIV');
				info.forEach(item => { el.classList.add(item); });
				tail.forEach(item => { el.appendChild(worker(item)); });
				return el;
			}

			if (tag == "Break") {
				return genElement('P');
			}

			// -----------------------------------------------------------------------
			// structure handling

			if (tag == "LawDoc") {
				let el = genElement('DIV');

				tail.forEach(item => {
					if (/^Meta /.test(item[0]))
						el.appendChild(worker(item));
				});

				refSuffix = infoStr.replace(/^[A-Z]+\./, '')
				let h1 = genElement('H1', tag + 'Title');
				h1.appendChild(document.createTextNode(metaData["Langtitel"][0] +
						"; i.d.F.v. " + metaData["FassungVom"][0]));
				el.appendChild(h1);

				let risLink = metaData["RisSrcLink"];
				let mdLink = `https://github.com/clairexen/LawAT/blob/main/files/${infoStr}.md`;
				let muLink = `https://github.com/clairexen/LawAT/blob/main/files/${infoStr}.markup.json`;

				let srcDiv = genElement('DIV', 'Src');
				srcDiv.innerHTML += `<b>LawAT GitHub Markdown:</b> <a href="${mdLink}" target="_blank">${mdLink}</a><br/>`;
				srcDiv.innerHTML += `<b>LawAT "LawDoc" Markup:</b> <a href="${muLink}" target="_blank">${muLink}</a><br/>`;
				srcDiv.innerHTML += `<b>RIS Quell-Dokument:</b> <a href="${risLink}" target="_blank">${risLink}</a>`;
				el.appendChild(srcDiv);

				tail.forEach(item => {
					if (/^Meta /.test(item[0]))
						return;
					el.appendChild(worker(item));
				});

				return el;
			}

			if (tag == "Part") {
				let el = genElement('DIV'), body = el;
				let sp = genElement('SPAN', tag + 'Name');
				sp.setAttribute('id', getIdForPartRef(infoStr + " " + refSuffix) + "_");
				sp.innerText = infoStr;
				tail.forEach(item => {
					if (body.children.length)
						body.appendChild(document.createTextNode("\n"));
					let c = worker(item);
					if (c.tagName != 'H2' && sp) {
						body = genElement('DIV', 'PartBody');
						el.appendChild(body);
						if (c.tagName == 'H3' && sp) {
							c.prepend(document.createTextNode(" "));
							c.prepend(sp);
						} else {
							let h3 = genElement('H3', tag + 'Title');
							h3.appendChild(sp);
							body.appendChild(h3);
						}
						sp = null;
					}
					body.appendChild(c);
				});
				if (refSuffix in zip["rsdata.json"]["index"]) {
					let key = infoStr + " " + refSuffix;
					let idPrefix = getIdForPartRef(key);
					if (key in zip["rsdata.json"]["index"][refSuffix]) {
						let rslist = zip["rsdata.json"]["index"][refSuffix][key];
						rslistCache[idPrefix] = rslist;

						let c = genElement('DIV', 'RS');
						c.setAttribute('id', `${idPrefix}_RS`);
						body.appendChild(c);
						body.appendChild(genElement('P'));

						c = genElement('A', 'RS');
						if (rslist.length > 1)
							c.text = `(+) ${rslist.length} Rechtssätze zu dieser Bestimmung anzeigen`;
						else
							c.text = `(+) ${rslist.length} Rechtssatz zu dieser Bestimmung anzeigen`;
						c.setAttribute('href', `javascript:showRS('${idPrefix}')`);
						c.setAttribute('id', `${idPrefix}_showRS`);
						c.style.display = 'block';
						body.appendChild(c);

						c = genElement('A', 'RS');
						if (rslist.length > 1)
							c.text = `(-) ${rslist.length} Rechtssätze zu dieser Bestimmung ausblenden`;
						else
							c.text = `(-) ${rslist.length} Rechtssatz zu dieser Bestimmung ausblenden`;
						c.setAttribute('href', `javascript:hideRS('${idPrefix}')`);
						c.setAttribute('id', `${idPrefix}_hideRS`);
						c.style.display = 'none';
						body.appendChild(c);
					}
				}
				return el;
			}

			if (tag == "Item") {
				let el = genElement('DD');
				let dt = genElement('DT', tag + 'Name');
				dt.innerText = infoStr;
				el.appendChild(dt);
				tail.forEach(item => {
					if (el.children.length)
						el.appendChild(document.createTextNode("\n"));
					el.appendChild(worker(item));
				});
				return el;
			}

			if (tag == "List") {
				let el = genElement('DL');
				info.forEach(item => { el.classList.add(item); });
				tail.forEach(item => {
					if (el.children.length)
						el.appendChild(document.createTextNode("\n"));
					c = worker(item);
					if (item[0] == 'Rem') {
						let dt = genElement('DT');
						dt.innerHTML = "—";
						el.appendChild(dt);
						let dd = genElement('DD');
						dd.appendChild(c);
						el.appendChild(dd);
					} else {
						if (c.firstElementChild.tagName == 'DT')
							el.appendChild(c.firstElementChild);
						el.appendChild(c);
					}
				});
				return el;
			}

			let el = genElement('TT', 'Err');
			el.innerText = JSON.stringify(markup);
			return el;
		}

		return worker(markup);
	}

	function getIdForPartRef(ref) {
		let a = [];
		for (tok of ref.split(/\s+/)) {
			if (tok == "§" || tok == "Art.") continue;
			a.push(tok);
		}
		return a.slice(-1).concat(a.slice(0,-1)).join(".");
	}

	// -----------------------------------------------------------------------
	return { zip, onLoad, render, getIdForPartRef };
})();
