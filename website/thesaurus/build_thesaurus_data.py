"""Generate thesaurus_data.js (tree per skos:ConceptScheme) from ontology/thesaurus.ttl."""
import json, pathlib
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import SKOS

here = pathlib.Path(__file__).parent
ttl = here / "../../ontology/thesaurus.ttl"
g = Graph()
# the ontology file does not declare every prefix it uses
extra = ("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
         "@prefix dcat: <http://www.w3.org/ns/dcat#> .\n"
         "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
g.parse(data=extra + ttl.read_text(encoding="utf-8"), format="turtle")

def label(s):
    labels = list(g.objects(s, SKOS.prefLabel))
    en = [l for l in labels if getattr(l, "language", None) == "en"]
    return str((en or labels or [str(s).split("#")[-1]])[0])

def details(s):
    fmt = lambda l: str(l) + (" (@%s)" % l.language if getattr(l, "language", None) else "")
    return {
        "prefLabels": sorted(fmt(l) for l in g.objects(s, SKOS.prefLabel)),
        "altLabels": sorted(fmt(l) for l in g.objects(s, SKOS.altLabel)),
        "definition": [str(d) for d in g.objects(s, SKOS.definition)] + [str(d) for d in g.objects(s, SKOS.note)],
    }

def build(scheme):
    members = set(g.subjects(SKOS.inScheme, scheme))
    parents = {}
    for c in members:
        ps = {p for p in g.objects(c, SKOS.broader) if p in members}
        ps |= {p for p in g.subjects(SKOS.narrower, c) if p in members}
        parents[c] = ps
    def node(c, path):
        kids = sorted((k for k in members if c in parents[k] and k not in path), key=label)
        n = {"uri": str(c), "name": label(c), **details(c)}
        if kids:
            n["children"] = [node(k, path | {c}) for k in kids]
        else:
            n["size"] = 1.0
        return n
    roots = sorted((c for c in members if not parents[c]), key=label)
    return {"uri": str(scheme), "name": label(scheme), **details(scheme),
            "children": [node(r, frozenset()) for r in roots]}

schemes = sorted(g.subjects(RDF.type, SKOS.ConceptScheme), key=label)
data = [build(s) for s in schemes]
(here / "thesaurus_data.js").write_text(
    "var SCHEMES = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print(len(data), "schemes")

import shutil
shutil.copyfile(ttl, here / "thesaurus.ttl")
