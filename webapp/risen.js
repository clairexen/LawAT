/**
 * risen.js – RisEnQuery MicroPython Shell helper
 * Loads PyScript lazily when risen.open() is first called.
 */
(function (global) {
  const risen = {};
  let initialized = false;
  let pyLoaded = false;
  let pyLoading = null; // Promise

  const PYSCRIPT_VER = '2025.5.1';
  const CORE_JS = `https://pyscript.net/releases/${PYSCRIPT_VER}/core.js`;
  const CORE_CSS = `https://pyscript.net/releases/${PYSCRIPT_VER}/core.css`;

  // --- load PyScript runtime on demand ---
  function loadPyScript() {
    if (pyLoaded) return Promise.resolve();
    if (pyLoading) return pyLoading;

    pyLoading = new Promise((resolve, reject) => {
      // css
      if (!document.getElementById('pyscript-core-css')) {
        const link = document.createElement('link');
        link.id = 'pyscript-core-css';
        link.rel = 'stylesheet';
        link.href = CORE_CSS;
        document.head.appendChild(link);
      }
      // js
      const script = document.createElement('script');
      script.id = 'pyscript-core';
      script.type = 'module';
      script.src = CORE_JS;
      script.onload = () => {
        pyLoaded = true;
        resolve();
      };
      script.onerror = () => reject(new Error('Failed to load PyScript core.js'));
      document.head.appendChild(script);
    });
    return pyLoading;
  }

  // --- styling & dragging ---
  function injectShellStyles() {
    if (document.getElementById('risen-style')) return;
    const css = `
#risen-shell-wrapper{position:fixed;top:10vh;left:10vw;width:600px;height:400px;border:1px solid #555;background:#111;color:#eee;display:none;resize:both;overflow:hidden;z-index:9999;box-shadow:0 0 10px rgba(0,0,0,.6);border-radius:.5rem}
#risen-shell-wrapper .risen-header{background:#222;user-select:none;cursor:move;padding:.25rem .5rem;font-family:sans-serif;font-size:.9rem}
#risen-shell-wrapper .risen-body{width:100%;height:calc(100% - 1.5rem);overflow:auto}
`;
    const style = document.createElement('style');
    style.id = 'risen-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function makeDraggable(win, handle) {
    let drag = false, offX=0, offY=0;
    handle.addEventListener('pointerdown', e=>{drag=true;offX=e.clientX-win.offsetLeft;offY=e.clientY-win.offsetTop;handle.setPointerCapture(e.pointerId);});
    handle.addEventListener('pointermove', e=>{if(!drag)return;win.style.left=`${e.clientX-offX}px`;win.style.top=`${e.clientY-offY}px`;});
    handle.addEventListener('pointerup',()=>drag=false);
  }

  // --- init once ---
  function initShell() {
    if (initialized) return;
    injectShellStyles();
    const wrapper = document.getElementById('risen-shell-wrapper');
    makeDraggable(wrapper, wrapper.querySelector('.risen-header'));
    initialized = true;
  }

  // --- public API ---
  risen.open = () => {
    initShell();
    loadPyScript().then(()=>{
      document.getElementById('risen-shell-wrapper').style.display='block';
    }).catch(console.error);
  };

  risen.close = () => {
    const el=document.getElementById('risen-shell-wrapper'); if(el) el.style.display='none';
  };

  risen.call = async ()=>{throw new Error('risen.call() not implemented yet');};
  risen.callback=(n,f)=>{console.warn('risen.callback placeholder');};

  global.risen = risen;
})(window);
