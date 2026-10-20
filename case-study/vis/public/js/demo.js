// index in the select (0 is the placeholder): 2 = second competency question
const DEFAULT_QUESTION = 2

class DIVADemo {
    constructor() {
        this.currentData // SPARQL results
        this.currentQueryName // file name for the selected query
        this.currentConfig // configuration for the visualizations of the selected query
        this.currentQuery // query string

        this.tableElement = new TableView(document.querySelector('#results-table'))
        this.muvinElement = document.querySelector('#vis-muvin')
        this.barchartElement = document.querySelector("#bar-chart")
        this.textArea = document.querySelector(".language-sparql")

        this.set()
    }

    async set() {
        let queries = await fetch('api/queries.json').then(res => res.json())

        let queriesSelect = [{label: 'Select a competency question', query: null}].concat(queries)
        d3.select('select#competency-questions')
            .selectAll('option')
            .data(queriesSelect)
            .join('option')
            .attr('value', d => d.queryFile)
            .text(d => d.label)
            .property('disabled', (_,i) => i === 0)
            .property('selected', (_,i) => i === DEFAULT_QUESTION)


        // Listen for when a tab is shown
        const tabButtons = document.querySelectorAll('#mainTabs button[data-bs-toggle="tab"]');

        tabButtons.forEach(button => {
            button.addEventListener('shown.bs.tab', event => {
                if (!this.currentData) return

                const targetTabId = event.target.getAttribute('data-bs-target'); 

                // Example: Run code depending on which tab is shown
                switch (targetTabId) {
                case "#results":
                    this.tableElement.set(this.currentData)
                    break;
                case "#vis":
                    this.showVisualization()
                    break
                }
            });
        });

        document.querySelector('#competency-questions').addEventListener('change', async (event) => {
            const selectElement = event.target;
            this.currentQueryName = selectElement.value;

            this.currentData = await fetch(`api/results/${this.currentQueryName}.json`).then(response => response.json())

            this.currentConfig = await fetch(`api/config/${this.currentQueryName}.json`).then(response => response.json())

            this.currentQuery = await fetch(`api/query/${this.currentQueryName}`).then(response => response.text())

            this.setQuery()
        });

        if (queriesSelect[DEFAULT_QUESTION])
            document.querySelector('#competency-questions').dispatchEvent(new Event('change'))
    }

    setQuery() {
        const resultsTabEl = document.querySelector('#sparql-tab');
        const tab = new bootstrap.Tab(resultsTabEl);
        tab.show();
        
        // Set the SPARQL query in the code block    
        this.textArea.textContent = this.currentQuery
        Prism.highlightAll();
    }
    
    async setMuvin(data, config) {
    
        document.querySelector('#muvin-container').style.display = 'block'

        await this.muvinElement.reset()

        if (config.width) this.muvinElement.setAttribute("width", this.muvinElement.parentNode.clientWidth)
        if (config.height) this.muvinElement.setAttribute("height", config.height)
    
        this.muvinElement.sparqlResults = data;
    
        this.muvinElement.encoding = config.encoding
    
        let nodeField = config.encoding.nodes.field;
    
        let nodes = data.results.bindings.map(d => {
            if (Array.isArray(nodeField)) {
                return nodeField.map(f => d[f]?.value).filter(Boolean).join(" | "); // Join multiple fields
            } else {
                return d[nodeField]?.value;
            }
            }).filter(Boolean)
    
        nodes = [...new Set(nodes)];
        
        this.muvinElement.launch(nodes);
    }

    showVisualization() {
        const cfg = this.currentConfig
        const isMuvin = !!cfg.muvin, isBar = !!cfg.barchart
        document.querySelector('#muvin-container').style.display = isMuvin ? 'block' : 'none'
        document.querySelector('#barchart-container').style.display = isBar ? 'block' : 'none'
        const msg = document.querySelector('#muvin-message')
        msg.style.display = (isMuvin || isBar) ? 'none' : 'block'
        msg.textContent = 'This query has no visualization'
        if (isMuvin) this.setMuvin(this.currentData, cfg.muvin)
        else if (isBar) this.setBarChart(this.currentData, cfg.barchart)
    }

    hideVis(id) {
        let messageDiv = document.querySelector(`#${id}-message`)
        messageDiv.style.display = 'block'
        messageDiv.innerHTML = "This query is not visualizable with " + id
        document.querySelector(`#${id}-container`).style.display = 'none'
    }
    
    setBarChart(data, config) {
        document.querySelector('#barchart-container').style.display = 'block'

        this.barchartElement.encoding = config.encoding
        this.barchartElement.sparqlResults = data
        this.barchartElement.draw()
    }

    


}



