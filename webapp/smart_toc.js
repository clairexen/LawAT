/**
 * Classic smart_toc – minimal scrolling TOC widget.
 * API:
 *   smart_toc.append(label [, targetId])
 *   smart_toc.show()
 *   smart_toc.reset()
 */

const smart_toc = (() => {
  let root, content;

  function ensureRoot() {
    if (root) return;
    root = document.createElement('smart-toc');
    content = document.createElement('div');
    content.className = 'content';
    root.appendChild(content);
    document.body.appendChild(root);
  }

  /**
   * Clear all entries and hide the TOC – useful for re‑loading.
   */
  function reset() {
    if (!root) return;
    content.innerHTML = '';
    root.style.display = 'none';
  }

  /**
   * @param {string|Node} domOrHtml – Entry label or DOM node.
   * @param {string=} targetId      – Optional element id to scroll into view.
   */
  function append(domOrHtml, targetId) {
    ensureRoot();

    const entry = document.createElement('div');
    entry.className = 'entry';

    // If targetId given, wrap content in an <a> so it can be copied / opened.
    if (targetId) {
      const link = document.createElement('a');
      link.href = `#${targetId}`;

      if (typeof domOrHtml === 'string') link.innerHTML = domOrHtml;
      else link.appendChild(domOrHtml);

      link.addEventListener('click', e => {
        // Respect modifier clicks (new tab, copy link etc.)
        if (e.defaultPrevented ||
            e.button !== 0 ||
            e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) {
          return;
        }
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

  function show() {
    ensureRoot();
    root.style.display = 'block';
  }

  return { append, show, reset };
})();
