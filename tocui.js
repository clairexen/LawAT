/**
 * tocui – lightweight always-visible TOC widget (classic scroll).
 *
 * API
 *   tocui.append(label [, targetId [, callback]])
 *       – label (string|Node)  : visible text or DOM node
 *       – targetId (string|undef): element id for link; omit → header
 *       – callback (Function|undef): click handler; default navigation is
 *         suppressed for plain left-clicks (the handler can re‑enable via
 *         location.href if desired).
 *   tocui.reset()
 *   tocui.addDoc(title [, callback])
 *   tocui.setDoc(title)
 */

const tocui = (() => {
  let root, content, select;
  const docs = new Map();
  let currentDoc = '';

  /* ------------------------------ helpers ------------------------------ */
  function ensureRoot() {
    if (root) return;

    root = document.createElement('tocui');

    /* doc selector */
    select = document.createElement('select');
    select.className = 'doc-select';
    root.appendChild(select);

    /* toc content */
    content = document.createElement('div');
    content.className = 'content';
    root.appendChild(content);

    document.body.appendChild(root);

    select.addEventListener('change', () => {
      const chosen = select.value;
      select.value = currentDoc; // revert UI immediately
      const cb = docs.get(chosen);
      if (typeof cb === 'function') cb();
    });
  }

  /* --------------------------------- API ------------------------------ */
  function reset() {
    if (!root) return;
    content.innerHTML = '';
    content.scrollTop = 0;
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  }

  function append(domOrHtml, targetId, clickCb) {
    ensureRoot();

    const entry = document.createElement('div');
    entry.className = 'entry';

    if (targetId) {
      const link = document.createElement('a');
      link.href = `#${targetId}`;

      if (typeof domOrHtml === 'string') link.innerHTML = domOrHtml;
      else link.appendChild(domOrHtml);

      link.addEventListener('click', e => {
        // Call user handler first so it can optionally preventDefault.
        if (typeof clickCb === 'function') clickCb(e);

        // Suppress default nav for plain left-clicks unless handler already did.
        if (
          !e.defaultPrevented &&
          e.button === 0 &&
          !e.ctrlKey &&
          !e.metaKey &&
          !e.shiftKey &&
          !e.altKey
        ) {
          e.preventDefault();
        }
      });

      entry.appendChild(link);
    } else {
      entry.classList.add('header');
      if (typeof domOrHtml === 'string') entry.textContent = domOrHtml;
      else entry.appendChild(domOrHtml);
    }

    content.appendChild(entry);
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

  return { append, reset, addDoc, setDoc };
})();
