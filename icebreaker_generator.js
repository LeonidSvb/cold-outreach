#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { createReadStream, createWriteStream } = require('fs');
const { parse } = require('csv-parse');
const { stringify } = require('csv-stringify');

// Load environment variables
try {
  require('dotenv').config({ path: path.join(__dirname, '.env') });
} catch (e) {
  // dotenv not available, continue with environment variables
}

// Configure paths
const CSV_PATH = 'C:\\Users\\79818\\Downloads\\call centers US UK Aus 10-100 - 10-50.csv';
const OUTPUT_DIR = path.join(__dirname, 'data', 'processed');
const OUTPUT_FILE = path.join(OUTPUT_DIR, `apollo_icebreaker_analyzed_${Date.now()}.csv`);
const LOG_FILE = path.join(OUTPUT_DIR, 'generator.log');

// Ensure directories exist
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// Logging
const logStream = fs.createWriteStream(LOG_FILE, { encoding: 'utf-8' });

function log(msg) {
  console.log(msg);
  logStream.write(msg + '\n');
}

log('='.repeat(60));
log('ICEBREAKER GENERATOR (Node.js)');
log('='.repeat(60));

// Import Anthropic
let Anthropic;
try {
  Anthropic = require('@anthropic-ai/sdk');
  log('[OK] Anthropic SDK loaded');
} catch (e) {
  log(`[FAIL] Anthropic SDK not found: ${e.message}`);
  log('Installing via npm...');
  const { execSync } = require('child_process');
  try {
    execSync('npm install @anthropic-ai/sdk', { stdio: 'inherit' });
    Anthropic = require('@anthropic-ai/sdk');
    log('[OK] Anthropic SDK installed');
  } catch (e2) {
    log(`[FAIL] Could not install: ${e2.message}`);
    process.exit(1);
  }
}

// Initialize client
const apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) {
  log('[FAIL] ANTHROPIC_API_KEY not set');
  log(`Available env vars: ${Object.keys(process.env).filter(k => k.includes('ANTHROPIC')).join(', ')}`);
  process.exit(1);
}

const client = new Anthropic({ apiKey });
log('[OK] Anthropic client initialized');

async function generateIcebreaker(fullName, companyName, title, headline, city) {
  const prompt = `You are an outreach message generator.
Your role: create short, casual, human-sounding icebreaker messages for LinkedIn-style outreach.
Goal: make the recipient feel recognized for their work without sounding pushy or overly formal.

Your task:
- If "full_name" looks like a company (contains words such as Company, Inc, LLC, Ltd, Group, Realty, Properties, Brokers, UAE, Dubai, Abu Dhabi):
    -> Output ONLY: its a company

- Else (if "full_name" is a person):
    1. Extract firstName = first word of full_name.
    2. Normalize company_name into shortCompany:
        - If ALL CAPS -> convert to Title Case (only first letter uppercase).
        - Remove corporate suffixes: Properties, Realty, Group, Brokers, LLC, Ltd, Inc, UAE, Dubai, Abu Dhabi.
        - Remove apostrophes or special symbols.
    3. Normalize region into shortRegion:
        - Dubai, Abu Dhabi -> Dubai
        - San Francisco -> SF
        - New York City -> NYC
        - Else keep original.
    4. Generate opening = pick randomly, in casual tone:
        - love how you
        - really like how you
        - awesome to see you
        - impressed by how you
        - great track with how you
        - cool to see you
    5. specializationPhrase:
        - Look at headline or title.
        - If clear keyword (luxury, sales, marketing, engineering, talent acquisition, product, design, etc.) -> rewrite naturally as an action (2-3 words).
            * Example: "Luxury Consultant" -> "drive luxury sales"
            * "Marketing Manager" -> "lead marketing"
            * "Talent Acquisition" -> "grow teams"
            * "Software Engineer" -> "build products"
        - If generic title -> simplify to meaningful action:
            * "Consultant" -> "work with clients"
            * "Broker" -> "push sales"
            * "Analyst" -> "dig into insights"
        - If nothing useful -> fallback: "bring industry experience".
    6. regionPhrase = pick randomly:
        - I'm also in the {shortRegion} market
        - I work across {shortRegion} as well
        - I'm active in {shortRegion} too
        - I also focus on {shortRegion}
    7. closingPhrase = pick randomly:
        - Wanted to run something by you.
        - Thought I'd share an idea with you.
        - Had something you might find interesting.
        - Figured I'd reach out quickly.

Final Output (always one line, no labels, no JSON):
Hey {firstName}, {opening} {specializationPhrase} at {shortCompany} - {regionPhrase}. {closingPhrase}

Context for this row:
full_name: ${fullName}
company_name: ${companyName}
title: ${title}
headline: ${headline}
city: ${city}`;

  try {
    const response = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 200,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ]
    });

    return response.content[0].text.trim();
  } catch (e) {
    return `ERROR: ${e.message.substring(0, 40)}`;
  }
}

