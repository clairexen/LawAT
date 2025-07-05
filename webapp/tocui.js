/**
 * tocui – classic scroll‑based TOC widget with document switching.
 *
 * API:
 *   tocui.append(label [, targetId])
 *   tocui.reset()
 *   tocui.show()
 *   tocui.addDoc(title [, callback])
 *   tocui.setDoc(title)
 */

const tocui = (() => {
  let root, content, select;
  const docs = new Map();          // title → callback (null if header)
  let currentDoc = '';

  /* ------------------------------------------------------------ */
  function ensureRoot() {
    if (root) return;

    root = document.createElement('tocui');
    root.style.display = 'none';

    // drop‑down for docs
    select = document.createElement('select');
    select.className = 'doc-select';
    root.appendChild(select);

    content = document.createElement('div');
    content.className = 'content';
    root.appendChild(content);

    document.body.appendChild(root);

    select.addEventListener('change', () => {
      const newTitle = select.value;
      // Immediately revert UI
      select.value = currentDoc;
      const cb = docs.get(newTitle);
      if (typeof cb === 'function') cb();
    });
  }

  /* ------------------------------------------------------------ */
  function reset() {
    if (!root) return;
    content.innerHTML = '';
    root.style.display = 'none';
  }

  /* ------------------------------------------------------------ */
  function append(domOrHtml, targetId) {
    ensureRoot();

    const entry = document.createElement('div');
    entry.className = 'entry';

    if (targetId) {
      const link = document.createElement('a');
      link.href = `#${targetId}`;
      if (typeof domOrHtml === 'string') link.innerHTML = domOrHtml;
      else link.appendChild(domOrHtml);

      link.addEventListener('click', e => {
        if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
        const target = document.getElementById(targetId);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        e.preventDefault();
      });
      entry.appendChild(link);
    } else {
      if (typeof domOrHtml === 'string') entry.innerHTML = domOrHtml;
      else entry.appendChild(domOrHtml);
    }

    content.appendChild(entry);
  }

  /* ------------------------------------------------------------ */
  function show() {
    ensureRoot();
    root.style.display = 'block';
  }

  /* ------------------------------------------------------------ */
  function addDoc(title, callback) {
    ensureRoot();

    if (callback === undefined) {
      // Header entry – disabled option acts as section marker
      const hdr = document.createElement('option');
      hdr.textContent = `── ${title} ──`;
      hdr.disabled = true;
      hdr.className = 'doc-header';
      select.appendChild(hdr);
      return;
    }

    docs.set(title, callback || null);
    const opt = document.createElement('option');
    opt.value = title;
    opt.textContent = title;
    select.appendChild(opt);
  }

  /* ------------------------------------------------------------ */
  function setDoc(title) {
    if (!docs.has(title)) return;
    ensureRoot();
    currentDoc = title;
    select.value = title;
  }

  /* ------------------------------------------------------------ */
  return { append, reset, show, addDoc, setDoc };
})();
