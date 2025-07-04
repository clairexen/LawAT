const smart_toc = (() => {
  let root, container, content, box;
  let isExpanded = false, shownOnce = false, mouseInside = false;

  // -----------------------------------------------------------------------
  // configuration
  // -----------------------------------------------------------------------
  const cfg = {
    showBox: true, // draw blue helper box
    viewportPadding: 30,
    deadZoneHeight: 30,
    speedExponent: 2.0,
    speedFactor: 3 // px per frame
  };

  // -----------------------------------------------------------------------
  // animation state
  // -----------------------------------------------------------------------
  let currentTop   = 0;          // current top of the box (px)
  let targetTop    = 0;          // desired top of the box (px)
  let currentSpeed = 0;
  let animId       = null;
  let lastMouseY   = 0;          // latest Y position of the pointer

  // -----------------------------------------------------------------------
  // public API
  // -----------------------------------------------------------------------
  function setup(userCfg = {}) {
    Object.assign(cfg, userCfg);
    reset();
  }

  function append(domOrHtml) {
    const entry = document.createElement('div');
    entry.className = 'entry';
    if (typeof domOrHtml === 'string') entry.innerHTML = domOrHtml;
    else entry.appendChild(domOrHtml);
    content.appendChild(entry);
    container.style.display = 'block';
  }

  // -----------------------------------------------------------------------
  // init / teardown
  // -----------------------------------------------------------------------
  function reset() {
    if (root) root.remove();
    if (box)  box.remove();
    if (animId) cancelAnimationFrame(animId);

    currentTop = cfg.viewportPadding;

    // ------- root & container -------------------------------------------
    root = document.createElement('smart-toc');
    container = document.createElement('div');
    container.className = 'container';
    container.style.display = 'none';

    content = document.createElement('div');
    content.className = 'content';

    container.appendChild(content);
    root.appendChild(container);
    document.body.appendChild(root);

    // ------- helper box --------------------------------------------------
    box = document.createElement('div');
    Object.assign(box.style, {
      position: 'fixed',
      left: '0',
      width: '100px',
      height: `${cfg.deadZoneHeight}px`,
      background: 'rgba(0,128,255,0.15)',
      pointerEvents: 'none',
      zIndex: '10000',
      display: 'none'
    });
    document.body.appendChild(box);

    // ------- pointer interaction ----------------------------------------
    root.addEventListener('mouseenter', e => {
      mouseInside = true;
      lastMouseY  = e.clientY;
      expand();
      targetTop   = clamp(e.clientY - cfg.deadZoneHeight / 2);
      ensureAnimLoop();
    });

    root.addEventListener('mouseleave', () => {
      mouseInside = false;
      collapse();
    });

    root.addEventListener('mousemove', e => {
      lastMouseY = e.clientY;

      // update target once the pointer leaves the current box bounds
      if (e.clientY < currentTop || e.clientY > currentTop + cfg.deadZoneHeight) {
        targetTop = clamp(e.clientY - cfg.deadZoneHeight / 2);
      }

      // horizontal position → speed (non‑linear mapping)
      currentSpeed = speedFromMouseX(e.clientX);
      ensureAnimLoop();
    });

    // collapse when pointer far right of page
    document.addEventListener('mousemove', e => {
      if (e.clientX > 400) collapse();
    });
  }

  // -----------------------------------------------------------------------
  // animation helpers
  // -----------------------------------------------------------------------
  function ensureAnimLoop() {
    if (!isExpanded) return;
    if (!animId) animId = requestAnimationFrame(animateBox);
  }

  function animateBox() {
    // stop moving once the cursor is within the box bounds
    if (lastMouseY >= currentTop && lastMouseY <= currentTop + cfg.deadZoneHeight) {
      targetTop = currentTop;
      updateBox();
      animId = null;
      return;
    }

    const diff      = targetTop - currentTop;
    const distance  = Math.abs(diff);

    if (distance < 0.2) {
      currentTop = targetTop;
      updateBox();
      animId = null;
      return;
    }

    // soft‑landing: within one dead‑zone height, fade speed from 1.0 → 0.1
    let stepSpeed = currentSpeed;
    if (distance < cfg.deadZoneHeight) {
      const ratio = distance / cfg.deadZoneHeight;   // 0…1
      stepSpeed  *= 0.1 + 0.9 * ratio;               // 0.1…1.0
    }

    currentTop += Math.sign(diff) * Math.min(stepSpeed, distance);
    updateBox();
    animId = requestAnimationFrame(animateBox);
  }

  function speedFromMouseX(x) {
    const scale = Math.pow(Math.min(1, Math.max(0, 1.0 - x / 100)), cfg.speedExponent);
    return scale * cfg.speedFactor;
  }

  // -----------------------------------------------------------------------
  // visual helpers (box + scrolling)
  // -----------------------------------------------------------------------
  function updateBox() {
    box.style.top    = `${currentTop}px`;
    box.style.height = `${cfg.deadZoneHeight}px`;
    if (cfg.showBox) {
      if (isExpanded) {
        box.style.display = 'block';
        box.style.width = '300px';
      } else {
        // box.style.display = 'none';
        box.style.width = '10px';
      }
    }
    updateScroll();
  }

  function updateScroll() {
    if (!isExpanded) return;
    const rect          = root.getBoundingClientRect();
    const visibleHeight = rect.height;
    const contentHeight = content.scrollHeight;
    const maxScroll     = contentHeight - visibleHeight;

    const centerY = currentTop + cfg.deadZoneHeight / 2;
    const usable  = visibleHeight - 2 * cfg.viewportPadding - cfg.deadZoneHeight;
    const clamped = Math.max(cfg.viewportPadding, Math.min(centerY, visibleHeight - cfg.viewportPadding));
    const ratio   = (clamped - cfg.viewportPadding - cfg.deadZoneHeight / 2) / usable;
    const scroll  = -Math.max(0, Math.min(1, ratio)) * maxScroll;
    content.style.top = `${scroll}px`;
  }

  function clamp(pos) {
    return Math.min(window.innerHeight - cfg.viewportPadding - cfg.deadZoneHeight,
                    Math.max(cfg.viewportPadding, pos));
  }

  // -----------------------------------------------------------------------
  // expansion / collapse helpers
  // -----------------------------------------------------------------------
  function expand() {
    if (!isExpanded) {
      root.classList.add('expanded');
      isExpanded = true;
      updateBox();
    }
  }

  function collapse() {
    if (isExpanded) {
      root.classList.remove('expanded');
      isExpanded = false;
      if (animId) { cancelAnimationFrame(animId); animId = null; }
      updateBox();
    }
  }

  function show() {
    if (shownOnce) return;
    shownOnce = true;
    container.style.display = 'block';
    expand();
    setTimeout(() => { if (!mouseInside) collapse(); }, 1000);
  }

  // -----------------------------------------------------------------------
  return { setup, append, reset, show };
})();
