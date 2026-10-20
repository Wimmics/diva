// Injects the shared footer (footer.html + site-footer.css) into <footer id="site-footer">.
(function () {
  const base = new URL('.', document.currentScript.src);
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = new URL('site-footer.css', base);
  document.head.appendChild(css);
  const target = document.getElementById('site-footer');
  fetch(new URL('footer.html', base))
    .then(r => r.text())
    .then(html => { target.innerHTML = html.replaceAll('{{root}}', base.href); });
})();
