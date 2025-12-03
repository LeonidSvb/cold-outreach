# SANTIAGO CASTELNOBLE - CONTENT CREATORS PROJECT
## Comprehensive Analysis & Action Plan

**Date:** 2025-12-03
**Client:** Santiago Castelnoble
**Project:** Find 1,000 Content Creators (Self-Development Niche)
**Budget:** $100 for 1,000 qualified leads
**Tool:** Apify Leads Finder (code_crafter/leads-finder)

---

## CLIENT REQUIREMENTS

### Target Profile
- **Location:** USA, Canada, or UK ONLY
- **Content Focus:** Personal improvement, professional growth, motivation, mindset, leadership, book-based learning
- **Content Type:** Regular publishers of book-related or self-improvement content
- **Authenticity:** Real engagement (no fake audience/manipulative growth)
- **Ownership:** Independent creators (NOT agency-managed, personal emails only)

### Quality Standards
- **Accuracy Target:** 80-90% qualified leads
- **Must Have:** Personal or business email addresses
- **Must NOT:** Coaches/consultants WITHOUT content creator activity

---

## PREVIOUS RUNS ANALYSIS

### Run 1: "self_dev_creators" (1,000 leads, $2.02)
**Input Strategy:**
- Broad company keywords: "coaching", "training", "education", "personal development"
- Revenue filter: $100K-$500K
- Size: 1-10 employees
- Seniority: partner, owner, founder

**Results: 0% ACCURACY**
- Web designers (T. Brooks Web Design)
- Graphic design agencies (Graphic Edge)
- Construction companies (The Wills Company)
- Tree services (Texas Tree Surgeons)
- IT consultants (QLS Solutions)
- Cleaning services (2 Green Chicks)

**Root Cause:** Keywords too generic, no job title filtering, focused on business owners not content creators

---

### Run 2: "self_dev_creators2" (30 leads, $0.07)
**Input Strategy:**
- Added contact_job_title: "mindset coach", "life coach", "content creator"
- Added contact_not_job_title: web designers, developers, etc.
- Same company keywords as Run 1

**Improvement:** Job title filtering introduced
**Issue:** Still mixed coaches with content creators

---

### Run 3: "self_dev_creators_refined" (30 leads, $0.08)
**Input Strategy:**
- Refined company keywords: "self improvement", "book review", "learning"
- Focused contact_job_title: "content creator", "youtube creator", "tiktok creator", "podcaster"
- Removed revenue and seniority filters

**Improvement:** More focused on digital content creators
**Issue:** Still too broad, missing content-specific keywords

---

### Run 5: "tik tok" (10 leads, $0.04) ✅ BEST PERFORMANCE
**Input Strategy:**
```json
{
  "company_keywords": [
    "self improvement content", "book summary", "book review",
    "motivational videos", "youtube channel", "podcast host",
    "self-improvement creator", "mindset creator"
  ],
  "contact_job_title": [
    "content creator", "video creator", "tiktok creator",
    "youtube creator", "podcast host", "influencer"
  ],
  "contact_location": ["united states"],
  "fetch_count": 10
}
```

**Results: 100% ACCURACY (for podcast/speaker niche)**
- Erin Coupe: CEO, Keynote Speaker, Podcast Host ✅
- Nicole Kalil: Author, Podcast Host ✅
- Bilal Zaidi: Founder + Podcast Host ✅
- Stephanie Trantham: Owner/Influencer (2.3M+ followers) ✅
- Chris Cerrone: Podcast Host ✅
- Caneel Joyce: Executive Coach, Podcaster ✅
- Erica Lockheimer: CEO, Podcast Host ✅
- Sun Yi: TEDx Speaker, Podcast Host ✅
- Christopher Nelson: Podcast Host ✅
- Nikki Innocent: Speaker, Podcast Host ✅

**Key Success Factors:**
- Very specific content-related keywords
- Clear job title focus on creators/podcasters
- No revenue/size constraints that limited pool

**Remaining Issues:**
- Many are COACHES/SPEAKERS, not pure content creators
- Not all publish book summaries/reviews (client requirement)
- Need more YouTube/TikTok/Instagram video creators
- Need to verify regular publishing schedule

---

## ROOT CAUSE ANALYSIS

### Why Previous Runs Failed:
1. **Too Generic Keywords:** "coaching", "training" matched service providers, not creators
2. **Wrong Target:** Focused on business owners instead of individual content creators
3. **Missing Platform Indicators:** Didn't specify YouTube, TikTok, Instagram in keywords
4. **No Book Focus:** Client wants book-related content, previous runs didn't emphasize this
5. **Revenue Filters:** Limited pool unnecessarily (content creators may not report revenue)

