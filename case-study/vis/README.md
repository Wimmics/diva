# DIVA Visualization Demo

A web application for exploring and visualizing analytical provenance data using the DIVA ontology.

## Overview

This application provides interactive visualizations of user exploration processes within visualization tools. It uses SPARQL queries to extract provenance information and displays it through multiple visualization types.

## Features

1. **Query Selection**
    - Dropdown menu for competency questions (defined in [here](../sparql-examples/README.md))
    - Dynamic loading of SPARQL queries
    - Query result caching

2. **Visualization Views**
    - SPARQL query display with syntax highligthing
    - Results table
    - Temporal sequence and relationships view supported by the Muvin tool
    - A bar chart for summarized information

## Dependencies

**Backend**
- Express.js for the backend server
- [Corese-Command](https://corese-stack.github.io/corese-command/v4.6.1/user_guide.html) for SPARQL query handling

**Frontend**
- D3.js for data visualization
- [Muvin](https://www.npmjs.com/package/muvin) for temporal sequences view

Check all dependencies in the [package.json](package.json)

## Setup

1. Install dependencies

```bash
npm install
```

- Corese-command should be installed separately. Check the installation guide [here](https://corese-stack.github.io/corese-command/v4.6.1/install.html)

2. Start the server:

```bash
node server.js
```

3. Access the application at [http://localhost:3000](http://localhost:3000)

## Directory Structure

```
vis/
├── public/
│   ├── js/
│   │   ├── demo.js       # Main application logic
│   │   ├── table-view.js # Results table component
│   │   └── barchart.js   # Bar chart visualization
│   └── css/
├── views/
│   └── index.ejs         # Main application template
├── config.json          # Config file for competency questions and visualizations
└── server.js            # Express server setup
```

