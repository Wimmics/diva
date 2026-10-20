// Extends the ToC with entity hierarchies and highlights the section currently in view.
window.addEventListener("load", function () {
  var toc = document.getElementById("toc");
  if (!toc) return;

  function label(entity) {
    var h = entity.querySelector("h3");
    if (!h) return entity.id;
    var c = h.cloneNode(true);
    c.querySelectorAll("sup, span").forEach(function (n) { n.remove(); });
    return c.textContent.trim();
  }

  function localSuper(entity, ids) {
    var dts = entity.querySelectorAll("dl.description > dt");
    for (var i = 0; i < dts.length; i++) {
      if (!/super-(classes|properties)/.test(dts[i].textContent)) continue;
      var links = dts[i].nextElementSibling.querySelectorAll("a[href^='#']");
      for (var j = 0; j < links.length; j++) {
        var id = links[j].getAttribute("href").slice(1);
        if (ids[id]) return id;
      }
    }
    return null;
  }

  // Moves entity cards (and their chips) so the page follows the ToC order.
  function reorder(section, entities, order, byId) {
    var parent = entities[0].parentNode;
    var next = entities[entities.length - 1].nextSibling;
    order.forEach(function (id) { parent.insertBefore(byId[id], next); });
    var chips = {}, list = section.querySelector("ul.hlist");
    if (!list) return;
    list.querySelectorAll("li > a[href^='#']").forEach(function (a) { chips[a.getAttribute("href").slice(1)] = a.parentElement; });
    order.forEach(function (id) { if (chips[id]) list.appendChild(chips[id]); });
  }

  function buildTree(sectionId) {
    var section = document.getElementById(sectionId);
    if (!section) return null;
    var entities = Array.prototype.slice.call(section.querySelectorAll(".entity"));
    if (!entities.length) return null;
    var byId = {}, children = {}, roots = [];
    entities.forEach(function (e) { byId[e.id] = e; children[e.id] = []; });
    entities.forEach(function (e) {
      var p = localSuper(e, byId);
      if (p && p !== e.id) children[p].push(e.id); else roots.push(e.id);
    });
    var seen = {}, order = [];
    function render(ids) {
      var ul = document.createElement("ul");
      ids.forEach(function (id) {
        if (seen[id]) return;
        seen[id] = true;
        order.push(id);
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + id;
        a.textContent = label(byId[id]);
        li.appendChild(a);
        if (children[id].length) {
          var sub = render(children[id]);
          if (sub.childNodes.length) {
            var t = document.createElement("button");
            t.type = "button";
            t.className = "toc-toggle toc-node-toggle";
            t.setAttribute("aria-label", "Collapse or expand");
            t.addEventListener("click", function () { li.classList.toggle("collapsed"); });
            li.appendChild(t);
            li.classList.add("has-children", "collapsed");
            li.appendChild(sub);
          }
        }
        ul.appendChild(li);
      });
      return ul;
    }
    var tree = render(roots);
    // entities caught in a cycle are not reachable from a root; list them flat
    var orphans = entities.map(function (e) { return e.id; }).filter(function (id) { return !seen[id]; });
    if (orphans.length) render(orphans).childNodes.forEach(function (n) { tree.appendChild(n.cloneNode(true)); });
    tree.className = "toc-entities";
    orphans.forEach(function (id) { order.push(id); });
    reorder(section, entities, order, byId);
    return tree;
  }

  [["classes-headline", "classes"], ["properties", "objectproperties"],
   ["dataproperties-headline", "dataproperties"], ["namedindividuals", "namedindividuals"]]
    .forEach(function (pair) {
      var link = toc.querySelector("a[href='#" + pair[0] + "']");
      var tree = buildTree(pair[1]);
      if (!link || !tree) return;
      var li = link.parentElement;
      li.classList.add("has-entities");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "toc-toggle";
      btn.setAttribute("aria-label", "Collapse or expand");
      btn.addEventListener("click", function () { li.classList.toggle("collapsed"); });
      li.appendChild(btn);
      var count = document.createElement("span");
      count.className = "toc-count";
      count.textContent = tree.querySelectorAll("li").length;
      li.appendChild(count);
      li.appendChild(tree);
    });

  var items = [];
  toc.querySelectorAll("li > a[href^='#']").forEach(function (a) {
    var target = document.getElementById(a.getAttribute("href").slice(1));
    if (target) items.push({ li: a.parentElement, target: target });
  });
  if (!items.length) return;

  var lastBest = null;
  function update() {
    var best = items[0], bestTop = -Infinity;
    items.forEach(function (it) {
      var top = it.target.getBoundingClientRect().top;
      if (top <= 80 && top > bestTop) { best = it; bestTop = top; }
    });
    items.forEach(function (it) { it.li.classList.toggle("active", it === best); });
    if (best !== lastBest) {
      lastBest = best;
      for (var p = best.li.parentElement; p && p !== toc; p = p.parentElement)
        if (p.tagName === "LI") p.classList.remove("collapsed");
    }
    var li = best.li;
    if (li.offsetParent && li.getClientRects().length) {
      var r = li.getBoundingClientRect(), t = toc.getBoundingClientRect();
      if (r.top < t.top || r.bottom > t.bottom) toc.scrollTop += r.top - t.top - toc.clientHeight / 2;
    }
  }
  var ticking = false;
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(function () { update(); ticking = false; }); }
  }, { passive: true });
  update();
});

// Embeds a WebVOWL diagram built on the fly from the published ontology file,
// so the diagram follows ontology updates without regenerating this page.
(function () {
  var host = document.getElementById("webvowl-diagram");
  if (!host) return;
  var url = host.getAttribute("data-ontology-url");
  var src = "https://service.tib.eu/webvowl/#iri=" + encodeURIComponent(url);
  host.innerHTML =
    '<h4>Ontology diagram</h4>' +
    '<div class="webvowl-bar"><span>Generated live with WebVOWL from <a href="' + url + '">the ontology file</a>.</span>' +
    '<a class="webvowl-open" href="' + src + '" target="_blank" rel="noopener">Open in WebVOWL &#8599;</a></div>' +
    '<iframe title="WebVOWL ontology diagram" loading="lazy" src="' + src + '"></iframe>';
})();
