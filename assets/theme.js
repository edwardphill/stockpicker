// Light/dark switch shared by every page. Loaded in <head> so the stored
// choice applies before the first paint. Dark (terminal) is the default.
(function () {
  var KEY = 'sp-theme';
  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function apply(t) {
    if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
    else document.documentElement.removeAttribute('data-theme');
    var btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = t === 'light' ? 'Dark' : 'Light';
  }
  window.toggleTheme = function () {
    var next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    try { localStorage.setItem(KEY, next); } catch (e) {}
    apply(next);
  };
  apply(stored());
  document.addEventListener('DOMContentLoaded', function () { apply(stored()); });
})();
