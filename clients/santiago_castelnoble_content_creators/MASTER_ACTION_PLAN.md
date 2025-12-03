# 🎯 SANTIAGO CASTELNOBLE - CONTENT CREATORS PROJECT
## Master Action Plan & Detailed Checklist

**Goal:** Find 1,000 qualified content creators in self-development niche
**Target Accuracy:** 80-90%
**Budget:** $100 (Estimated actual cost: ~$2.40)
**Timeline:** 5 days

---

## 📋 EXECUTION CHECKLIST

### ✅ PHASE 0: PREPARATION (COMPLETED)

- [x] **Task 1:** Create project folder structure
  - `clients/santiago_castelnoble_content_creators/`
  - `apify_runs/` - Store all run inputs/outputs
  - `analysis/` - Analysis documents
  - `results/` - Final deliverables

- [x] **Task 2:** Analyze Apify Actor documentation
  - Understood all available parameters
  - Identified pricing: $0.002/lead ($2 per 1,000 leads)
  - Confirmed email validation available

- [x] **Task 3:** Analyze previous 5 runs
  - Run 1: 0% accuracy (too generic keywords)
  - Run 2: Low accuracy (mixed coaches/creators)
  - Run 3: Better (focused on creators)
  - Run 5: 100% accuracy for podcast hosts (BEST TEMPLATE)

- [x] **Task 4:** Identify success patterns
  - Content-specific keywords work best
  - Platform names in keywords increase accuracy
  - Remove business filters (revenue, size)
  - Exclude pure coaches without content

- [x] **Task 5:** Create hypothesis document
  - See `comprehensive_analysis.md`
  - Key insight: Focus on platforms + book content

---

### 🧪 PHASE 1: NARROW FOCUS TESTING (10 runs × 10 leads)

**Objective:** Find most promising keyword combinations
**Cost:** ~$0.20 total
**Timeline:** Days 1-2

#### Test 1: Book Summary YouTubers (US)
- [ ] **Create input JSON:**
  ```json
  {
    "company_keywords": [
      "book summary youtube", "book review youtube",
      "self-help books youtube", "book recommendations youtube",
      "reading list youtube", "book breakdown videos"
    ],
    "contact_job_title": [
      "content creator", "youtube creator", "youtuber",
      "book reviewer", "book summary creator"
    ],
    "contact_not_job_title": [
      "life coach", "business coach", "executive coach",
      "career coach", "leadership coach", "wellness coach",
      "web designer", "developer", "programmer"
    ],
    "contact_location": ["united states"],
    "email_status": ["validated"],
    "fetch_count": 10,
    "file_name": "test1_book_summary_youtubers_us"
  }
  ```
- [ ] **Run via Apify API**
- [ ] **Download results JSON**
- [ ] **Manual review & scoring:**
  - Score each lead: 0-5 (criteria in analysis doc)
  - Calculate accuracy: (leads 4-5 score) / 10 × 100%
- [ ] **Document insights:**
  - What worked?
  - What didn't?
  - Patterns in good vs bad results?
- [ ] **Decision:** Scale up or adjust?

---

#### Test 2: Motivational TikTok Creators (US)
- [ ] **Create input JSON:**
  ```json
  {
    "company_keywords": [
      "tiktok motivation", "motivational tiktok", "self improvement tiktok",
      "mindset tiktok", "personal growth tiktok", "book tiktok",
      "productivity tiktok", "tiktok creator self help"
    ],
    "contact_job_title": [
      "content creator", "tiktok creator", "tiktoker",
      "digital creator", "short-form creator", "influencer"
    ],
    "contact_not_job_title": [
      "life coach", "business coach", "executive coach",
      "marketing agency", "social media manager"
    ],
    "contact_location": ["united states"],
    "email_status": ["validated"],
    "fetch_count": 10,
    "file_name": "test2_motivational_tiktok_us"
  }
  ```
- [ ] **Run & analyze** (same process as Test 1)

---

#### Test 3: Self-Help Instagram Creators (US)
- [ ] **Create input JSON:**
  ```json
  {
    "company_keywords": [
      "instagram reels self improvement", "self help instagram",
      "motivational reels", "book quotes instagram",
      "personal growth instagram", "mindset instagram creator"
    ],
    "contact_job_title": [
      "content creator", "instagram creator", "influencer",
      "digital creator", "reels creator"
    ],
    "contact_not_job_title": [
      "life coach", "business coach", "fitness coach",
      "beauty influencer", "fashion influencer"
    ],
    "contact_location": ["united states"],
    "email_status": ["validated"],
    "fetch_count": 10,
    "file_name": "test3_selfhelp_instagram_us"
  }
  ```
