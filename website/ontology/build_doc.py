#!/usr/bin/env python3
"""Generates the DIVA ontology documentation page (a WIDOCO replacement).

Everything that can be derived from the ontology (metadata, namespaces, class /
property / individual cross-reference, overview lists) is regenerated from
`ontology/diva.ttl`. Hand-written parts live in `src/` and are never touched:

    src/config.json         page-level settings not stored in the ontology
    src/introduction.md     Introduction (markdown)
    src/description.md      Description (markdown)
    src/references.md       References (markdown)
    src/acknowledgments.html
    src/head.html, src/body.html   page skeleton (@TOKENS@ are substituted)

Usage:  python3 build_doc.py            (from anywhere)
Writes: index.html and ontology.{ttl,owl,nt,jsonld} next to this script.
Requires: rdflib >= 6.
"""
import json
import shutil
import sys
from html import escape as _escape
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import DCAT, DCTERMS, OWL, RDF, RDFS

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"

KINDS = {  # kind -> (sup, sup title, section id, headline id, headline, toc label)
    "c": ("c", "class", "classes", "classes-headline", "Classes", "Class ToC"),
    "op": ("op", "object property", "objectproperties", "properties", "Object Properties", "Object Property ToC"),
    "dp": ("dp", "data property", "dataproperties", "dataproperties-headline", "Data Properties", "Data Property ToC"),
    "ni": ("ni", "named individual", "namedindividuals", "namedindividuals", "Named Individuals", "Named Individual ToC"),
}
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
SCHEMA_TYPES = {OWL.Class: "c", RDFS.Class: "c", OWL.ObjectProperty: "op", OWL.DatatypeProperty: "dp"}
IGNORED_TYPES = {OWL.Ontology, OWL.AnnotationProperty}


def escape(text):
    return _escape(text, quote=False)


def read(name):
    return (SRC / name).read_text(encoding="utf-8").strip()


