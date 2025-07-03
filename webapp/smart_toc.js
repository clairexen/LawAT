class SmartTOC extends HTMLElement {
  constructor() {
    super();
    this.viewportPadding = 10;
    this.deadZoneHeight = 20;
    this.expanded = false;
    this.deadZoneTop = null;

    this.container = document.createElement('div');
    this.container.classList.add('container');

    this.content = document.createElement('div');
    this.content.classList.add('content');

    const children = Array.from(this.children).filter(el => el.tagName === 'LI');
    children.forEach(li => {
      const entry = document.createElement('div');
      entry.className = 'entry';
      entry.textContent = li.textContent;
      this.content.appendChild(entry);
    });

    this.deadZoneBox = document.createElement('div');
    this.deadZoneBox.className = 'dead-zone';
    this.deadZoneBox.style.position = 'fixed';
    this.deadZoneBox.style.left = '0';
    this.deadZoneBox.style.width = '300px';
    this.deadZoneBox.style.height = `${this.deadZoneHeight}px`;
    this.deadZoneBox.style.background = 'rgba(0, 128, 255, 0.15)';
    this.deadZoneBox.style.pointerEvents = 'none';
    this.deadZoneBox.style.zIndex = '10000';
    this.deadZoneBox.style.display = 'none';
    document.body.appendChild(this.deadZoneBox);

    this.container.appendChild(this.content);
    this.innerHTML = ''; // Clear slotted content after extraction
    this.appendChild(this.container);

    this.addEventListener('mouseenter', this.handleMouseEnter.bind(this));
    this.addEventListener('mousemove', this.handleMouseMove.bind(this));
    document.addEventListener('mousemove', this.handleGlobalMouseMove.bind(this));
  }

  handleMouseEnter(e) {
    this.expand();
    this.deadZoneTop = this.clampDeadZoneTop(e.clientY - this.deadZoneHeight / 2);
    this.updateDeadZoneBox();
  }

  handleMouseMove(e) {
    const rect = this.getBoundingClientRect();
    const mouseY = e.clientY;
    const visibleHeight = rect.height;
    const contentHeight = this.content.scrollHeight;
    const maxScroll = contentHeight - visibleHeight;

    const dzBottom = this.deadZoneTop + this.deadZoneHeight;
    let outside = false;

    if (mouseY < this.deadZoneTop) {
      this.deadZoneTop = this.clampDeadZoneTop(mouseY);
      outside = true;
    } else if (mouseY > dzBottom) {
      this.deadZoneTop = this.clampDeadZoneTop(mouseY - this.deadZoneHeight);
      outside = true;
    }

    if (outside) {
      this.updateDeadZoneBox();

      const effectiveUsableHeight = visibleHeight - 2 * this.viewportPadding - this.deadZoneHeight;
      const clampedY = Math.max(this.viewportPadding, Math.min(mouseY, visibleHeight - this.viewportPadding));
      const scrollRatio = Math.max(0, Math.min(1,
        (clampedY - this.viewportPadding - this.deadZoneHeight / 2) / effectiveUsableHeight
      ));

      const targetTop = -scrollRatio * maxScroll;
      this.content.style.top = `${targetTop}px`;
    }
  }

  handleGlobalMouseMove(e) {
    if (e.clientX > 400) {
      this.collapse();
      if (!this.hasAttribute('show-box')) {
        this.deadZoneBox.style.display = 'none';
      }
    }
  }

  expand() {
    if (!this.expanded) {
      this.classList.add('expanded');
      this.expanded = true;
    }
  }

  collapse() {
    if (this.expanded) {
      this.classList.remove('expanded');
      this.expanded = false;
    }
  }

  clampDeadZoneTop(proposedTop) {
    const maxTop = window.innerHeight - this.viewportPadding - this.deadZoneHeight;
    const minTop = this.viewportPadding;
    return Math.min(maxTop, Math.max(minTop, proposedTop));
  }

  updateDeadZoneBox() {
    this.deadZoneBox.style.top = `${this.deadZoneTop}px`;
    this.deadZoneBox.style.height = `${this.deadZoneHeight}px`;
    if (this.hasAttribute('show-box')) {
      this.deadZoneBox.style.display = 'block';
    }
  }
}

customElements.define('smart-toc', SmartTOC);
