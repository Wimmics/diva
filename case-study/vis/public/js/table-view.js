class TableView {
    constructor(container) {    
        this.container = container;
        
        this.headers = [];
        this.data = [];

        this.rowsPerPage = 30;
        this.currentPage = 1;
        this.sortDirection = {}; // Tracks asc/desc for each column
    }

    set(sparqlResults) {

        if (!sparqlResults || !sparqlResults.head || !sparqlResults.results || !Array.isArray(sparqlResults.results.bindings)) {
            console.error("Invalid SPARQL results format");
            return;
        }
        
        let recordCountVar = 'row count';
        this.headers = [recordCountVar].concat(sparqlResults.head.vars)
       
        this.data = sparqlResults.results.bindings.map((row, index) => ({...row, [recordCountVar]: { value: index + 1 } }));
        
        // Calculate rows per page based on container size
        this.rowsPerPage = 20
        
        const thead = document.querySelector("#results-table thead");
        const tbody = document.querySelector("#results-table tbody");
        thead.innerHTML = "";
        tbody.innerHTML = "";
        
        // Create table header
        const tr = document.createElement("tr");
        this.headers.forEach((header, index) => {
            const th = document.createElement("th");
            th.textContent = header;
            th.addEventListener("click", () => this.sortTableByColumn(index));
            tr.appendChild(th);
        });
        thead.appendChild(tr);
        
        this.currentPage = 1;

        this.render();
    }
      

    render(page = 1) {
        const tableBody = this.container.querySelector("tbody");
        tableBody.innerHTML = "";
    
        const start = (page - 1) * this.rowsPerPage;
        const end = start + this.rowsPerPage;
        const paginatedData = this.data.slice(start, end);
        
        
        for (const row of paginatedData) {
            const tr = document.createElement("tr");
            
            for (const varName of this.headers) {
                const td = document.createElement("td");
                const cell = row[varName];
                td.textContent = cell ? cell.value : "";  // use value if it exists
                tr.appendChild(td);
            }
            
            tableBody.appendChild(tr);
        }
        
        this.renderPagination(this.data.length);
    }
    
    renderPagination(totalRows) {
        const pagination = document.getElementById("pagination");
        pagination.innerHTML = "";
        
        const pageCount = Math.ceil(totalRows / this.rowsPerPage);
        
        const createButton = (label, page, disabled = false) => {
            const btn = document.createElement("button");
            btn.textContent = label;
            btn.disabled = disabled;
            if (!disabled) {
                btn.addEventListener("click", () => {
                    this.currentPage = page;
                    this.render(this.currentPage);
                    this.renderPagination(totalRows);
                });
            }
            return btn;
        }
        
        // ← Previous
        pagination.appendChild(createButton("←", this.currentPage - 1, this.currentPage === 1));
        
        // Always show first two pages
        for (let i = 1; i <= Math.min(2, pageCount); i++) {
            pagination.appendChild(createButton(i, i, this.currentPage === i));
        }
        
        // Left ellipsis
        if (this.currentPage > 4) {
            const dots = document.createElement("span");
            dots.textContent = "...";
            dots.className = "dots";
            pagination.appendChild(dots);
        }
        
        // Middle current page (if not near edges)
        if (this.currentPage > 2 && this.currentPage < pageCount - 1) {
            pagination.appendChild(createButton(this.currentPage, this.currentPage, true));
        }
        
        // Right ellipsis
        if (this.currentPage < pageCount - 3) {
            const dots = document.createElement("span");
            dots.textContent = "...";
            dots.className = "dots";
            pagination.appendChild(dots);
        }
        
        // Always show last two pages
        for (let i = Math.max(pageCount - 1, 3); i <= pageCount; i++) {
            if (i > 2) {
                pagination.appendChild(createButton(i, i, this.currentPage === i));
            }
        }
        
        // → Next
        pagination.appendChild(createButton("→", this.currentPage + 1, this.currentPage === pageCount));
    }
    
    sortTableByColumn(colIndex) {
        const isAsc = sortDirection[colIndex] = !sortDirection[colIndex];
        this.data.sort((a, b) => {
            if (a[colIndex] < b[colIndex]) return isAsc ? -1 : 1;
            if (a[colIndex] > b[colIndex]) return isAsc ? 1 : -1;
            return 0;
        });
        this.render(this.currentPage);
    }

}