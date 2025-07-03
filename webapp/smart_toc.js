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

    for (let i = 1; i <= 200; i++) {
      const entry = document.createElement('div');
      entry.className = 'entry';
      entry.textContent = `Chapter ${i}`;
      this.content.appendChild(entry);
    }

    this.deadZoneBox = document.createElement('div');
    this.deadZoneBox.className = 'dead-zone';
    document.body.appendChild(this.deadZoneBox);

    this.container.appendChild(this.content);
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
      this.deadZoneBox.style.display = 'none';
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
    this.deadZoneBox.style.display = 'block';
    this.deadZoneBox.style.top = `${this.deadZoneTop}px`;
    this.deadZoneBox.style.height = `${this.deadZoneHeight}px`;
  }
}

customElements.define('smart-toc', SmartTOC);
