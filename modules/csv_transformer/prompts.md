# CSV Transformation Prompts

## COMPANY_NAME_NORMALIZER
**Purpose:** Normalize company names to casual format
**Input Columns:** company_name
**Output:** Casual company name

```
You will receive a company name as input.

Your task is to return a shortened, casual version of that name — the way employees or insiders would refer to the company in everyday conversation.

Only output the normalized, informal name — no extra words, no explanations, no capitalization unless absolutely natural.

Strip away any corporate terms like "Inc.", "LLC", "Solutions", "Technologies", "Group", "Enterprises", etc.

Make the name as short and casual as possible, while keeping it recognizable.

Examples:
• "Acme Technologies Inc." → "acme"
• "Northwest Payment Solutions" → "northwest"
• "BrightPixel Group" → "brightpixel"
• "Global Data Systems LLC" →  "globaldata"

Only return the casual name. Nothing else.

Company name: {company_name}
```

## CITY_NORMALIZER
**Purpose:** Normalize city names to common abbreviations
**Input Columns:** city
**Output:** Normalized city name or abbreviation

```
You will receive the name of a city or location as input.

Your task is to return a **casual, real-world abbreviation or shorthand** — the way locals or people in tech/startup circles naturally refer to it.

Only return a casual version **if one actually exists and is commonly used**.
If the full city name is already short and used as-is (like "London" or "Berlin"), just return it unchanged.

Guidelines:
• Use natural abbreviations only if they are real and recognized (e.g. "SF" for San Francisco, "NYC" for New York City, "SPB" for Saint Petersburg, "BLR" for Bangalore).
• Do **not** invent abbreviations that no one uses.
• Respect context — only shorten when it's common in tech/startup/business/informal language.
• Keep capitalization natural (e.g. "NYC", not "nyc"; "SPB", not "spb"; "London", not "london").
• Never include country, region, or extra words — just the core location name or its casual abbreviation.

Examples:
• "San Francisco" → "SF"
• "New York" → "NYC"
• "Saint Petersburg" → "SPB"
• "Bangalore" → "BLR"
• "Los Angeles" → "LA"
• "London" → "London"
• "Berlin" → "Berlin"
• "Chicago" → "Chicago"
• "São Paulo" → "Sampa"

Only return the final, normalized city name or abbreviation. No explanation, no punctuation, no extra words.

City name: {city}
```