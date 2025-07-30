
# DIVA: Data, Interaction, Visualization, and Analysis 

An ontology for representing and analyzing analytical provenance information from visualization tools.

## Overview

DIVA provides and ontology and a thesaurus to:

- Model user interactions with visualization tools
- Capture exploration paths and patterns
- Enable semantic analysis of visual analytics process
- Support reuse and comparison of analysis strategies

The DIVA namespace is ``http://ns.inria.fr/diva/``

## RDF Data Modeling

See the [DIVA ontology](ontology) repository.

## Case Study: eSTIMe visualization system

To demonstrate the usage of DIVA ontology, we lifted system logs describing analytical provenance information from the eSTIMe visualization system, a multi-screen visualization platform designed for exploring urban mobility data. 

The system logs describe the exploration processes of six users, varying from 31 to 207 steps (i.e., performed actions within the visualization). Each log was recorded as a JSON array, structured sequentially to represent user interactions and the corresponding visualization states. Each log entry includes metadata such as timestamp, action type, target, view context, and descriptors of the resulting artifacts (e.g., visualizations or datasets). We used the `rdflib` library in `Python` to transform this structured JSON data into an RDF KG.

A set of competency questions were implemented through SPARQL queries and interactive visualization tools, supporting visual exploration of analytical provenance information.

See the [Case Study](case-study) repository.

## Directory Structure

```
diva/
├── ontology/              # DIVA ontology files
│   ├── diva.ttl          # Core OWL ontology in Turtle format
│   └── thesaurus.ttl     # Controlled vocabulary
│
└── case-study/           # Example implementation
    ├── data/             # Input and output data used in the case study                                    
    ├── lifting/          # Data conversion scripts
    ├── sparql-examples/  # Example SPARQL queries and competency questions
    └── vis/              # Visualization components
``` 

## License

See the [LICENSE](LICENSE) file.