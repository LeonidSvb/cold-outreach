# Scraping Module - AI Prompts

## Version History
- v2.0.0 (2025-09-25): Complete modular scraping system with Apify integration
- v1.0.0 (2025-01-19): Legacy embedded prompts in scripts

---

## PAGE_CLASSIFICATION

Used in: page_prioritizer.py
Purpose: Classify web pages by outreach intelligence value for cold outreach campaigns

```
# WEB PAGE OUTREACH INTELLIGENCE ANALYSIS

You are an expert at analyzing web pages for B2B cold outreach intelligence gathering. Analyze the provided web page content and classify its value for cold outreach personalization.

## PAGE DATA:
**URL:** {page_url}
**Title:** {page_title}
**Content Length:** {content_length} characters
**Domain:** {domain}

**PAGE CONTENT:**
{page_content}

## ANALYSIS REQUIREMENTS:

### 1. OUTREACH VALUE CLASSIFICATION
Classify this page into ONE of these categories:

**HIGH VALUE (Score 8-10):**
- About/Team pages with leadership information
- Case studies with specific client results
- Recent news/achievements with dates
- Awards/recognition with details
- Company culture/values insights

**MEDIUM VALUE (Score 5-7):**
- Services pages with unique positioning
- General company history
- Basic team information without details
- Industry insights/blog posts
- Partnership announcements

**LOW VALUE (Score 2-4):**
- Generic service descriptions
- FAQ pages
- Technical documentation
- Privacy/legal pages
- Product specifications only

**NO VALUE (Score 0-1):**
- Error pages
- Login/registration forms
- Cart/checkout pages
- Pure navigation pages
- Duplicate content

### 2. INTELLIGENCE EXTRACTION
For pages scored 5+, extract specific insights:

**PERSONALIZATION OPPORTUNITIES:**
- Company achievements with dates
- Leadership names and backgrounds
- Recent growth/expansion news
- Unique company positioning
- Client success stories
- Industry awards/recognition

**CONVERSATION STARTERS:**
- Recent milestones or changes
- Interesting company culture elements
- Notable partnerships or clients
- Growth indicators
- Market positioning statements

### 3. CONFIDENCE ASSESSMENT
Rate confidence in the analysis (1-10):
- 10: Crystal clear, abundant specific information
- 7-9: Good information, some specific details
- 4-6: Moderate information, mostly general
- 1-3: Limited information, unclear content

## OUTPUT FORMAT:
Provide structured JSON response:

{{
  "classification": {{
    "category": "HIGH_VALUE|MEDIUM_VALUE|LOW_VALUE|NO_VALUE",
    "score": 0-10,
    "confidence": 0-10,
    "reasoning": "Why this score was assigned"
  }},
  "intelligence": {{
    "personalization_opportunities": [
      "Specific fact with context for outreach",
      "Another specific insight"
    ],
    "conversation_starters": [
      "Recent achievement or change",
      "Interesting company element"
    ],
    "key_people": [
      "Name - Title - Key detail"
    ],
    "company_insights": {{
      "size_indicators": "small|medium|large|enterprise",
      "growth_stage": "startup|growing|established|mature",
      "unique_positioning": "what makes them different"
    }}
  }},
  "outreach_summary": "2-3 sentence summary of best outreach angles for this company"
}}

Focus on actionable intelligence that would make cold outreach more personalized and relevant.
```

---

## CONTENT_ANALYSIS

Used in: website_scraper.py
Purpose: Extract and clean meaningful content from raw HTML

```
# WEBSITE CONTENT EXTRACTION AND CLEANING

You are an expert at extracting meaningful business content from raw website text. Clean and structure the provided content for business intelligence analysis.

## RAW CONTENT:
{raw_content}

## EXTRACTION REQUIREMENTS:

### 1. CONTENT CLEANING
- Remove navigation elements and footers
- Filter out repetitive content
- Keep only substantive business information
- Preserve company names, people names, and specific details

### 2. STRUCTURE IDENTIFICATION
Identify and extract:
- Company description/mission
- Key services or products
- Team/leadership information
- Client testimonials or case studies
- Recent news or achievements
- Contact information

### 3. QUALITY ASSESSMENT
Rate content quality (1-10):
- 10: Rich, specific business information
- 7-9: Good business content with details
- 4-6: Basic information, some gaps
- 1-3: Minimal or poor quality content

## OUTPUT FORMAT:
{{
  "cleaned_content": {{
    "company_description": "Main company overview",
    "key_services": ["Service 1", "Service 2"],
    "leadership": ["Name - Title - Detail"],
    "achievements": ["Recent achievement with context"],
    "unique_elements": ["What makes them different"]
  }},
  "content_quality": {{
    "score": 0-10,
    "word_count": 0,
    "information_density": "high|medium|low",
    "business_relevance": "high|medium|low"
  }},
  "extraction_summary": "Brief summary of content value"
}}
```