- [ ] **Run & analyze**

---

#### Test 4: Book Review Podcasters (US)
- [ ] **Create input JSON:**
  ```json
  {
    "company_keywords": [
      "book review podcast", "reading podcast",
      "self-help podcast", "personal development podcast",
      "book discussion podcast", "author interviews podcast"
    ],
    "contact_job_title": [
      "podcast host", "podcaster", "content creator",
      "book reviewer", "host"
    ],
    "contact_not_job_title": [
      "executive coach", "business consultant",
      "marketing agency owner"
    ],
    "contact_location": ["united states"],
    "email_status": ["validated"],
    "fetch_count": 10,
    "file_name": "test4_book_podcast_us"
  }
  ```
- [ ] **Run & analyze**

---

#### Test 5: Personal Growth YouTubers (US)
- [ ] **Create input JSON:**
  ```json
  {
    "company_keywords": [
      "personal growth youtube", "self development videos",
      "mindset youtube channel", "productivity youtube",
      "life advice youtube", "personal development content"
    ],
    "contact_job_title": [
      "content creator", "youtube creator", "youtuber",
      "video creator", "digital creator"
    ],
    "contact_not_job_title": [
      "life coach", "therapist", "counselor"
    ],
    "contact_location": ["united states"],
    "email_status": ["validated"],
    "fetch_count": 10,
    "file_name": "test5_personal_growth_youtube_us"
  }
  ```
- [ ] **Run & analyze**

---

#### Test 6: Mindset Content Creators (US + Canada)
- [ ] **Create input JSON** (expand location)
- [ ] **Run & analyze**

---

#### Test 7: Productivity Content Creators (US + UK)
- [ ] **Create input JSON**
- [ ] **Run & analyze**

---

#### Test 8: Leadership Content Creators (All 3)
- [ ] **Create input JSON** (US + Canada + UK)
- [ ] **Run & analyze**

---

#### Test 9: Professional Development Creators (All 3)
- [ ] **Create input JSON**
- [ ] **Run & analyze**

---

#### Test 10: Best Combo (Mixed Platforms)
- [ ] **Combine winning keywords** from Tests 1-9
- [ ] **Create optimized input JSON**
- [ ] **Run & analyze**

---

#### Phase 1 Review & Analysis
- [ ] **Create comparison spreadsheet:**
  - Test # | Keywords Used | Accuracy % | Top Insights
- [ ] **Identify top 3 performers**
- [ ] **Extract common success patterns:**
  - Which platforms worked best?
  - Which keywords had highest precision?
  - Any unexpected wins?
- [ ] **Select winning strategy for Phase 2**

---

### 🔬 PHASE 2: REFINEMENT & VALIDATION (3 runs × 30 leads)

**Objective:** Achieve stable 85%+ accuracy
**Cost:** ~$0.18 total
**Timeline:** Day 3

#### Validation Run 1 (30 leads)
- [ ] **Combine best keywords from Phase 1**
- [ ] **Create refined input JSON:**
  ```json
  {
    "company_keywords": [
      "BEST_KEYWORDS_FROM_TESTS_1-10",
      "Mix of platform + content type",
      "Book-focused terms if Tests 1/4 performed well"
    ],
    "contact_job_title": [
      "BEST_JOB_TITLES_FROM_PHASE_1"
    ],
    "contact_not_job_title": [
      "ALL_EXCLUSIONS_PLUS_NEW_ONES_FROM_PHASE_1_FAILURES"
    ],
    "company_not_keywords": [
      "fitness", "gym", "nutrition", "diet",
      "agency", "consulting firm", "coaching business"
    ],
    "contact_location": ["united states", "canada", "united kingdom"],
    "email_status": ["validated"],
    "fetch_count": 30,
    "file_name": "validation1_combined_best"
  }
  ```
- [ ] **Run & deep analysis:**
  - Check all 30 leads manually
  - Score each: 0-5
  - Calculate accuracy
  - **Target: 85%+ accuracy**
- [ ] **If <85%:** Document failure patterns, adjust keywords

---

#### Validation Run 2 (30 leads)
- [ ] **Adjust based on Validation 1 results**
- [ ] **Run with refined parameters**
- [ ] **Analyze & score**
- [ ] **If still <85%:** More aggressive exclusions

---

