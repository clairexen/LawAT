/**
 * tocui – lightweight TOC widget with doc switching (classic scroll).
 *
 * API
 *   tocui.append(label [, targetId])
 *   tocui.reset()
 *   tocui.show()
 *   tocui.addDoc(title [, callback])
 *   tocui.setDoc(title)
 */

const tocui = (() => {
  let root, content, select;
  const docs = new Map(); // title → callback | null
  let currentDoc = '';

  /* -------------------------------- helpers ------------------------------ */
  function ensureRoot() {
    if (root) return;

    root = document.createElement('tocui');
    root.style.display = 'none';

    /* doc selector --------------------------------------------------------*/
    select = document.createElement('select');
    select.className = 'doc-select';
    root.appendChild(select);

    /* toc content ---------------------------------------------------------*/
    content = document.createElement('div');
    content.className = 'content';
    root.appendChild(content);

    document.body.appendChild(root);

    /* selector change -----------------------------------------------------*/
    select.addEventListener('change', () => {
      const chosen = select.value;
      // revert UI immediately
      select.value = currentDoc;
      const cb = docs.get(chosen);
      if (typeof cb === 'function') cb();
    });
  }

  /* -------------------------------- core API ---------------------------- */
  function reset() {
    if (!root) return;
    content.innerHTML = '';
    content.scrollTop = 0; // reset toc scroll
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' }); // reset main view
    root.style.display = 'none';
  }

  function append(domOrHtml, targetId) {
    ensureRoot();

    const entry = document.createElement('div');
    entry.className = 'entry';

    if (targetId) {
      /* clickable --------------------------------------------------------*/
      const link = document.createElement('a');
      link.href = `#${targetId}`;

      if (typeof domOrHtml === 'string') link.innerHTML = domOrHtml;
      else link.appendChild(domOrHtml);

      link.addEventListener('click', e => {
        /* ignore modified clicks ---------------------------------------*/
        if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

        const target = document.getElementById(targetId);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });

        /* update URL without reload ------------------------------------*/
        history.pushState(null, '', `#${targetId}`);

        e.preventDefault();
      });

      entry.appendChild(link);
    } else {
      /* non-clickable header -------------------------------------------*/
      entry.classList.add('header');
      if (typeof domOrHtml === 'string') entry.textContent = domOrHtml;
      else entry.appendChild(domOrHtml);
    }

    content.appendChild(entry);
  }

  function show() {
    ensureRoot();
    root.style.display = 'block';
  }

  function addDoc(title, callback) {
    ensureRoot();

    if (callback === undefined) {
      const hdr = document.createElement('option');
      hdr.textContent = `── ${title} ──`;
      hdr.disabled = true;
      select.appendChild(hdr);
      return;
    }

    docs.set(title, callback || null);
    const opt = document.createElement('option');
    opt.value = title;
    opt.textContent = title;
    select.appendChild(opt);
  }

  function setDoc(title) {
    if (!docs.has(title)) return;
    ensureRoot();
    currentDoc = title;
    select.value = title;
  }

  /* expose ---------------------------------------------------------------*/
  return { append, reset, show, addDoc, setDoc };
})();
