class BarChart extends HTMLElement {
    constructor() {
        super()

        this.attachShadow({ mode: "open" });

        this.svg = null;

        this.nodes = [];
        this.links = [];

        // To organize private attributes (e.g. query, endpoint)
        this.internalData = new WeakMap()
        this.internalData.set(this, {}); // Initialize internal storage
    }

    set sparqlResults(json) {
        const data = this.internalData.get(this) || {};
        data.json = json;
        this.internalData.set(this, data);
    }
    
    get sparqlResults() {
        return this.internalData.get(this)?.json;
    }

    set encoding(json) {
        const data = this.internalData.get(this) || {};
        data.encoding = json;
        this.internalData.set(this, data);
    }   

    get encoding() {
        return this.internalData.get(this)?.encoding || this.defaultEncoding();
    }

    async connectedCallback() {
        this.render();

        this.svg = d3.select(this.shadowRoot.querySelector("#chart-container"))
    }

    render() {
        this.shadowRoot.innerHTML = `
          <style>
            svg {
                border: 1px solid #ccc;
            }

            #tooltip {
                position: absolute;
                pointer-events: none;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1000;
                opacity: 0; /* Start hidden */
            }
          </style>

          <div id="tooltip" ></div>

          <svg id="chart-container"></svg>
          
        `;
    }

    defaultEncoding() {
        return {
            "y": {
                "field": null,
            },
            "x": {
                "field": null,
            },
            "color": {
                "field": null,
                "type": "ordinal"
            },
            "nodes": {
                "field": null
            }
        }
    }

    updateDimensions() {
        this.defaultWidth = this.width = computePixelValue('width', this.getAttribute("width"), this.parentElement) || 1200;
        this.height =  computePixelValue('height', this.getAttribute("height"), this.parentElement) || 800;
        this.height *= .9 // reduce height by 10% to leave space for the toolbar

        if (this.getAttribute("width") === null) {
            console.warn('No width specified for the chart. Using default value of 1200px.');
        }
        if (this.getAttribute("height") === null) {
            console.warn('No height specified for the chart. Using default value of 800px.');
        }

        
        this.svg.attr('height', this.height).attr('width', this.width)
    }

    async draw() {
        this.updateDimensions();

        this.data = this.sparqlResults?.results?.bindings || [];
        if (!this.data.length) {
            console.warn("No data found in SPARQL results.");
            return;
        }

        this.createStack()
        this.drawChart()
    }
      
    
    displayTooltip(content) {
        const tooltip = d3.select(this.shadowRoot.querySelector("#tooltip"));

        tooltip
            .style("position", "absolute")
            .style("opacity", 1)
            .html(content)
            .style("left", `${d3.event.pageX + 10}px`)
            .style("top", `${d3.event.pageY + 10}px`);
    }

    hideTooltip() {
        const tooltip = d3.select(this.shadowRoot.querySelector("#tooltip"));
        tooltip.style("opacity", 0);
    }
  
    createStack() {
        // === Parse SPARQL JSON ===
        const data = this.data.map(d => ({
            user: d.user.value,
            visType: d.visType.value,
            actionType: d.actionType.value,
            repetitions: +d.repetitions.value
        }));

        // === Nest and stack data ===
        // const users = Array.from(new Set(data.map(d => d.user)));
        // const visTypes = Array.from(new Set(data.map(d => d.visType)));
        const actionTypes = Array.from(new Set(data.map(d => d.actionType))).sort();

        const nested = d3.nest()
            .key(d => d.user)
            .key(d => d.visType)
            .rollup(leaves => {
                const byAction = {};
                actionTypes.forEach(a => byAction[a] = 0);
                leaves.forEach(d => byAction[d.actionType] += d.repetitions);
                return byAction;
            })
            .entries(data);

        // Flatten for stack layout
        const flatData = [];
        nested.forEach(userGroup => {
            userGroup.values.forEach(visGroup => {
                const row = { user: userGroup.key, visType: visGroup.key };
                Object.assign(row, visGroup.value);
                flatData.push(row);
            });
        });

        // === Stack layout ===
        const stack = d3.stack().keys(actionTypes);
        this.stackedSeries = stack(flatData);

        this.colorScale = d3.scaleOrdinal()
            .domain(actionTypes)
            .range(d3.schemeSet2);
        
    }
    
