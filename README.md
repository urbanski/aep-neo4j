# Adversary Emulation Planner on Neo4j

This guide explains how to import the ATT&CK technique data from the Adversary Emulation Planner into Neo4j.

## Step 1: Generate CSV Files

Run the Python script to convert the JSON data to CSV format:

```bash
python3 convert_to_neo4j.py
```

This will create a `neo4j_import` directory with the following CSV files:
- `techniques.csv`: All ATT&CK techniques
- `capabilities.csv`: Tactical goals techniques can provide
- `mitigations.csv`: Mitigations for techniques
- `provides_relationships.csv`: What capabilities techniques provide
- `requires_relationships.csv`: What capabilities techniques require
- `mitigation_relationships.csv`: Which techniques mitigations address
- `conditional_provides.csv`: Conditional capabilities techniques can provide
- `relevant_for.csv`: System types techniques are relevant for
- `child_relationships.csv`: Subtechnique relationships

## Step 2: Import into Neo4j Desktop

1. Launch Neo4j Desktop and create a new database (or open an existing one)
2. Click on the database you want to use, then click "Manage"
3. Select "Open Folder" and navigate to "Import"
4. Copy all the CSV files from the `neo4j_import` directory to this import folder

## Step 3: Run Import Cypher Queries

Open Neo4j Browser for your database and run the following Cypher queries:

```cypher
// Create constraints
CREATE CONSTRAINT technique_id IF NOT EXISTS FOR (t:Technique) REQUIRE t.techniqueId IS UNIQUE;
CREATE CONSTRAINT capability_id IF NOT EXISTS FOR (c:Capability) REQUIRE c.capabilityId IS UNIQUE;
CREATE CONSTRAINT mitigation_id IF NOT EXISTS FOR (m:Mitigation) REQUIRE m.mitigationId IS UNIQUE;

// Import techniques
LOAD CSV WITH HEADERS FROM 'file:///techniques.csv' AS row
CREATE (t:Technique {
  techniqueId: row.`techniqueId:ID`,
  name: row.name
})
WITH t, row
WHERE row.`agent_class:string[]` <> ''
SET t.agent_class = split(row.`agent_class:string[]`, ';');

// Import capabilities
LOAD CSV WITH HEADERS FROM 'file:///capabilities.csv' AS row
CREATE (c:Capability {
  capabilityId: row.`capabilityId:ID`,
  name: row.name
});

// Import mitigations
LOAD CSV WITH HEADERS FROM 'file:///mitigations.csv' AS row
CREATE (m:Mitigation {
  mitigationId: row.`mitigationId:ID`,
  name: row.name
});

// Import PROVIDES relationships
LOAD CSV WITH HEADERS FROM 'file:///provides_relationships.csv' AS row
MATCH (t:Technique {techniqueId: row.`:START_ID`})
MATCH (c:Capability {capabilityId: row.`:END_ID`})
CREATE (t)-[:PROVIDES]->(c);

// Import REQUIRES relationships
LOAD CSV WITH HEADERS FROM 'file:///requires_relationships.csv' AS row
MATCH (t:Technique {techniqueId: row.`:START_ID`})
MATCH (c:Capability {capabilityId: row.`:END_ID`})
CREATE (t)-[:REQUIRES]->(c);

// Import MITIGATES relationships
LOAD CSV WITH HEADERS FROM 'file:///mitigation_relationships.csv' AS row
MATCH (m:Mitigation {mitigationId: row.`:START_ID`})
MATCH (t:Technique {techniqueId: row.`:END_ID`})
CREATE (m)-[:MITIGATES]->(t);

// Import CONDITIONALLY_PROVIDES relationships
LOAD CSV WITH HEADERS FROM 'file:///conditional_provides.csv' AS row
MATCH (t:Technique {techniqueId: row.`:START_ID`})
MATCH (c:Capability {capabilityId: row.`:END_ID`})
CREATE (t)-[:CONDITIONALLY_PROVIDES {condition: row.condition}]->(c);

// Import RELEVANT_FOR relationships
LOAD CSV WITH HEADERS FROM 'file:///relevant_for.csv' AS row
MATCH (t:Technique {techniqueId: row.`:START_ID`})
CREATE (s:SystemType {name: row.systemType})
CREATE (t)-[:RELEVANT_FOR]->(s);

// Merge SystemTypes to avoid duplicates
MATCH (s:SystemType)
WITH s.name AS name, COLLECT(s) AS nodes
WHERE SIZE(nodes) > 1
WITH nodes[0] AS keepNode, nodes[1..] AS duplicateNodes
UNWIND duplicateNodes AS duplicateNode
MATCH (duplicateNode)<-[r]-(source)
CREATE (source)-[newRel:RELEVANT_FOR]->(keepNode)
DELETE r, duplicateNode;

// Import HAS_SUBTECHNIQUE relationships
LOAD CSV WITH HEADERS FROM 'file:///child_relationships.csv' AS row
MATCH (parent:Technique {techniqueId: row.`:START_ID`})
MATCH (child:Technique {techniqueId: row.`:END_ID`})
CREATE (parent)-[:HAS_SUBTECHNIQUE]->(child);
```