def local_name(iri):
    return str(iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def md(text):
    """Markdown is rendered client-side by marked.js from the span's text."""
    return escape(text)


def pick(graph, subject, predicate):
    values = list(graph.objects(subject, predicate))
    if not values:
        return None
    values.sort(key=lambda v: (getattr(v, "language", None) not in (None, "en"), str(v)))
    return str(values[0])


class Doc:
    def __init__(self, config):
        self.cfg = config
        g = Graph(bind_namespaces="none")
        g.parse(str((SRC / config["ontology_file"]).resolve()), format="turtle")
        prefix = dict(g.namespaces()).get("rdf")
        if prefix is not None and str(prefix) != RDF_NS:
            print(f"warning: prefix 'rdf:' is bound to <{prefix}> in the ontology, not to the RDF "
                  "namespace; using the standard one in the generated files.", file=sys.stderr)
            g.bind("rdf", RDF, override=True, replace=True)
            g.bind("rdfs", RDFS, override=True, replace=True)
        self.g = g
        self.onto = next(g.subjects(RDF.type, OWL.Ontology))
        self.ns = str(self.onto)
        self.entities = self._collect()

    # ---------- model ----------
    def _collect(self):
        found = {}
        for s in set(self.g.subjects(RDF.type, None)):
            if not isinstance(s, URIRef) or not str(s).startswith(self.ns) or s == self.onto:
                continue
            types = set(self.g.objects(s, RDF.type))
            kind = next((SCHEMA_TYPES[t] for t in types if t in SCHEMA_TYPES), None)
            if kind is None and types <= IGNORED_TYPES:
                continue
            found[s] = kind or "ni"
        return found

    def label(self, iri):
        return pick(self.g, iri, RDFS.label) or pick(self.g, iri, DCTERMS.title) or local_name(iri)

    def by_kind(self, kind):
        items = [s for s, k in self.entities.items() if k == kind]
        return sorted(items, key=lambda s: self.label(s).lower())

    # ---------- html helpers ----------
    @staticmethod
    def sup(kind):
        code, title = KINDS[kind][:2]
        return f' <sup class="type-{code}" title="{title}">{code}</sup>'

    def link(self, iri, external_kind=None):
        if iri in self.entities:
            return (f'<a href="#{local_name(iri)}" title="{iri}">{escape(self.label(iri))}</a>'
                    + self.sup(self.entities[iri]))
        sup = self.sup(external_kind) if external_kind else ""
        return f'<a href="{iri}" target="_blank" title="{iri}">{escape(local_name(iri))}</a>{sup}'

    def links(self, iris, external_kind=None):
        iris = [i for i in iris if isinstance(i, URIRef)]
        iris.sort(key=lambda i: (i not in self.entities, self.label(i).lower()))
        return ", ".join(self.link(i, external_kind) for i in iris)

    @staticmethod
    def dl(pairs, indent="  "):
        rows = [f"{indent} <dt>\n{indent}  {t}\n{indent} </dt>\n{indent} <dd>\n{indent}  {d}\n{indent} </dd>"
                for t, d in pairs if d]
        return "\n".join(rows)

    # ---------- sections ----------
    def entity(self, iri):
        kind = self.entities[iri]
        code, title, section, _, _, toc_label = KINDS[kind]
        g, name = self.g, local_name(iri)
        comment = pick(g, iri, RDFS.comment)
        defined_by = pick(g, iri, RDFS.isDefinedBy)
        out = [
            f' <div class="entity" id="{name}">',
            f'  <h3>{escape(self.label(iri))}<sup class="type-{code}" title="{title}">{code}</sup> '
            f'<span class="backlink"> back to <a href="#toc">ToC</a> or <a href="#{section}">{toc_label}</a> </span></h3>',
            f"  <p><strong>IRI:</strong> {iri}</p>",
        ]
        if comment:
            out.append(f'  <div class="comment">\n   <span class="markdown">{md(comment)}</span>\n  </div>')
        if defined_by:
            out.append('  <dl class="definedBy">\n   <dt>\n    Is defined by\n   </dt>\n   <dd>\n'
                       f'    <a href="{defined_by}">{escape(defined_by)}</a>\n   </dd>\n  </dl>')

        if kind == "c":
            props = [s for s, k in self.entities.items() if k in ("op", "dp")]
            pairs = [
                ("has super-classes", self.links(list(g.objects(iri, RDFS.subClassOf)), "c")),
                ("has sub-classes", self.links([s for s in g.subjects(RDFS.subClassOf, iri)
                                                if s in self.entities], "c")),
                ("is in domain of", self.links([p for p in props if (p, RDFS.domain, iri) in g])),
                ("is in range of", self.links([p for p in props if (p, RDFS.range, iri) in g])),
            ]
            body = self.dl(pairs)
            if body:
                out.append(f'  <dl class="description">\n{body}\n  </dl>')
        elif kind in ("op", "dp"):
            pairs = [("has domain", self.links(list(g.objects(iri, RDFS.domain)))),
                     ("has range", self.links(list(g.objects(iri, RDFS.range))))]
            body = self.dl(pairs, "   ")
            if body:
                out.append(f'  <div class="description">\n   <dl>\n{body}\n   </dl>\n  </div>')
        else:
            types = [t for t in g.objects(iri, RDF.type) if t != OWL.NamedIndividual]
            body = self.dl([("belongs to", self.links(types, "c"))])
            if body:
                out.append(f'  <dl class="description">\n{body}\n  </dl>')
        out.append(" </div>")
        return "\n".join(out)

    def hlist(self, iris):
        items = "\n".join(f'  <li><a href="#{local_name(i)}" title="{i}">{escape(self.label(i))}</a></li>'
                          for i in iris)
        return f' <ul class="hlist">\n{items}\n </ul>'

    def crossref(self):
        parts = []
        for kind, (_, _, section, headline, title, _) in KINDS.items():
            iris = self.by_kind(kind)
            if not iris:
                continue
            body = "\n".join(self.entity(i) for i in iris)
            parts.append(f'<div id="{section}">\n <h3 id="{headline}" class="list">{title}</h3>\n'
                         f'{self.hlist(iris)}\n{body}\n</div>')
        return "\n".join(parts)

    def overview(self):
        parts = []
        for kind, (_, _, _, _, title, _) in KINDS.items():
            iris = self.by_kind(kind)
            if iris:
                parts.append(f"<h4>{title}</h4>\n{self.hlist(iris).replace(' <ul', '<ul', 1)}")
        return "\n".join(parts)

    def namespaces(self):
        items = sorted(self.g.namespaces(), key=lambda p: (str(p[1]) != self.ns, p[0]))
        return "".join(f"<tr><td><b>{p}</b></td><td>&lt;{escape(str(u))}&gt;</td></tr>\n" for p, u in items)

    def metadata(self):
        g, o, c = self.g, self.onto, self.cfg
        creators = sorted(str(x) for x in g.objects(o, DCTERMS.creator))
        modified, version = pick(g, o, DCTERMS.modified), pick(g, o, OWL.versionInfo)
        license_url = pick(g, o, DCTERMS.license)
        landing = pick(g, o, DCAT.landingPage)
        formats = [("JSON-LD", "JSON_LD", "ontology.jsonld"), ("RDF/XML", "RDF/XML", "ontology.owl"),
                   ("N-Triples", "N_Triples", "ontology.nt"), ("TTL", "TTL", c["ontology_file_url"])]
        badges = "".join(
            f'<span><a href="{href}" target="_blank"><img src="https://img.shields.io/badge/Format-{b}-blue.svg" '
            f'alt="{n}" /></a> </span>' for n, b, href in formats)
        rows = []

        def add(term, *values):
            rows.append(f"<dt>{term}</dt>")
            rows.extend(f"<dd>{v}</dd>" for v in values)

        if modified:
            rows.append(f"<dt>Modified on: {escape(modified)}</dt>")
        add("This version:", f'<a href="{c["this_version"]}">{self.ns}</a>')
        add("Latest version:", f'<a href="{c["latest_version"]}">{self.ns}</a>')
        if version:
            add("Revision:", escape(version))
        if creators:
            add("Authors:", *map(escape, creators))
        add("Publisher:", escape(c["publisher"]))
        add("Download serialization:", badges)
        if license_url:
            label = escape(c["license_label"])
            add("License:", f'<a href="{license_url}" target="_blank"><img src="https://img.shields.io/badge/License-'
                            f'{label.replace(" ", "_")}-blue.svg" alt="{label}" /></a>')
        cite = c.get("citation")
        if cite:
            links = [(l["label"], l["url"]) for l in cite.get("links", [])]
            if cite.get("bibtex_file"):
                links.append(("BibTeX", Path(cite["bibtex_file"]).name))
            anchors = " ".join(f'<a href="{u}">[{escape(n)}]</a>' for n, u in links)
            add("Cite as:", f'{escape(cite["text"])} {anchors}'.strip())
        if landing:
            add("Vocabulary maintained at:", f'<a href="{landing}">{escape(landing)}</a>')
        if c.get("see_also"):
            add("See also:", *(f'<a href="{s["url"]}">{escape(s["label"])}</a>' for s in c["see_also"]))
        return "\n".join(rows)

    def schema_org(self):
        g, o, c = self.g, self.onto, self.cfg
        data = {
            "@context": "https://schema.org", "@type": "TechArticle", "url": self.ns,
            "image": f"http://vowl.visualdataweb.org/webvowl/#iri={self.ns}",
            "name": pick(g, o, DCTERMS.title),
            "headline": f"Document describing the ontology {self.ns}",
            "dateReleased": pick(g, o, DCTERMS.created), "dateModified": pick(g, o, DCTERMS.modified),
            "version": pick(g, o, OWL.versionInfo), "license": pick(g, o, DCTERMS.license),
            "codeRepository": pick(g, o, DCAT.landingPage),
            "author": [{"@type": "Person", "name": str(a)} for a in sorted(g.objects(o, DCTERMS.creator))],
        }
        return json.dumps({k: v for k, v in data.items() if v}, ensure_ascii=False).replace("</", "<\\/")

    def page(self):
        c, title = self.cfg, pick(self.g, self.onto, DCTERMS.title)
        tokens = {
            "TITLE": escape(title), "RELEASE": escape(pick(self.g, self.onto, DCTERMS.created) or ""),
            "STATUS": escape(c["status"]), "SHORT": escape(c["short_name"]),
            "METADATA": self.metadata(), "NAMESPACES": self.namespaces(),
            "OVERVIEW": self.overview(), "CROSSREF": self.crossref(),
            "WEBVOWL_URL": c["webvowl_ontology_url"],
            "INTRODUCTION": md(read("introduction.md")), "DESCRIPTION": md(read("description.md")),
            "REFERENCES": md(read("references.md")), "ACKNOWLEDGMENTS": read("acknowledgments.html"),
            "SCHEMA_ORG": self.schema_org(),
        }
        html = read("head.html") + "\n\n" + read("body.html") + "\n"
        for key, value in tokens.items():
            html = html.replace(f"@{key}@", value)
        return html


SERIALIZATIONS = (("owl", "xml"), ("nt", "nt"), ("jsonld", "json-ld"))


def main():
    config = json.loads(read("config.json"))
    doc = Doc(config)
    (HERE / "index.html").write_text(doc.page(), encoding="utf-8")
    shutil.copyfile((SRC / config["ontology_file"]).resolve(), HERE / "ontology.ttl")
    bib = config.get("citation", {}).get("bibtex_file")
    if bib:
        shutil.copyfile(SRC / bib, HERE / Path(bib).name)
    for ext, fmt in SERIALIZATIONS:
        doc.g.serialize(destination=str(HERE / f"ontology.{ext}"), format=fmt)
    counts = {k: len(doc.by_kind(k)) for k in KINDS}
    print(f"Generated index.html and ontology.{{owl,nt,jsonld}} from {config['ontology_file']}: {counts}")


if __name__ == "__main__":
    main()
