#!/usr/bin/env python3
"""
Create interactive HTML viewer for HVAC data
"""

import pandas as pd
from pathlib import Path

# Read enriched data
df = pd.read_csv('data/processed/hvac_websites_enriched_20251109_145423.csv')

# Filter successful scrapes
df_success = df[df['status'] == 'SUCCESS'].copy()

# Create HTML
html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HVAC Companies - Texas</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }
        .stat {
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 4px;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
        }
        .controls {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filters {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        input, select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        input[type="text"] {
            flex: 1;
            min-width: 250px;
        }
        select {
            min-width: 200px;
        }
        .table-container {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e5e7eb;
            position: sticky;
            top: 0;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .company-name {
            font-weight: 600;
            color: #1f2937;
        }
        .email {
            color: #2563eb;
            word-break: break-all;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .badge-residential {
            background: #dbeafe;
            color: #1e40af;
        }
        .badge-commercial {
            background: #fef3c7;
            color: #92400e;
        }
        .badge-both {
            background: #d1fae5;
            color: #065f46;
        }
        .badge-general {
            background: #e5e7eb;
            color: #374151;
        }
        .services {
            font-size: 13px;
            color: #666;
        }
        .rating {
            color: #f59e0b;
            font-weight: 600;
        }
        .copy-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .copy-btn:hover {
            background: #1d4ed8;
        }
        .no-results {
            padding: 40px;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Texas HVAC Companies</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Total Companies</div>
                <div class="stat-value" id="total-count">""" + str(len(df_success)) + """</div>
            </div>
            <div class="stat">
                <div class="stat-label">With Emails</div>
                <div class="stat-value">""" + str(len(df_success)) + """</div>
            </div>
            <div class="stat">
                <div class="stat-label">Avg Rating</div>
                <div class="stat-value">""" + f"{df_success['rating'].mean():.1f}" + """</div>
            </div>
        </div>
    </div>

    <div class="controls">
        <div class="filters">
            <input type="text" id="search" placeholder="Search by company name...">
            <select id="city-filter">
                <option value="">All Cities</option>
"""

# Add city options
cities = df_success['city'].dropna().unique()
for city in sorted(cities):
    html += f'                <option value="{city}">{city}</option>\n'

html += """
            </select>
            <select id="spec-filter">
                <option value="">All Specializations</option>
"""

# Add specialization options
specs = df_success['specialization'].dropna().unique()
for spec in sorted(specs):
    html += f'                <option value="{spec}">{spec}</option>\n'

html += """
            </select>
        </div>
    </div>

    <div class="table-container">
        <table id="companies-table">
            <thead>
                <tr>
                    <th>Company</th>
                    <th>City</th>
                    <th>Email</th>
                    <th>Specialization</th>
                    <th>Services</th>
                    <th>Rating</th>
                    <th>Phone</th>
                </tr>
            </thead>
            <tbody id="table-body">
"""

# Add table rows
for idx, row in df_success.iterrows():
    # Determine badge class
    spec = row['specialization']
    if 'Residential & Commercial' in spec:
        badge_class = 'badge-both'
    elif 'Residential' in spec:
        badge_class = 'badge-residential'
    elif 'Commercial' in spec:
        badge_class = 'badge-commercial'
    else:
        badge_class = 'badge-general'

    # Truncate email if too long
    email = str(row['emails'])[:50] if pd.notna(row['emails']) else ''

    html += f"""
                <tr data-city="{row['city']}" data-spec="{spec}" data-name="{row['company_name'].lower()}">
                    <td class="company-name">{row['company_name']}</td>
                    <td>{row['city']}</td>
                    <td class="email">
                        {email}
                        <button class="copy-btn" onclick="copyEmail('{email}')">Copy</button>
                    </td>
                    <td><span class="badge {badge_class}">{spec}</span></td>
                    <td class="services">{row['services']}</td>
                    <td class="rating">{row['rating']} ({int(row['reviews'])})</td>
                    <td>{row['phone']}</td>
                </tr>
"""

html += """
            </tbody>
        </table>
        <div id="no-results" class="no-results" style="display: none;">
            No companies found matching your filters
        </div>
    </div>

    <script>
        const searchInput = document.getElementById('search');
        const cityFilter = document.getElementById('city-filter');
        const specFilter = document.getElementById('spec-filter');
        const tableBody = document.getElementById('table-body');
        const noResults = document.getElementById('no-results');
        const totalCount = document.getElementById('total-count');

        function filterTable() {
            const searchTerm = searchInput.value.toLowerCase();
            const selectedCity = cityFilter.value;
            const selectedSpec = specFilter.value;

            const rows = tableBody.getElementsByTagName('tr');
            let visibleCount = 0;

            for (let row of rows) {
                const name = row.getAttribute('data-name');
                const city = row.getAttribute('data-city');
                const spec = row.getAttribute('data-spec');

                const matchesSearch = name.includes(searchTerm);
                const matchesCity = !selectedCity || city === selectedCity;
                const matchesSpec = !selectedSpec || spec === selectedSpec;

                if (matchesSearch && matchesCity && matchesSpec) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            }

            totalCount.textContent = visibleCount;
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            tableBody.style.display = visibleCount === 0 ? 'none' : '';
        }

        function copyEmail(email) {
            navigator.clipboard.writeText(email);
            alert('Email copied: ' + email);
        }

        searchInput.addEventListener('input', filterTable);
        cityFilter.addEventListener('change', filterTable);
        specFilter.addEventListener('change', filterTable);
    </script>
</body>
</html>
"""

# Save HTML
output_path = Path('hvac_viewer.html')
output_path.write_text(html, encoding='utf-8')

print(f"HTML viewer created: {output_path.absolute()}")
print(f"\nOpen in browser to view {len(df_success)} companies!")
