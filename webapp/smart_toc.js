const smart_toc = (() => {
  let root = null;
  let container = null;
  let content = null;
  let box = null;
  let isExpanded = false;
  let shownOnce = false;
  let mouseInside = false;
  let cfg = {
    showBox: false,
    viewportPadding: 30,
    deadZoneHeight: 30
  };
  let deadZoneTop = 0;

  function setup(userCfg = {}) {
    cfg = { ...cfg, ...userCfg };
    reset();
  }

  function reset() {
    if (root) root.remove();
    if (box) box.remove();

    root = document.createElement('smart-toc');
    container = document.createElement('div');
    container.className = 'container';
    container.style.display = 'none';

    content = document.createElement('div');
    content.className = 'content';

    container.appendChild(content);
    root.appendChild(container);
    document.body.appendChild(root);

    box = document.createElement('div');
    Object.assign(box.style, {
      position: 'fixed',
      left: '0',
      width: '300px',
      height: `${cfg.deadZoneHeight}px`,
      background: 'rgba(0, 128, 255, 0.15)',
      pointerEvents: 'none',
      zIndex: '10000',
      display: 'none'
    });
    document.body.appendChild(box);

    root.addEventListener('mouseenter', e => {
      mouseInside = true;
      expand();
      deadZoneTop = clamp(e.clientY - cfg.deadZoneHeight / 2);
      updateBox();
    });

    root.addEventListener('mouseleave', () => {
      mouseInside = false;
      collapse();
    });

    root.addEventListener('mousemove', e => {
      const rect = root.getBoundingClientRect();
      const mouseY = e.clientY;
      const visibleHeight = rect.height;
      const contentHeight = content.scrollHeight;
      const maxScroll = contentHeight - visibleHeight;

      let dzBottom = deadZoneTop + cfg.deadZoneHeight;
      let outside = false;

      if (mouseY < deadZoneTop) {
        deadZoneTop = clamp(mouseY);
        outside = true;
      } else if (mouseY > dzBottom) {
        deadZoneTop = clamp(mouseY - cfg.deadZoneHeight);
        outside = true;
      }

      if (outside) {
        updateBox();
        const usable = visibleHeight - 2 * cfg.viewportPadding - cfg.deadZoneHeight;
        const clampedY = Math.max(cfg.viewportPadding, Math.min(mouseY, visibleHeight - cfg.viewportPadding));
        const ratio = (clampedY - cfg.viewportPadding - cfg.deadZoneHeight / 2) / usable;
        const scroll = -Math.max(0, Math.min(1, ratio)) * maxScroll;
        content.style.top = `${scroll}px`;
      }
    });

    document.addEventListener('mousemove', e => {
      if (e.clientX > 400) collapse();
    });
  }

  function append(domOrHtml) {
    const entry = document.createElement('div');
    entry.className = 'entry';
    if (typeof domOrHtml === 'string') entry.innerHTML = domOrHtml;
    else entry.appendChild(domOrHtml);
    content.appendChild(entry);
    container.style.display = 'block';
  }

  function updateBox() {
    box.style.top = `${deadZoneTop}px`;
    box.style.height = `${cfg.deadZoneHeight}px`;
  }

  function clamp(pos) {
    return Math.min(window.innerHeight - cfg.viewportPadding - cfg.deadZoneHeight, Math.max(cfg.viewportPadding, pos));
  }

  function expand() {
    if (!isExpanded) {
      root.classList.add('expanded');
      if (cfg.showBox) box.style.display = 'block';
      isExpanded = true;
    }
  }

  function collapse() {
    if (isExpanded) {
      root.classList.remove('expanded');
      box.style.display = 'none';
      isExpanded = false;
    }
  }

  function show() {
    if (shownOnce) return;
    shownOnce = true;
    container.style.display = 'block';
    expand();
    setTimeout(() => {
      if (!mouseInside) collapse();
    }, 1000);
  }

  return { setup, append, reset, show };
})();
