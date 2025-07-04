const smart_toc = (() => {
  let root, container, content, box;
  let isExpanded = false, shownOnce = false, mouseInside = false;

  // -----------------------------------------------------------------------
  // configuration
  // -----------------------------------------------------------------------
  const cfg = {
    boxWidth: 20,
    boxHeight: 30,
    viewportPadding: 30,
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

  function innerHeight() {
    // return root.getBoundingClientRect().height;
    return window.innerHeight;
  }

  function clamp(pos) {
    return Math.min(innerHeight() - cfg.viewportPadding - cfg.boxHeight / 2,
                    Math.max(cfg.viewportPadding + cfg.boxHeight / 2, pos));
  }

  function updateTargetAndSpeed()
  {
    currentCenter = clamp(currentCenter);
    targetCenter = lastMouseY;
    currentSpeed = targetCenter - currentCenter;
    if (lastMouseX < cfg.boxWidth) return;
    if (Math.abs(currentSpeed) < cfg.boxHeight / 2) {
      targetCenter = currentCenter;
      currentSpeed = 0;
    } else {
      targetCenter -= Math.sign(currentSpeed) * cfg.boxHeight / 2;
      const diff = targetCenter - currentCenter;
      const dist = Math.min(1.0, Math.abs(diff) / cfg.boxHeight);
      const scale = Math.pow(Math.min(1, Math.max(0, 1.0 - lastMouseX / 100)), cfg.speedExponent);
      currentSpeed = Math.sign(diff) * dist * scale * cfg.speedFactor;
    }
  }

  function animate() {
    animId = null;
    updateTargetAndSpeed();
    currentCenter = clamp(currentCenter + currentSpeed);

    box.style.top    = `${currentCenter - cfg.boxHeight/2}px`;
    box.style.height = `${cfg.boxHeight}px`;
    if (cfg.boxWidth) {
      if (isExpanded) {
        box.style.display = 'block';
        // box.style.width = '300px';
      } else {
        // box.style.display = 'none';
        box.style.width = `${cfg.boxWidth}px`;
      }
    }

    const visibleHeight = root.getBoundingClientRect().height;
    const minCenter = cfg.viewportPadding + cfg.boxHeight/2;
    const maxCenter = innerHeight() - cfg.viewportPadding - cfg.boxHeight/2;
    const ratio = (currentCenter - minCenter) / (maxCenter - minCenter); // 0..1

    const contentHeight = content.scrollHeight;
    const maxScroll = Math.max(100, contentHeight - visibleHeight);
    const scroll = -maxScroll * Math.max(0, Math.min(1, ratio));
    content.style.top = `${scroll}px`;

    if (Math.abs(targetCenter - currentCenter) > 0.1 && isExpanded)
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
      width: `${cfg.boxWidth}px`,
      height: `${cfg.boxHeight}px`,
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