### Why Run 5 Succeeded:
1. **Content-Specific Keywords:** "book summary", "motivational videos", "youtube channel"
2. **Creator Job Titles:** "content creator", "video creator", "podcast host"
3. **No Business Constraints:** Removed revenue/size filters
4. **Platform Names in Keywords:** "tiktok", "youtube", "podcast"

---

## HYPOTHESIS FOR 80-90% ACCURACY

### Critical Changes Needed:

#### 1. **Exclude Pure Coaches/Consultants**
```json
"contact_not_job_title": [
  "executive coach", "life coach", "business coach",
  "leadership coach", "career coach", "wellness coach"
]
```

#### 2. **Focus on Video/Visual Content Platforms**
```json
"company_keywords": [
  "youtube channel", "tiktok account", "instagram reels",
  "book summary videos", "book review youtube",
  "self-help youtube", "motivation shorts"
]
```

#### 3. **Emphasize Book-Related Content**
```json
"company_keywords": [
  "book summary", "book review", "book breakdown",
  "reading list", "book recommendations"
]
```

#### 4. **Add Platform-Specific Job Titles**
```json
"contact_job_title": [
  "youtuber", "tiktoker", "instagram creator",
  "book reviewer", "book summary creator"
]
```

#### 5. **Expand to Canada & UK**
```json
"contact_location": [
  "united states", "canada", "united kingdom"
]
```

#### 6. **Remove Business Filters**
- NO max_revenue
- NO min_revenue
- NO size restrictions
- NO seniority_level (content creators may not have traditional titles)

---

## OPTIMIZATION STRATEGY

### Phase 1: Narrow Focus Testing (10 runs x 10 leads = 100 leads)

**Objective:** Find the most promising keyword combinations

**Test Matrix:**
1. **Book Summary YouTubers** (US only)
2. **Motivational TikTok Creators** (US only)
3. **Self-Help Instagram Creators** (US only)
4. **Book Review Podcasters** (US only)
5. **Personal Growth YouTubers** (US only)
6. **Mindset Content Creators** (US + Canada)
7. **Productivity Content Creators** (US + UK)
8. **Leadership Content Creators** (All 3 countries)
9. **Professional Development Creators** (All 3 countries)
10. **Mixed Platform Creators** (Best performing keywords combo)

**Success Criteria:**
- 80%+ accuracy = Scale up
- 50-79% accuracy = Refine keywords
- <50% accuracy = Abandon approach

### Phase 2: Validation & Refinement (based on Phase 1 results)

**Actions:**
1. Analyze top 3 performing keyword sets
2. Combine winning elements
3. Run 3 validation tests (30 leads each)
4. Adjust based on results

### Phase 3: Scale-Up Production

**Once 85%+ accuracy achieved:**
1. Run production batches (100-200 leads each)
2. Manual QA on samples
3. Adjust if accuracy drops
4. Deliver final 1,000 leads

---

## DETAILED ACTION PLAN

### PREPARATION PHASE (Before Starting Runs)

#### Step 1: Research Platform-Specific Keywords ✅
- [x] Analyze successful Run 5 keywords
- [ ] Identify book-related content indicators
- [ ] List platform-specific terms (YouTube, TikTok, Instagram)
- [ ] Compile NOT keywords (coaches, agencies, etc.)

#### Step 2: Create Test Configurations ✅
- [ ] Prepare 10 JSON input files for Phase 1 tests
- [ ] Document hypothesis for each test
- [ ] Set up tracking spreadsheet for results

#### Step 3: Establish Success Metrics ✅
- [ ] Define what counts as "qualified" (exact criteria)
- [ ] Create scoring rubric (0-5 scale per lead)
- [ ] Set up results tracking template

---

### EXECUTION PHASE (Testing & Optimization)

#### Phase 1: Testing (Days 1-2)
**Daily Target:** 5 runs per day

**Workflow:**
1. Run test (10 leads)
2. Download results JSON
3. Manual review of all 10 leads
4. Score each lead (0-5):
   - 5: Perfect match (content creator + self-dev + books)
   - 4: Good match (content creator + self-dev, no books)
   - 3: Partial match (content creator, wrong niche OR coach with content)
   - 2: Weak match (coach/consultant, minimal content)
   - 1: Wrong target (business owner, wrong industry)
   - 0: Completely irrelevant
