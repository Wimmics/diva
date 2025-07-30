# ESTIME to DIVA Data Lifting

This directory contains scripts for lifting ESTIME visualization logs to the DIVA ontology format.

## Overview

### estime_parser.py
The `estime_parser.py` file contains a `LogParser` class that handles parsing and converting ESTIME visualization logs into DIVA ontology concepts. Key features:

- Parses JSON log data from ESTIME visualization sessions
- Extracts metadata about:
  - User actions (create, modify, delete visualizations)
  - Visualization types and their properties
  - Dataset information
  - UI interactions
  - Visual encodings
- Maps ESTIME concepts to DIVA ontology terms

### lifting-estime-to-diva.py
Main script that uses the parser to convert ESTIME logs to RDF format using the DIVA ontology.

## Installation

1. Create a Python virtual environment:
```sh
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install required packages:
```sh
pip install -r requirements.txt
```

## Usage

1. Place your ESTIME JSON log files in the `/case-study/data/input` directory
2. Run the lifting script providing the input and output folders as parameters:
```sh
python lifting-estime-to-diva.py ../data/input ../data/output
```
3. The converted RDF data will be saved in the `/case-study/data/output` directory

## Requirements
See `requirements.txt` for full list of dependencies. Main requirements:
- Python 3.7+
- rdflib
- json