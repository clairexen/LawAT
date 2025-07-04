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
    speedExponent: 3.0,
    speedFactor: 5 // px per frame
  };

  // -----------------------------------------------------------------------
  // animation state
  // -----------------------------------------------------------------------
  let lastMouseX    = 0;          // latest X position of the pointer
  let lastMouseY    = 0;          // latest Y position of the pointer
  let currentCenter = 0;          // current vertical center of the box (px)
  let targetCenter  = 0;          // desired vertical center of the box (px)
  let currentSpeed  = 0;
  let animId        = null;

  function clamp(pos) {
    return Math.min(window.innerHeight - cfg.viewportPadding - cfg.deadZoneHeight / 2,
                    Math.max(cfg.viewportPadding + cfg.deadZoneHeight / 2, pos));
  }

  function updateTargetAndSpeed()
  {
    currentCenter = clamp(currentCenter);
    targetCenter = clamp(lastMouseY);
    const delta = targetCenter - currentCenter;
    if (Math.abs(delta) < cfg.deadZoneHeight / 2) {
      targetCenter = currentCenter;
      currentSpeed = 0;
    } else {
      targetCenter -= Math.sign(delta) * cfg.deadZoneHeight / 2;
      const diff = targetCenter - currentCenter;
      const dist = Math.min(1.0, Math.abs(diff) / cfg.deadZoneHeight);
      const scale = Math.pow(Math.min(1, Math.max(0, 1.0 - lastMouseX / 100)), cfg.speedExponent);
      currentSpeed = Math.sign(diff) * dist * scale * cfg.speedFactor;
      if (Math.abs(currentSpeed) > Math.abs(diff)) currentSpeed = diff;
    }
  }

  function animate() {
    animId = null;
    updateTargetAndSpeed();
    currentCenter += currentSpeed;
    if (Math.abs(targetCenter - currentCenter) < 0.1) return;

    box.style.top    = `${currentCenter - cfg.deadZoneHeight/2}px`;
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

    const rect          = root.getBoundingClientRect();
    const visibleHeight = rect.height;
    const contentHeight = content.scrollHeight;
    const maxScroll     = Math.max(100, contentHeight - visibleHeight);
    const ratio = (currentCenter - cfg.deadZoneHeight/2 - cfg.viewportPadding) /
                         (visibleHeight - cfg.deadZoneHeight - 2*cfg.viewportPadding);  // 0..1
    const scroll = -maxScroll * Math.max(0, Math.min(1, ratio));
    content.style.top = `${scroll}px`;

    if (isExpanded)
      animId = requestAnimationFrame(animate);
  }

  function go() {
    if (!animId) animId = requestAnimationFrame(animate);
  }

  function expand() {
    if (!isExpanded) {
      root.classList.add('expanded');
      isExpanded = true;
      go();
    }
  }

  function collapse() {
    if (isExpanded) {
      root.classList.remove('expanded');
      isExpanded = false;
      go();
    }
  }

  // -----------------------------------------------------------------------
  // public API
  // -----------------------------------------------------------------------
  function setup(userCfg = {}) {
    Object.assign(cfg, userCfg);
    reset();
  }

  function reset() {
    if (root) root.remove();
    if (box)  box.remove();
    if (animId) cancelAnimationFrame(animId);

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
      lastMouseX  = e.clientX;
      lastMouseY  = e.clientY;
      updateTargetAndSpeed();
      expand();
      go();
    });

    root.addEventListener('mouseleave', () => {
      mouseInside = false;
      // collapse();
    });

    root.addEventListener('mousemove', e => {
      lastMouseX = e.clientX;
      lastMouseY = e.clientY;
      updateTargetAndSpeed();
      go();
    });

    // collapse when pointer far right of page
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

  function show() {
    if (shownOnce) return;
    shownOnce = true;
    container.style.display = 'block';
    expand();
    setTimeout(() => { if (!mouseInside) collapse(); }, 1000);
  }

  // -----------------------------------------------------------------------
  return { setup, reset, append, show };
})();
