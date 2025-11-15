# Email Templates: Soviet Boots Connector Campaign

## 🎯 Campaign Overview

**Product:** Authentic Soviet military boots (from real soldiers)
**Angle:** Connector (introduce supplier to customer)
**Target:** European museums, militaria stores, reenactment clubs
**Tone:** Short, personal, connector-style

---

## 📧 EMAIL SEQUENCE (3 emails)

### **EMAIL 1: INITIAL OUTREACH**

**Subject:** Quick intro – Soviet military artifacts

**Body:**
```
Hey {{firstName}},

{{personal_compliment}}

I'm passionate about Soviet military history and connecting collectors with authentic pieces.

{{relevance_reason}}

I know a collector who sources genuine Soviet military boots directly from veterans – each pair has real history.

{{specific_use_case}}

Worth an intro if {{companyName}} is interested?

Best,
[Your Name]
```

---

### **EMAIL 2: FOLLOW-UP (3-4 days later)**

**Subject:** Re: Quick intro – Soviet military artifacts

**Body:**
```
Hi {{firstName}},

Still worth making the connection or wrong timing?

Best,
[Your Name]
```

---

### **EMAIL 3: BREAKUP (7 days after follow-up)**

**Subject:** Re: Quick intro – Soviet military artifacts

**Body:**
```
Hi {{firstName}},

Haven't heard back so I'll assume it's not a fit right now.

Will keep {{companyName}} in mind if similar opportunities come up.

Best,
[Your Name]
```

---

## 🔧 VARIABLES MAPPING

### **Universal Variables:**
- `{{firstName}}` - First name from database
- `{{companyName}}` - Organization name
- `{{personal_compliment}}` - Segment-specific compliment
- `{{relevance_reason}}` - Why reaching out to them specifically
- `{{specific_use_case}}` - How they would use the boots

---

## 🎨 SEGMENT-SPECIFIC VARIATIONS

### **Segment A: MUSEUMS**

**Example:**
```
Subject: quick question

Hey Michael

Checked out polish army museum, really liked the Cold War section you guys have

Thought it might work for your exhibits since you focus on Eastern Front preservation, I work with a collector who sources original Soviet boots from veterans

Could add some authenticity - visitors tend to connect more with real gear than reproductions

Worth a quick chat?

Leo
```

**Variables:**
```json
{
  "compliment": "Checked out polish army museum, really liked the Cold War section you guys have",
  "relevance_reason": "it might work for your exhibits since you focus on Eastern Front preservation",
  "value_proposition": "Could add some authenticity - visitors tend to connect more with real gear than reproductions"
}
```

---

### **Segment B: MILITARIA STORES**

**Example:**
```
Subject: quick question

Hey Anna

Found military antiques berlin on Google, pretty solid eastern european collection

Thought your customers might be into this since they seem to prefer authentic stuff, I work with a collector who sources original Soviet boots from veterans

Not reproductions - actual issue boots with real wear, your collectors would probably dig them

Worth a chat about supply?

Leo
```

**Variables:**
```json
{
  "compliment": "Found military antiques berlin on Google, pretty solid eastern european collection",
  "relevance_reason": "your customers might be into this since they seem to prefer authentic stuff",
  "value_proposition": "Not reproductions - actual issue boots with real wear, your collectors would probably dig them"
}
```

---

### **Segment C: REENACTMENT CLUBS**

**Example:**
```
Subject: quick question

Hey Dmitry

Saw red army reenactment club's photos, love how you guys focus on getting the details right

Thought it could fit your events since the group's all about accuracy, I work with a collector who sources original Soviet boots from veterans

Actual period boots, not modern repros - would add some real authenticity

Worth a quick chat?

Leo
```

**Variables:**
```json
{
  "compliment": "Saw red army reenactment club's photos, love how you guys focus on getting the details right",
  "relevance_reason": "it could fit your events since the group's all about accuracy",
  "value_proposition": "Actual period boots, not modern repros - would add some real authenticity"
}
```

---

## 🤖 AI PERSONALIZATION PROMPT (CASUAL STYLE)

Use this prompt to generate variables from existing data:

```
You're helping write casual, human-sounding connector emails for a Soviet military boots campaign.

PRODUCT CONTEXT:
- What: Original Soviet military boots from real veterans (not reproductions)
- Angle: You're a connector - introducing a supplier friend to potential customers
- Tone: Personal, casual, authentic - like a real person reaching out
- NOT a sales pitch - just seeing if there's interest in making an intro

LEAD DATA:
- Name: {{name}}
- Type: {{type}} (museum/militaria_store/reenactment_club/collector)
- Summary: {{summary}}
- Hooks: {{personalization_hooks}}
- Focus: {{focus_wars}}, {{focus_periods}}, {{focus_topics}}

EMAIL TEMPLATE:
```
Subject: quick question

Hey {{firstName}}

{{compliment}}

Thought {{relevance_reason}}, I work with a collector who sources original Soviet boots from veterans

{{value_proposition}}

