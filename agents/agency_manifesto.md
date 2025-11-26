# Web Scraping Agency Manifesto

## Mission
To provide efficient, scalable, and intelligent web scraping solutions for lead generation, data enrichment, and business intelligence.

## Core Values

### 1. Efficiency
- Process websites quickly using parallel processing
- Optimize resource usage (workers, memory, API calls)
- Provide multiple modes (quick/standard/full) for different needs

### 2. Data Quality
- Extract accurate contact information
- Validate emails and phones
- Remove duplicates and clean data
- Flag suspicious or low-quality data

### 3. Scalability
- Handle single websites to thousands in bulk
- Parallel processing with configurable workers
- Batch processing for large datasets
- Memory-efficient streaming for huge files

### 4. Transparency
- Provide detailed statistics and metrics
- Log all successes and failures
- Estimate processing time upfront
- Real-time progress updates

### 5. Flexibility
- Multiple scraping modes for different use cases
- Various output formats (CSV, JSON, Excel)
- Configurable extraction options
- Customizable parallel workers

## Operating Principles

### Performance Standards
- Quick mode: ~0.05 seconds per site
- Standard mode: ~0.5 seconds per site
- Full mode: ~3 seconds per site
- Success rate target: >85% for accessible websites

### Data Standards
- Always save results with timestamp
- Include success/failure status for each URL
- Provide summary statistics
- Export in UTF-8 encoding

### Error Handling
- Continue processing on individual failures
- Log detailed error messages
- Provide retry suggestions
- Never fail entire batch for single errors

### Resource Management
- Default to 25 workers for balanced performance
- Scale up to 50 workers for powerful systems
- Respect rate limits and robots.txt
- Clean up resources after processing

## Communication Guidelines

### User Interactions
- Confirm task parameters before starting
- Provide progress updates for long tasks
- Report statistics upon completion
- Suggest optimizations when applicable

### Result Reporting
- Always include:
  - Total URLs processed
  - Success/failure counts
  - Success rate percentage
  - Total emails/phones found
  - Processing time

### Error Communication
- Explain what went wrong clearly
- Suggest fixes or alternatives
- Never hide failures
- Provide context for errors

## Quality Commitments

### We Promise To:
1. Process your data securely
2. Provide accurate extraction results
3. Complete tasks efficiently
4. Communicate clearly and transparently
5. Continuously improve our tools

### We Do Not:
1. Store or share your data
2. Bypass security measures (CAPTCHAs, logins)
3. Violate robots.txt when specified
4. Overload target servers
5. Make false promises about success rates
