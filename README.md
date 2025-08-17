# Langchain Project to Convert Natural Language to SQL queries


## Table of Contents
1. General Info
2. Technology Used

## General Info
This project aims on conversion of Natural Language questions of the users to SQL queries, extracting the data based on those queries and giving the output in Natural Language.

I recently developed an intelligent chatbot that seamlessly converts natural language queries into SQL statements and executes them on a database, using a powerful orchestration of custom AI agents and a Modular Control Plane (MCP). For this project, I used dummy ERP system data to simulate real-world business scenarios and test the chatbot’s capabilities.

Here’s how it works:

 1. User inputs a query.

 2. LLM-1 analyzes the query and crafts an initial response.

 3. LLM-2 evaluates that response to determine whether it’s a regular answer or a SQL query.

 4. If SQL is detected, LLM-2 validates it against the database schema metadata loaded in Redis and checks SQL syntax. If the query is flawed, it rewrites it accordingly.

 5. Finally, the validated SQL query is executed on the database through tools managed by the MCP.

## Technology Used

1. Langchain
2. Custom AI Agents 
3. PostgreSQL hosted on GCP.
4. MCP tools