5. Calculate accuracy: (leads scoring 4-5) / 10 × 100%
6. Document insights
7. Adjust next test based on learnings

**Expected Outcomes:**
- Identify top 3 keyword combinations
- Understand which platforms work best (YouTube vs TikTok vs Instagram)
- Discover optimal location filtering strategy

#### Phase 2: Refinement (Day 3)
**Objective:** Achieve 85%+ accuracy

**Actions:**
1. Combine best keywords from Phase 1
2. Run 3 validation tests (30 leads each = 90 leads)
3. Analyze failure cases
4. Fine-tune exclusions (contact_not_job_title, company_not_keywords)
5. Re-test until 85%+ accuracy stable

#### Phase 3: Production (Days 4-5)
**Objective:** Deliver 1,000 qualified leads

**Workflow:**
1. Run production batches:
   - 5 runs × 200 leads = 1,000 leads
2. QA sampling (manual check 10% of each batch)
3. If accuracy drops below 80%, pause and refine
4. Deduplicate results
5. Format final CSV
6. Final QA review
7. Deliver to client

---

### MONITORING & QUALITY CONTROL

#### Real-Time Tracking
**Per Run:**
- Input parameters used
- Cost incurred
- Leads retrieved
- Accuracy score
- Top issues found

**Cumulative:**
- Total leads collected
- Average accuracy
- Total cost
- Best performing keyword sets
- Common rejection reasons

#### Quality Checkpoints
1. After every 10 leads: Quick scan for red flags
2. After every 100 leads: Detailed QA review
3. Before delivery: Full audit of final dataset

---

## EXPECTED OUTCOMES

### Cost Projection
- Phase 1: 10 runs × 10 leads = 100 leads ≈ $0.20
- Phase 2: 3 runs × 30 leads = 90 leads ≈ $0.18
- Phase 3: 5 runs × 200 leads = 1,000 leads ≈ $2.00
- **Total Estimated Cost:** $2.40 (well under $100 budget)

### Timeline
- Day 1: Preparation + Phase 1 Testing (runs 1-5)
- Day 2: Phase 1 Testing (runs 6-10) + Initial Analysis
- Day 3: Phase 2 Refinement + Validation
- Day 4: Phase 3 Production (batches 1-3)
- Day 5: Phase 3 Production (batches 4-5) + QA + Delivery

**Total Timeline:** 5 days

### Success Probability
- **High Confidence (85%):** Achieving 80%+ accuracy
- **Medium Confidence (60%):** Achieving 90%+ accuracy
- **Key Risk:** Apollo/LinkedIn data quality for niche content creators

---

## FALLBACK STRATEGIES

### If Accuracy Below 70% After Phase 2:

#### Option A: Multi-Platform Search
Instead of one query, run separate searches for:
- YouTube-only creators
- TikTok-only creators
- Instagram-only creators
- Podcast-only hosts

**Benefit:** Platform-specific keywords more precise

#### Option B: Looser Matching + Manual Filtering
- Accept 60-70% accuracy from tool
- Manually filter final results
- Use LinkedIn verification for content activity

#### Option C: Hybrid Approach
- Use Apify for 500-700 leads (best matches)
- Supplement with manual research (YouTube search, TikTok hashtags)
- Combine to reach 1,000 qualified leads

---

## NEXT STEPS

### Immediate Actions:
1. **Create Test 1 Configuration** (Book Summary YouTubers - US)
2. **Run Test 1** (10 leads)
3. **Analyze results**
4. **Adjust and run Test 2**
5. **Continue iterative testing**

### Approval Needed:
- Confirm client priorities: Books focus vs General self-dev?
- Preferred platforms: YouTube > TikTok > Instagram?
- Accept podcast hosts or video-only creators?
- OK with coaches IF they create regular content?

---

## APPENDIX

### Full Parameter Reference (From Previous Runs)

**Available Parameters:**
- company_domain
- company_industry
- company_keywords
- company_not_industry
- company_not_keywords
- contact_job_title
- contact_location
- contact_not_city
- contact_not_job_title
- contact_not_location
- email_status
- fetch_count
- file_name
- functional_level
- funding
- max_revenue
- min_revenue
- seniority_level
- size

**Confirmed Working Values:**
- contact_location: "united states", "canada", "united kingdom"
- email_status: "validated", "not_validated", "unknown"
- Recommended: Keep only "validated" for deliverable quality

---

**END OF ANALYSIS**
