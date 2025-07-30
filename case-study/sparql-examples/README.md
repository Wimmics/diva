# SPARQL Query Examples

This directory contains SPARQL queries that demonstrate key competency questions for analyzing analytical provenance information using the DIVA ontology.

## Competency Questions

### Query 1: What are the sequence of actions of a specific user?
[query1.rq](query1.rq) retrieves the sequence of actions performed by a specific user during their visualization exploration:
- Retrieves each action's title and type
- Displays the step number in the exploration sequence  
- Identifies entities (visualizations, manipulations) involved in each action
- Filters for a specific user ("user_1")
- Orders results by exploration step

```sparql
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX diva: <http://ns.inria.fr/diva/ontology#>
prefix dc: <http://purl.org/dc/terms/> 
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> 


SELECT DISTINCT ?action ?actionTitle ?step ?actionType ?entityName ?user WHERE {

    BIND ("user_1" as ?user)

    ?action a diva:Action ;
        prov:wasAssociatedWith [ foaf:name ?user ] ; 
        diva:hasActionType [ skos:prefLabel ?actionType ] ;
        dc:description ?actionTitle ;
        prov:used ?entity .

    OPTIONAL {
        ?entity diva:hasViewManipulationType [ skos:prefLabel ?VMType ] .
    }

    OPTIONAL {
        ?entity a [ rdfs:label ?className ] .
        FILTER langMatches(lang(?className), "en")
    }

    OPTIONAL {
        ?vis a [ rdfs:label ?visName ] ; 
            prov:wasGeneratedBy ?action  .
    }

    BIND (COALESCE(?visName, ?VMType, ?className) as ?entityName)

    ?explorationPath a diva:ExplorationPath ;
        ?p ?action .

    BIND (xsd:integer(REPLACE(STR(?p), ".*[#_]", "")) AS ?step) .
     
} ORDER BY ?step
```

### Query 2: Do users exhibit similar patterns in their sequences of actions?
[query2.rq](query2.rq) finds all actions that involved creating or modifying visualizations:
- Captures both actions that used existing visualizations and those that generated new ones
- Shows the visualization type for each action
- Includes the user who performed the action
- Orders results chronologically by step number

```sparql
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX diva: <http://ns.inria.fr/diva/ontology#>
PREFIX dc: <http://purl.org/dc/terms/> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 

SELECT DISTINCT ?action ?actionTitle ?step ?actionType ?entityName ?user WHERE {

    ?action a diva:Action ;
        prov:wasAssociatedWith [ foaf:name ?user ] ; 
        diva:hasActionType [ skos:prefLabel ?actionType ] ;
        dc:description ?actionTitle  .

    { ?action prov:used ?entity }
    UNION
    { ?entity prov:wasGeneratedBy ?action }

    ?entity a ?class .
    ?class rdfs:subClassOf diva:Visualization ;
        rdfs:label ?entityName .

    ?explorationPath a diva:ExplorationPath ;
        ?p ?action .

    BIND (xsd:integer(REPLACE(STR(?p), ".*[#_]", "")) AS ?step) .
     
} ORDER BY ?step
```

### Query 3: Are there observable trends on the way visualizations are used by the users?
[query3.rq](query3.rq) analyzes patterns in how users interact with different visualization types:
- Counts the number of times each user performed specific action types
- Groups results by user, action type, and visualization type
- Provides insight into which visualizations see the most user interaction
- Shows user preferences for different visualization operations

```sparql
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX diva: <http://ns.inria.fr/diva/ontology#>
PREFIX dcterms: <http://purl.org/dc/terms/> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX dcat: <http://www.w3.org/ns/dcat#> 

SELECT ?user ?actionType ?visType (COUNT(?action) AS ?repetitions) WHERE {
  ?action a diva:Action ;
          prov:wasAssociatedWith [ foaf:name ?user ] ;
          diva:hasActionType [ skos:prefLabel ?actionType ] ;
          prov:startedAtTime ?time .

  { ?action prov:used ?entity . }
  UNION
  { ?entity prov:wasGeneratedBy ?action . }

  ?entity a ?class .
  ?class rdfs:subClassOf diva:Visualization ;
    rdfs:label ?visType .
}
GROUP BY ?user ?actionType ?visType
```

## Usage

These queries can be executed against any RDF store containing exploration path data conforming to the DIVA ontology. 

To run these queries, use your preferred SPARQL endpoint or RDF query tool, ensuring your data includes the required DIVA ontology predicates and classes.