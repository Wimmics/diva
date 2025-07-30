const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

// Set EJS as the view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// External vocabulaires used in our model
const prov = "https://www.w3.org/ns/prov-o"
const dcat = "https://www.w3.org/ns/dcat3.ttl"

// Serve static files from the 'public' folder
app.use(express.static(path.join(__dirname, 'node_modules/muvin/dist')));

app.use(express.static(path.join(__dirname, 'public')));

// Example route
app.get('/', (req, res) => {
    res.render('index')
})

app.get('/all-queries/', (req, res) => {
    let config = fs.readFileSync(path.join(__dirname, "config.json"))
    config = JSON.parse(config)

    let queries = config.map(d => ({label: d.label, queryFile: d.queryFile}))

    res.send(queries)
})

app.get('/clear-cache/', async (req, res) => {
    const cacheDir = path.join(__dirname, 'cache');
    try {
        const files = fs.readdirSync(cacheDir); 
    
        await Promise.all(
          files.map(file => fs.unlinkSync(path.join(cacheDir, file)))
        );
    
        res.status(200).json({ message: 'Cache cleared successfully.' });
    } catch (error) {
        console.error('Error clearing cache:', error);
        res.status(500).json({ message: 'Failed to clear cache.' });
    }
})

app.get('/query-config/', (req, res) => {

    const queryFile = req.query.queryFile;

    if (!queryFile) {
        return res.status(400).json({ error: 'Missing query parameter' });
    }

    let config = fs.readFileSync(path.join(__dirname, "config.json"))
    config = JSON.parse(config)

    let queryConfig = config.find(d => d.queryFile === queryFile)

    if (!queryConfig) {
        return res.status(404).json({ error: `The config for query: ${queryFile} could not be found.` }  )
    }

    res.send(queryConfig)
})

app.get('/query/', (req, res) => {
    const queryFile = req.query.queryFile

    if (!queryFile) {
        return res.status(400).json({ error: 'Missing query parameter' });
    }

    res.sendFile(path.join(__dirname, "../sparql-examples", queryFile))
})

app.get('/corese-query/', (req, res) => {
    const query = req.query.query;
    const queryfile = req.query.queryFile;

    if (!query && !queryfile) {
        return res.status(400).json({ error: 'Missing query parameter' });
    }

    // Sanitize the filename to prevent command injection (basic check)
    if (!/^[\w.-]+$/.test(queryfile)) {
        return res.status(400).send('Invalid query file name');
    }

    // Create a unique cache file name based on the query
    let cacheFile = path.join(__dirname, `cache/${hash(query || queryfile)}.json`);
    
    if (fs.existsSync(cacheFile)) {
        return res.sendFile(cacheFile);
    }

    let dataPath = path.join(__dirname, '../data/output')
    let ontologyPath = path.join(__dirname, '../../ontology/diva.ttl')
    let thesaurusPath = path.join(__dirname, "../../ontology/thesaurus.ttl")

    let cmd = `corese query -i ${dataPath} -i ${ontologyPath} -i ${thesaurusPath} -i ${prov} -i ${dcat} -if ttl -of json `;
    if (queryfile)
        // Build the command to execute Corese
        cmd += `-q ${path.join(__dirname, '../sparql-examples', queryfile)}`
    else if (query)
        cmd += `-q "${query}"`

    // Execute the command
    exec(cmd, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return res.status(500).json({ error: error.message });
        }
        if (stderr) {
            console.error(`stderr: ${stderr}`);
            // Sometimes stderr includes warnings, not just errors
        }

        try {
            const json = JSON.parse(stdout);

            fs.mkdirSync('cache', { recursive: true });
        
            fs.writeFileSync(cacheFile, JSON.stringify(json, null, 2), 'utf-8');

            res.json(json);
        } catch (e) {
            res.status(500).json({ error: `Failed to parse JSON: ${e.message}\nRaw output:\n${stdout}` });
        }
    });
})

app.get('/sparql/', async function (req, res) {
    try {
        const endpoint = req.query.endpoint;
        const query = req.query.query;

        if (!endpoint || !query) {
            return res.status(400).json({ error: 'Missing endpoint or query parameter' });
        }

        let cacheFile = path.join(__dirname, `cache/${hash(endpoint, query)}.json`)
        if (fs.existsSync(cacheFile)) {
            return res.sendFile(cacheFile)
        }

        const response = await fetch(`${endpoint}?query=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: { 'Accept': 'application/sparql-results+json' },
        });

        if (!response.ok) {
            return res.status(response.status).json({
                error: `SPARQL endpoint returned status ${response.statusText}`
            });
        }

        const data = await response.json();

        fs.mkdirSync('cache', { recursive: true });
        
        console.log("Writing cache file:", cacheFile);
        fs.writeFileSync(cacheFile, JSON.stringify(data, null, 2), 'utf-8');

        res.json(data);
    } catch (error) {
        console.error('SPARQL proxy error:', error);
        res.status(500).json({ error: 'Proxy error', detail: error.message });
    }
})

// Hash function
function hash(...args) {
    return crypto.createHash('sha256').update(args.join('--')).digest('hex');
}



app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
})