#### Validation Run 3 (30 leads)
- [ ] **Final refinement**
- [ ] **Run & validate**
- [ ] **Target: 85-90% accuracy STABLE**
- [ ] **If achieved:** PROCEED TO PHASE 3
- [ ] **If not:** Execute Fallback Strategy (see below)

---

#### Phase 2 Decision Point
- [ ] **Check:** Is accuracy 85%+ on all 3 validation runs?
  - **YES** → Proceed to Phase 3 Production
  - **NO** → Execute Fallback Strategy A or B

---

### 🚀 PHASE 3: PRODUCTION (5 runs × 200 leads = 1,000)

**Objective:** Deliver 1,000 qualified leads
**Cost:** ~$2.00
**Timeline:** Days 4-5

#### Production Batch 1 (200 leads)
- [ ] **Use winning configuration from Phase 2**
- [ ] **Run production batch:**
  ```json
  {
    "SAME_AS_VALIDATION_RUNS_BUT_fetch_count_200"
  }
  ```
- [ ] **Download results**
- [ ] **QA Sample:** Manually check 20 random leads (10%)
- [ ] **Calculate sample accuracy**
- [ ] **If accuracy drops below 80%:** PAUSE & investigate

---

#### Production Batch 2 (200 leads)
- [ ] **Run second batch**
- [ ] **QA Sample:** Check 20 leads
- [ ] **Monitor accuracy**

---

#### Production Batch 3 (200 leads)
- [ ] **Run third batch**
- [ ] **QA Sample:** Check 20 leads

---

#### Production Batch 4 (200 leads)
- [ ] **Run fourth batch**
- [ ] **QA Sample:** Check 20 leads

---

#### Production Batch 5 (200 leads)
- [ ] **Run final batch**
- [ ] **QA Sample:** Check 20 leads

---

#### Data Processing & Deduplication
- [ ] **Combine all 5 batches** into master dataset
- [ ] **Deduplicate by email:**
  - Remove duplicate email addresses
  - Keep first occurrence (or best quality record)
- [ ] **Verify total:** Should have ~1,000 unique leads
- [ ] **If under 1,000:** Run supplementary batch with adjusted params

---

#### Final Quality Assurance
- [ ] **Full dataset review:**
  - Check for obvious errors
  - Verify email format validity
  - Confirm location field = US/Canada/UK only
- [ ] **Sample audit:** Manually verify 50 random leads
- [ ] **Calculate final accuracy:** (qualified leads / total) × 100%
- [ ] **Target: 80-90% accuracy**

---

#### Deliverable Preparation
- [ ] **Export to CSV format:**
  - Clean column headers
  - Remove unnecessary fields
  - Organize: Name, Email, Job Title, Company, Location, LinkedIn, etc.
- [ ] **Create summary report:**
  - Total leads delivered
  - Accuracy achieved
  - Breakdown by platform (YouTube/TikTok/Instagram/Podcast)
  - Breakdown by location (US/Canada/UK)
- [ ] **Package files:**
  - `santiago_content_creators_final_1000.csv`
  - `project_summary_report.md`

---

### 📊 FALLBACK STRATEGIES

#### If Accuracy <85% After Phase 2:

**Fallback A: Platform-Specific Searches**
- [ ] Run separate searches for each platform:
  - YouTube-only creators (250 leads)
  - TikTok-only creators (250 leads)
  - Instagram-only creators (250 leads)
  - Podcast-only hosts (250 leads)
- [ ] Use ultra-specific keywords per platform
- [ ] Combine results after deduplication

**Fallback B: Hybrid Approach**
- [ ] Use Apify for best 500-700 leads (highest confidence)
- [ ] Supplement with manual research:
  - YouTube search: "book summary", "self-help books"
  - TikTok hashtag search: #booksummary, #selfimprovement
  - Instagram search: similar hashtags
- [ ] Manually verify each supplementary lead
- [ ] Combine to reach 1,000 total

**Fallback C: Relaxed Matching + Manual Filter**
- [ ] Accept 60-70% accuracy from tool
- [ ] Run larger batches (1,500 leads total)
- [ ] Manually filter down to best 1,000
- [ ] Time-intensive but guarantees quality

---

## 📈 SUCCESS METRICS & TRACKING

