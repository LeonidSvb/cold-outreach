#!/usr/bin/env node
/**
 * Apollo ICP Analyzer
 * Version: 1.0.0 | Created: 2025-11-03
 *
 * PURPOSE:
 * Analyze Apollo CSV data and add ICP scoring for call center prospects.
 * Validates company fit against call center profile criteria.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const CONFIG = {
  INPUT_FILE: 'C:/Users/79818/Downloads/call centers US UK Aus 10-100 - 10-50.csv',
  OUTPUT_DIR: 'C:/Users/79818/Desktop/Outreach - new/modules/apollo/results',
  BATCH_SIZE: 200,
};

const LEGAL_SUFFIXES = [
  /\s+LLC\s*$/i, /\s+Inc\.\s*$/i, /\s+Inc\s*$/i,
  /\s+Incorporated\s*$/i, /\s+Ltd\.\s*$/i, /\s+Ltd\s*$/i,
  /\s+Limited\s*$/i, /\s+Corp\.\s*$/i, /\s+Corp\s*$/i,
  /\s+Corporation\s*$/i, /\s+Co\.\s*$/i, /\s+Co\s*$/i,
  /\s+Company\s*$/i, /\s+PLC\s*$/i, /\s+Pty\s*$/i,
  /\s+GmbH\s*$/i, /\s+AG\s*$/i, /\s+SRL\s*$/i,
  /\s+SARL\s*$/i
];

const CALL_CENTER_KEYWORDS = [
  'call center', 'contact center', 'call centre', 'contact centre',
  'telemarketing', 'outbound call', 'inbound call', 'telefundraising',
  'telesales', 'phone sales', 'dialer', 'bpo', 'business process outsourcing',
  'customer contact', 'customer service', 'phone support', 'call handling',
  'call operations', 'call management', 'call center operations', 'outsourcing'
];

const LOCATION_ABBREVIATIONS = {
  'New York': 'NYC', 'Los Angeles': 'LA', 'San Francisco': 'SF',
  'Washington': 'DC', 'Boston': 'Boston', 'Miami': 'Miami',
  'Chicago': 'Chicago', 'Atlanta': 'Atlanta', 'Dallas': 'Dallas',
  'Houston': 'Houston', 'Phoenix': 'Phoenix', 'Philadelphia': 'Philadelphia',
  'Seattle': 'Seattle', 'Austin': 'Austin', 'Denver': 'Denver',
  'United States': 'US', 'United Kingdom': 'UK', 'Australia': 'Aus',
  'New Zealand': 'NZ', 'Canada': 'Canada', 'India': 'India',
  'Philippines': 'Philippines', 'Mexico': 'Mexico'
};

const US_STATE_ABBREVIATIONS = {
  'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
  'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
  'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
  'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
  'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
  'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
  'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
  'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
  'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
  'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
  'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
  'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
  'Wisconsin': 'WI', 'Wyoming': 'WY'
};

function normalizeCompanyName(name) {
  if (!name || name === '') return '';

  let normalized = String(name).trim();

  for (const suffix of LEGAL_SUFFIXES) {
    normalized = normalized.replace(suffix, '');
  }

  return normalized.trim();
}

function normalizeLocation(city, state, country) {
  city = String(city || '').trim();
  state = String(state || '').trim();
  country = String(country || '').trim();

  if (!city && !state && !country) return '';

  if (LOCATION_ABBREVIATIONS[city]) {
    return LOCATION_ABBREVIATIONS[city];
  }

  if (city) {
    const cityClean = city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
    if (cityClean.length <= 8) return cityClean;
    if (LOCATION_ABBREVIATIONS[cityClean]) return LOCATION_ABBREVIATIONS[cityClean];
    return cityClean;
  }

  if (state) {
    if (state.length === 2) return state.toUpperCase();
    if (US_STATE_ABBREVIATIONS[state]) return US_STATE_ABBREVIATIONS[state];
    if (state.length <= 8) return state;
    return state;
  }

  if (country) {
    if (LOCATION_ABBREVIATIONS[country]) return LOCATION_ABBREVIATIONS[country];
    return country;
  }

  return '';
}

function hasCallCenterKeywords(companyName, industry, headline, keywords) {
  const text = `${companyName} ${industry} ${headline} ${keywords}`.toLowerCase();

  for (const keyword of CALL_CENTER_KEYWORDS) {
    if (text.includes(keyword)) {
      return true;
    }
  }

  return false;
}

function scoreIcp(companyName, industry, headline, keywords, title, estimatedEmployees) {
  companyName = String(companyName || '').toLowerCase();
  industry = String(industry || '').toLowerCase();
  headline = String(headline || '').toLowerCase();
  keywords = String(keywords || '').toLowerCase();
  title = String(title || '').toLowerCase();

  const estEmp = parseInt(estimatedEmployees) || 0;

  if (industry.includes('outsourc') || industry.includes('offshoring') || industry.includes('bpo')) {
    return {
      score: 2,
      reasoning: 'Outsourcing/BPO industry indicates strong call center operations. Likely handles high-volume customer interactions.'
    };
  }

  if (hasCallCenterKeywords(companyName, industry, headline, keywords)) {
    return {
      score: 2,
      reasoning: 'Clear call center indicators found in company data. Keywords match call center operations profile.'
    };
  }

  if ((industry.includes('contact') || industry.includes('customer service') || industry.includes('telecom')) && estEmp >= 10) {
    return {
      score: 1,
      reasoning: `Customer contact/service industry with ${estEmp}+ employees. Likely phone-based operations but not explicitly confirmed.`
    };
  }

  if ((title.includes('call') || title.includes('contact') || title.includes('customer')) && estEmp >= 10) {
    return {
      score: 1,
      reasoning: 'Title suggests customer contact focus, but insufficient confirmation of phone-based operations.'
    };
  }

  if (estEmp >= 50 && (industry.includes('service') || industry.includes('support') || industry.includes('customer'))) {
    return {
      score: 1,
      reasoning: `Large company (${estEmp}+ employees) in service/support industry. Possible call center operations but unclear.`
    };
  }

  return {
    score: 0,
    reasoning: 'No clear call center indicators found in company profile, industry, or keywords.'
  };
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let insideQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (insideQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === ',' && !insideQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  result.push(current);
  return result;
}

async function main() {
  console.log('Starting Apollo ICP Analysis');
  console.log(`Input file: ${CONFIG.INPUT_FILE}`);

  if (!fs.existsSync(CONFIG.INPUT_FILE)) {
    console.error(`ERROR: File not found: ${CONFIG.INPUT_FILE}`);
    process.exit(1);
  }

  // Create output directory
  if (!fs.existsSync(CONFIG.OUTPUT_DIR)) {
    fs.mkdirSync(CONFIG.OUTPUT_DIR, { recursive: true });
  }

  // Read and parse CSV
  const fileContent = fs.readFileSync(CONFIG.INPUT_FILE, 'utf-8');
  const lines = fileContent.split('\n');

  console.log(`Loaded CSV: ${lines.length - 1} total rows (excluding header)`);

  // Parse header
  const headerLine = lines[0];
  const headers = parseCSVLine(headerLine);
  const headerIndex = {};
  headers.forEach((h, i) => {
    headerIndex[h] = i;
  });

  console.log(`Found ${headers.length} columns`);

  // Process data
  const allRows = [];
  const stats = { score_2: 0, score_1: 0, score_0: 0 };

  for (let lineNum = 1; lineNum < lines.length; lineNum++) {
    if (lineNum % 500 === 0) {
      console.log(`Processed ${lineNum} rows...`);
    }

    const line = lines[lineNum].trim();
    if (!line) continue;

    const fields = parseCSVLine(line);
    const row = {};

    // Map fields to header
    headers.forEach((header, i) => {
      row[header] = fields[i] || '';
    });

    // Score ICP
    const icpResult = scoreIcp(
      row['company_name'],
      row['industry'],
      row['headline'],
      row['keywords'],
      row['title'],
      row['estimated_num_employees']
    );

    // Add new columns
    row['normalized_company_name'] = normalizeCompanyName(row['company_name']);
    row['normalized_location'] = normalizeLocation(row['city'], row['state'], row['country']);
    row['icp_score'] = icpResult.score;
    row['reasoning'] = icpResult.reasoning;

    // Update stats
    stats[`score_${icpResult.score}`]++;

    allRows.push(row);
  }

  console.log(`All rows processed: ${allRows.length} total`);
  console.log(`ICP Score Distribution: Score 2: ${stats.score_2}, Score 1: ${stats.score_1}, Score 0: ${stats.score_0}`);

  // Add new column headers
  headers.push('normalized_company_name');
  headers.push('normalized_location');
  headers.push('icp_score');
  headers.push('reasoning');

  // Write CSV
  const timestamp = new Date().toISOString().replace(/[:-]/g, '').replace(/\./g, '').slice(0, 15);
  const outputFile = path.join(CONFIG.OUTPUT_DIR, `apollo_icp_analyzed_${timestamp}.csv`);

  // Build CSV content
  let csvContent = headers.map(h => `"${h}"`).join(',') + '\n';

  for (const row of allRows) {
    const line = headers.map(h => {
      const value = row[h] || '';
      const escaped = String(value).replace(/"/g, '""');
      return `"${escaped}"`;
    }).join(',');
    csvContent += line + '\n';
  }

  fs.writeFileSync(outputFile, csvContent, 'utf-8');
  console.log(`Results saved to: ${outputFile}`);

  console.log('\n' + '='.repeat(60));
  console.log('АНАЛИЗ ЗАВЕРШЁН');
  console.log('='.repeat(60));
  console.log(`Результаты сохранены: ${outputFile}`);
  console.log(`\nРаспределение ICP scores:`);
  console.log(`  Score 2 (Perfect Fit): ${stats.score_2} компаний`);
  console.log(`  Score 1 (Maybe): ${stats.score_1} компаний`);
  console.log(`  Score 0 (Not a Fit): ${stats.score_0} компаний`);
  console.log('='.repeat(60) + '\n');

  return { outputFile, stats };
}

main().catch(err => {
  console.error('Script failed:', err);
  process.exit(1);
});