Worth a quick chat?

Leo
```

TASK:
Generate these 3 variables in CASUAL, HUMAN style:

1. **compliment** (15-25 words)
   - Reference something specific from their summary/hooks
   - Sound natural, like quick typing
   - Use lowercase for organization name
   - Natural punctuation (commas ok, no long dashes)
   - Examples: "checked out polish army museum, really liked the cold war section", "found your site on google, pretty solid eastern european collection"

2. **relevance_reason** (15-25 words)
   - Why boots might fit their focus
   - Connect to their specific activities
   - Keep conversational, can be grammatically imperfect
   - Examples: "you seem focused on authentic pieces", "might work for your exhibitions somehow", "could fit your reenactment events"

3. **value_proposition** (15-25 words)
   - Specific benefit for their use case
   - Museums: exhibitions, visitor connection
   - Stores: collector appeal, authenticity
   - Clubs: reenactment accuracy
   - Very casual tone, like afterthought
   - Examples: "could add some authenticity to your exhibits", "your collectors would probably dig the real history", "better than modern repros for events"

STYLE REQUIREMENTS:
- Use lowercase for organization names (e.g., "polish army museum" not "Polish Army Museum")
- Sound like a real person typing quickly - natural, not polished
- OK to use contractions: "I'm", "it's", "they'd"
- Can have minor grammar quirks to sound authentic
- No corporate speak or sales language
- Short, punchy sentences

OUTPUT FORMAT (JSON):
{
  "compliment": "...",
  "relevance_reason": "...",
  "value_proposition": "..."
}
```

---

## 📊 IMPLEMENTATION WORKFLOW

### **Step 1: Segment Selection**
```python
# Filter high-value leads
df_tier1 = df[
    (df['relevance_score'] >= 7) &
    (df['contact_status'] == 'with_emails')
]

# Segment by type
museums = df_tier1[df_tier1['type'] == 'museum']
stores = df_tier1[df_tier1['type'] == 'militaria_store']
clubs = df_tier1[df_tier1['type'] == 'reenactment_club']
```

### **Step 2: Generate Variables with AI**
```python
for lead in museums:
    variables = generate_with_gpt4(
        name=lead['name'],
        type=lead['type'],
        summary=lead['summary'],
        hooks=lead['personalization_hooks']
    )

    lead['compliment'] = variables['compliment']
    lead['relevance_reason'] = variables['relevance_reason']
    lead['value_proposition'] = variables['value_proposition']
```

### **Step 3: Fill Templates**
```python
email_1 = f"""subject: quick question

hey {lead['firstName']}

{lead['compliment']}

thought {lead['relevance_reason']}, a friend sources original soviet boots from veterans

{lead['value_proposition']}

worth a quick chat?

leo
"""
```

### **Step 4: Export to Google Sheets / Instantly**
```python
# Add icebreaker column to Parquet
manager.add_columns(icebreakers_df, key='place_id')

# Export for campaign
manager.export_csv(
    output='soviet_boots_tier1_museums.csv',
    columns=['firstName', 'email', 'companyName', 'icebreaker_email1'],
    filters={'type': 'museum', 'relevance_score': '>=7'}
)
```

---

## 🎯 CAMPAIGN PRIORITIES

### **Phase 1: TIER 1 Museums (509 leads, score 7+)**
- Highest conversion potential
- Most aligned with product
- Start here

### **Phase 2: TIER 1 Stores (subset of 509)**
- Good commercial potential
- Easier to close (B2B sale)

### **Phase 3: TIER 2 (386 leads, score 5-6)**
- Test after Tier 1 response
- May need stronger personalization

---

## 💡 PERSONALIZATION TIPS

### **DO:**
- ✅ Reference specific details from their website/summary
- ✅ Mention Soviet-era wars/periods they focus on
- ✅ Be brief (under 100 words)
- ✅ Sound like a connector, not a seller

### **DON'T:**
- ❌ Generic compliments ("your website is great")
- ❌ Long emails (over 150 words)
- ❌ Sales pitch tone ("buy now", "limited time")
- ❌ Multiple asks in one email

---

## 📈 SUCCESS METRICS

**Target Response Rates:**
- Email 1: 5-10% reply rate (25-50 replies from 509 Tier 1)
- Email 2: 2-3% additional
- Email 3: 1-2% additional

**Total Expected:** 40-75 interested leads from Tier 1

---

## 🔧 TECHNICAL IMPLEMENTATION

**Script to create:** `modules/openai/scripts/generate_soviet_boots_icebreakers.py`

**Features:**
- Load from Parquet (soviet_boots_europe)
- Generate 3 variables per lead with GPT-4o-mini:
  - compliment
  - relevance_reason
  - value_proposition
- Add `email_body` column with filled template
- Save back to Parquet
- Export segmented CSVs for campaigns

**Estimated cost:** $0.10 per 100 leads (GPT-4o-mini)
**For 509 Tier 1 leads:** ~$0.50

---

**Last Updated:** 2025-11-11