### Per-Run Tracking Template
```
RUN ID: ___________
DATE: ___________
PHASE: [ ] 1-Testing  [ ] 2-Validation  [ ] 3-Production

INPUT PARAMETERS:
- Keywords: ___________
- Job Titles: ___________
- Locations: ___________
- Count: ___________

RESULTS:
- Leads Retrieved: ___________
- Cost: $___________
- Accuracy: ___%

TOP ISSUES:
1. ___________
2. ___________
3. ___________

ADJUSTMENTS FOR NEXT RUN:
- ___________
```

### Cumulative Dashboard
- **Total Leads Collected:** ___ / 1,000
- **Total Cost:** $___ / $100
- **Average Accuracy:** ___%
- **Best Keyword Set:** ___________
- **Phase Status:** [ ] 1  [ ] 2  [ ] 3

---

## 🎯 QUALITY SCORING RUBRIC

**5 - Perfect Match:**
- Content creator (YouTube/TikTok/Instagram/Podcast)
- Self-development/personal growth niche
- Regularly publishes book summaries/reviews OR motivational content
- Personal email (not agency)
- Location: US/Canada/UK

**4 - Good Match:**
- Content creator with self-dev focus
- May not specifically do book content
- All other criteria met

**3 - Partial Match:**
- Content creator but wrong niche OR
- Coach/speaker with significant content creation activity
- Location correct

**2 - Weak Match:**
- Primarily coach/consultant
- Minimal content creation
- May be in self-dev space

**1 - Wrong Target:**
- Business owner (non-creator)
- Wrong industry
- May be in correct location

**0 - Completely Irrelevant:**
- Web designer, developer, tree service, etc.
- No relation to content creation or self-dev

**Accuracy Calculation:**
```
Accuracy = (Count of 4-5 scores / Total leads) × 100%
```

---

## ⚠️ CRITICAL SUCCESS FACTORS

1. **Book Content Focus:**
   - If client wants book-focused creators, emphasize "book summary", "book review" keywords
   - If general self-dev OK, broader keywords acceptable

2. **Platform Preference:**
   - Determine if YouTube > TikTok > Instagram in priority
   - Adjust keyword weighting accordingly

3. **Coach vs Creator:**
   - Clarify: Are coaches acceptable IF they create content regularly?
   - Or pure content creators only?

4. **Agency-Free:**
   - Ensure exclusions catch agency-managed creators
   - Look for "agency", "management", "media company" in company names
   - Verify email domain matches personal/brand domain

5. **Engagement Verification:**
   - Tool provides follower counts where available
   - Manual spot-check LinkedIn/social profiles for authenticity
   - Red flags: Sudden follower spikes, low engagement ratio

---

## 📞 CHECKPOINT QUESTIONS FOR CLIENT

**Before starting Phase 1:**
- [ ] **Priority:** Books content required, or general self-dev OK?
- [ ] **Platform:** Preference order? (YouTube/TikTok/Instagram/Podcast)
- [ ] **Coaches:** Accept if they create content regularly?
- [ ] **Follower count:** Minimum threshold? (micro vs macro influencers)
- [ ] **Publishing frequency:** How often must they post to qualify?

---

## 🗓️ TIMELINE BREAKDOWN

**Day 1 (4-6 hours):**
- Morning: Tests 1-3
- Afternoon: Tests 4-5
- Evening: Analysis of first 5 tests

**Day 2 (4-6 hours):**
- Morning: Tests 6-8
- Afternoon: Tests 9-10
- Evening: Phase 1 comprehensive analysis
- Decision: Select winning strategy

**Day 3 (4-6 hours):**
- Morning: Validation Run 1
- Afternoon: Validation Runs 2-3
- Evening: Final refinement & Phase 2 decision

**Day 4 (4-6 hours):**
- Batches 1-3 (600 leads)
- QA sampling & monitoring

**Day 5 (4-6 hours):**
- Batches 4-5 (400 leads)
- Deduplication
- Final QA
- Deliverable prep
- Client handoff

**Total Time:** 20-30 hours over 5 days

---

## ✅ FINAL DELIVERABLES CHECKLIST

- [ ] **Main CSV File:**
  - `santiago_content_creators_1000.csv`
  - Clean, deduplicated
  - All required fields populated

- [ ] **Summary Report:**
  - Total leads: 1,000
  - Accuracy achieved: ___%
  - Platform breakdown
  - Location breakdown
  - Methodology summary

- [ ] **Quality Metrics:**
  - Sample audit results
  - Confidence score per lead (optional)

- [ ] **Bonus Insights:**
  - Top creators by followers
  - Emerging trends noticed
  - Recommended outreach approach

---

**END OF MASTER ACTION PLAN**

*Ready to execute upon approval.*