    drawChart() {
        let margin = { top: 50, right: 200, bottom: 150, left: 60 },
            width = this.width - margin.left - margin.right,
            height = this.height - margin.top - margin.bottom;
    
        const users = Array.from(new Set(this.data.map(d => d.user.value)));
        const visTypes = Array.from(new Set(this.data.map(d => d.visType.value)));
        const barPositions = [];
    
        // === Set scales ===
        const x0 = d3.scaleBand()
            .domain(users)
            .range([0, width])
            //.paddingInner(0.1);
    
        const x1 = d3.scaleBand()
            .domain(visTypes)
            .range([0, x0.bandwidth()])
            .padding(0.05);

        users.forEach(user => {
            visTypes.forEach(vis => {
                barPositions.push({
                    key: `${user}--${vis}`,
                    user,
                    visType: vis,
                    position: x0(user) + x1(vis) 
                });
            });
        });

        const flatScale = d3.scaleBand()
            .domain(barPositions.map(d => d.key))
            .range([0, width])
            .padding(0.05);

        const y = d3.scaleLinear()
            .domain([0, d3.max(this.stackedSeries[this.stackedSeries.length - 1], d => d[1])])
            .nice()
            .range([height, 0]);
    
        const g = this.svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
        
        // === Top x-axis: Users ===
        g.append("g")
            .attr("class", "x-axis-user")
            .call(d3.axisTop(x0));
        
        g.append("text")
            .attr("x", width / 2)
            .attr("y", -20)
            .style("text-anchor", "middle")
            .style("font-weight", "bold")
            .text(this.encoding?.x?.label || this.encoding?.x?.field);
          
        // === Bottom x-axis: group field ===
        const xAxisVis = g.append("g")
            .attr("class", "x-axis-vis")
            .attr("transform", `translate(0,${height})`)
            .call(
                d3.axisBottom(flatScale)
                    .tickFormat(d => d.split("--")[1])
            );

        xAxisVis.selectAll("text")
            .style("text-anchor", "end")
            .attr("transform", "rotate(-60)")
            .style("font-size", "12px")
            .style("fill", "#666");

        g.append("text")
            .attr("x", width / 2)
            .attr("y", height + margin.bottom - 10)
            .style("text-anchor", "middle")
            .style("font-weight", "bold")
            .text(this.encoding?.group?.label || this.encoding?.group?.field);
          
        
        // === Y-axis ===
        g.append("g")
            .attr("class", "y-axis")
            .call(d3.axisLeft(y));
        
        g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -50)
            .attr("x", -height / 2)
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style("font-weight", "bold")
            .text(this.encoding?.y?.label || this.encoding?.y?.field);

        // === Optional styling ===
        g.selectAll(".x-axis-user text")
            .style("font-weight", "bold");
    
        g.selectAll(".x-axis-vis text")
            .style("font-size", "12px")
            .style("fill", "#666")
            .style("text-anchor", "end")
            .attr('transform', 'translate(-15, 5)rotate(-60)')

        // Add vertical dashed lines to separate user groups
        g.selectAll(".user-separator")
            .data(users.slice(1)) // skip the first to avoid line at y=0
            .enter()
            .append("line")
            .attr("class", "user-separator")
            .attr("x1", d => x0(d))
            .attr("x2", d => x0(d))
            .attr("y1", 0)
            .attr("y2", height)
            .attr("stroke", "#999")
            .attr("stroke-dasharray", "4,4")
            .attr("stroke-width", 1);

        // === Draw stacked bars ===
        g.append("g")
            .selectAll("g")
            .data(this.stackedSeries)
            .enter().append("g")
            .attr("fill", d => this.colorScale(d.key)) // actionType
            .selectAll("rect")
                .data(d => d)
                .enter().append("rect")
                .attr("x", d => x0(d.data.user) + x1(d.data.visType))
                .attr("y", d => y(d[1]))
                .attr("height", d => y(d[0]) - y(d[1]))
                .attr("width", x1.bandwidth())
                .append('title')
                .text(d => `${d.data.user}: ${d.data.visType}`)

        this.drawLegend()
    
    }

    drawLegend() {
        // === Legend ===
        const legend = this.svg.append("g")
            .attr("class", "legend")
            .attr("transform", `translate(${this.width - 180}, 30)`); // adjust position

        const legendItemHeight = 20;
        const legendSpacing = 5;
        const top = 10;

        legend.append('g')
            .append('text')
            .style("font-weight", "bold")
            .text(this.encoding?.color?.label || "Color Legend")

        this.colorScale.domain().forEach((actionType, i) => {
            const item = legend.append("g")
                .attr("transform", `translate(0, ${top + i * (legendItemHeight + legendSpacing)})`);

            // Colored box
            item.append("rect")
                .attr("width", 16)
                .attr("height", 16)
                .attr("fill", this.colorScale(actionType));

            // Label
            item.append("text")
                .attr("x", 22)
                .attr("y", 12)
                .text(actionType)
                .style("font-size", "12px")
                .style("alignment-baseline", "middle");
        });

    }
    
}

customElements.define('vis-barchart', BarChart);