---

## BATCH_ANALYSIS

Used in: page_prioritizer.py
Purpose: Efficient batch processing of multiple pages from same domain

```
# BATCH PAGE PRIORITIZATION

Analyze multiple pages from the same domain efficiently while identifying the most valuable pages for cold outreach intelligence.

## DOMAIN: {domain}
## PAGES TO ANALYZE: {page_count}

{pages_data}

## BATCH ANALYSIS REQUIREMENTS:

### 1. PRIORITIZATION RANKING
Rank all pages by outreach value (1-10 scale)

### 2. TOP INSIGHTS IDENTIFICATION
Identify the 3-5 most valuable insights across all pages

### 3. DOMAIN INTELLIGENCE SUMMARY
Create comprehensive company intelligence from all pages combined

## OUTPUT FORMAT:
{{
  "domain_summary": {{
    "company_overview": "Combined company understanding",
    "key_people": ["Most important contacts identified"],
    "best_outreach_angles": ["Top 3 conversation starters"],
    "company_stage": "startup|growing|established|enterprise"
  }},
  "page_rankings": [
    {{
      "url": "page_url",
      "priority_score": 0-10,
      "value_category": "HIGH|MEDIUM|LOW|NONE",
      "key_insights": ["Top insights from this page"]
    }}
  ],
  "outreach_strategy": "Recommended approach for contacting this company"
}}
```

---

## SITE_SUITABILITY

Used in: site_analyzer.py
Purpose: Determine optimal scraping method (HTTP vs Apify)

```
# WEBSITE SCRAPING METHOD ANALYSIS

Analyze website technical characteristics to determine the most effective scraping approach.

## WEBSITE DATA:
**URL:** {website_url}
**HTTP Response Code:** {status_code}
**Content Length:** {content_length}
**Response Time:** {response_time}s

**SAMPLE CONTENT:**
{content_sample}

**HTML INDICATORS:**
{html_indicators}

## ANALYSIS REQUIREMENTS:

### 1. TECHNICAL ASSESSMENT
Evaluate these factors:
- Content accessibility via HTTP
- JavaScript dependency level
- Bot protection presence
- Content quality and completeness

### 2. RECOMMENDATION LOGIC
- **HTTP_SUITABLE**: Simple sites with full content accessible
- **APIFY_REQUIRED**: JavaScript-heavy, protected, or dynamic sites
- **HYBRID_APPROACH**: Sites that might work with both methods

### 3. CONFIDENCE SCORING
Rate confidence in recommendation (0.0-1.0):
- 0.9+: Very confident in method choice
- 0.7-0.9: Confident with minor uncertainty
- 0.5-0.7: Moderate confidence, could go either way
- <0.5: Low confidence, needs testing

## OUTPUT FORMAT:
{{
  "recommendation": {{
    "method": "HTTP_SUITABLE|APIFY_REQUIRED|HYBRID_APPROACH",
    "confidence": 0.0-1.0,
    "reasoning": ["Primary factors influencing decision"]
  }},
  "technical_analysis": {{
    "javascript_dependency": "none|light|moderate|heavy",
    "bot_protection": "none|light|moderate|strong",
    "content_accessibility": "full|partial|minimal",
    "spa_framework": "none|react|angular|vue|other"
  }},
  "cost_estimate": {{
    "http_cost": 0.0,
    "apify_cost_usd": 0.002,
    "recommended_cost": 0.0
  }}
}}
```

---

## ARCHIVE

### Previous Versions

#### v1.0.0 Embedded Prompts (DEPRECATED)
Original prompts were embedded directly in scripts
Issues: Hard to modify, no version control, inconsistent formatting