## Step 4: Verify the Import

Run the following queries to check the data was imported correctly:

```cypher
// Count nodes by label
MATCH (n) RETURN labels(n) AS label, COUNT(n) AS count;

// Check relationships
MATCH ()-[r]->() RETURN type(r) AS relationship, COUNT(r) AS count;

// Sample technique and its relationships
MATCH (t:Technique {techniqueId: 'T1027'})
RETURN t.name AS technique,
[(t)-[:PROVIDES]->(c) | c.name] AS provides,
[(t)-[:REQUIRES]->(c) | c.name] AS requires,
[(m)-[:MITIGATES]->(t) | m.name] AS mitigations,
[(t)-[:RELEVANT_FOR]->(s) | s.name] AS relevant_for;
```

## Step 5: Useful Queries for Analysis

```cypher
// Find potential attack paths (techniques that provide capabilities that other techniques require)
MATCH (t1:Technique)-[:PROVIDES]->(c:Capability)<-[:REQUIRES]-(t2:Technique)
RETURN t1.techniqueId AS source, t1.name AS sourceName, 
       c.capabilityId AS capability, 
       t2.techniqueId AS target, t2.name AS targetName
LIMIT 20;

// Find techniques with the most available next steps
MATCH (t1:Technique)-[:PROVIDES]->(c:Capability)<-[:REQUIRES]-(t2:Technique)
WITH t1, COUNT(DISTINCT t2) AS next_steps
RETURN t1.techniqueId, t1.name, next_steps
ORDER BY next_steps DESC
LIMIT 10;

// Identify critical mitigations (those that mitigate techniques providing the most capabilities)
MATCH (m:Mitigation)-[:MITIGATES]->(t:Technique)-[:PROVIDES]->(c:Capability)
WITH m, COUNT(DISTINCT c) AS blocked_capabilities
RETURN m.mitigationId, m.name, blocked_capabilities
ORDER BY blocked_capabilities DESC
LIMIT 10;
```

## Visualization

Use Neo4j's built-in visualization capabilities to explore the graph:

```cypher
// Visualize a technique with its relationships
MATCH (t:Technique {techniqueId: 'T1027'})
OPTIONAL MATCH (t)-[:PROVIDES]->(c:Capability)
OPTIONAL MATCH (t)-[:REQUIRES]->(c2:Capability)
OPTIONAL MATCH (m:Mitigation)-[:MITIGATES]->(t)
RETURN t, c, c2, m LIMIT 50;

// Visualize attack paths starting from a specific technique
MATCH path = (t:Technique {techniqueId: 'T1566'})-[:PROVIDES]->(:Capability)<-[:REQUIRES]-(:Technique)-[:PROVIDES]->(:Capability)<-[:REQUIRES]-(:Technique)
RETURN path LIMIT 25;
```
