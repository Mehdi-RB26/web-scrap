// File: backend/server.js

const express = require('express');
const { MongoClient } = require('mongodb');
const cors = require('cors');
require('dotenv').config(); // Load variables from .env file

// --- Configuration ---
const app = express();
const port = 8000; // The port our backend will run on
const mongoUri = process.env.MONGO_URI;

// --- Middleware ---
// Enable CORS to allow our React app to make requests to this server
app.use(cors());

// --- Database Connection ---
if (!mongoUri) {
  console.error("FATAL ERROR: MONGO_URI is not defined in your .env file.");
  process.exit(1); // Exit the application
}

const client = new MongoClient(mongoUri);
let collection; // We will store the articles collection here

async function connectToDatabase() {
  try {
    await client.connect();
    // Use the default database specified in your MONGO_URI
    const db = client.db(); 
    collection = db.collection('articles');
    console.log(`✅ Successfully connected to MongoDB database: ${db.databaseName}`);
  } catch (err) {
    console.error("❌ Failed to connect to MongoDB", err);
    process.exit(1);
  }
}

// --- API Endpoint ---
// This is the URL our React app will fetch data from
app.get('/api/articles', async (req, res) => {
  if (!collection) {
    return res.status(500).json({ error: "Database connection not established." });
  }

  try {
    const articles = await collection
      .find({}) // Get all documents
      .sort({ publication_date: -1 }) // Sort by newest first
      .toArray();
    res.json(articles); // Send the articles as a JSON response
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch articles.' });
  }
});


// --- Start the Server ---
async function startServer() {
  await connectToDatabase();
  app.listen(port, () => {
    console.log(`🚀 Server is running on http://localhost:${port}`);
  });
}

startServer();