async function main() {
  log('[1/3] Loading CSV...');

  const rows = [];
  const errorHandler = (err) => {
    log(`[ERROR] CSV Parse: ${err.message}`);
    process.exit(1);
  };

  await new Promise((resolve, reject) => {
    createReadStream(CSV_PATH, { encoding: 'utf-8' })
      .pipe(parse({ columns: true }))
      .on('data', (row) => rows.push(row))
      .on('error', errorHandler)
      .on('end', resolve);
  });

  log(`[OK] Loaded ${rows.length} rows`);

  // Process rows in batches
  log('\n[2/3] Generating icebreakers...');
  const BATCH_SIZE = 50;
  const startTime = Date.now();

  let successCount = 0;
  let companyCount = 0;
  let errorCount = 0;

  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const batchEnd = Math.min(i + BATCH_SIZE, rows.length);
    const batchSize = batchEnd - i;

    log(`\n[BATCH ${batchNum}] Processing rows ${i + 1}-${batchEnd}...`);
    const batchStart = Date.now();

    // Process batch in parallel
    const batchPromises = [];
    for (let j = i; j < batchEnd; j++) {
      const row = rows[j];
      const promise = generateIcebreaker(
        row.full_name || '',
        row.company_name || '',
        row.title || '',
        row.headline || '',
        row.city || ''
      ).then((icebreaker) => {
        rows[j].icebreaker = icebreaker;

        if (icebreaker.includes('ERROR')) {
          errorCount++;
        } else if (icebreaker.toLowerCase().includes('its a company')) {
          companyCount++;
        } else {
          successCount++;
        }

        return icebreaker;
      });

      batchPromises.push(promise);
    }

    await Promise.all(batchPromises);

    const batchTime = ((Date.now() - batchStart) / 1000).toFixed(1);
    log(`  Completed in ${batchTime}s | Success: ${successCount}, Companies: ${companyCount}, Errors: ${errorCount}`);
  }

  const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
  log(`\n[OK] Generation complete in ${totalTime}s`);

  // Save CSV
  log('\n[3/3] Saving results...');

  const csvOutput = createWriteStream(OUTPUT_FILE);
  const stringifier = stringify({ header: true, columns: Object.keys(rows[0]) });

  stringifier.pipe(csvOutput);

  for (const row of rows) {
    stringifier.write(row);
  }

  stringifier.end();

  await new Promise((resolve, reject) => {
    csvOutput.on('finish', resolve);
    csvOutput.on('error', reject);
  });

  log(`[OK] Saved to ${OUTPUT_FILE}`);

  // Stats
  log('\n' + '='.repeat(60));
  log('FINAL STATISTICS');
  log('='.repeat(60));
  log(`Total rows: ${rows.length}`);
  log(`Successful: ${successCount}`);
  log(`Companies detected: ${companyCount}`);
  log(`Errors: ${errorCount}`);
  log(`Total time: ${totalTime}s`);
  log(`Output: ${OUTPUT_FILE}`);
  log('='.repeat(60));

  // Sample
  log('\nSAMPLE ICEBREAKERS (first 10):');
  let sampleCount = 0;
  for (const row of rows) {
    if (!row.icebreaker.includes('ERROR') && !row.icebreaker.toLowerCase().includes('its a company')) {
      sampleCount++;
      log(`\n[${sampleCount}] ${row.full_name} @ ${row.company_name}`);
      log(`    ${row.icebreaker}`);
      if (sampleCount >= 10) break;
    }
  }

  logStream.end();
  process.exit(0);
}

main().catch((err) => {
  log(`FATAL ERROR: ${err.message}`);
  logStream.end();
  process.exit(1);
});
