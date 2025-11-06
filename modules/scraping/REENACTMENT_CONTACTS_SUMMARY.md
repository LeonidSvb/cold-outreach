# Historical Reenactment Clubs - Contact Collection Summary

**Date:** 2025-11-02
**Target:** 300+ contacts (USA, Canada, Europe, Australia)
**Focus:** WWII, Afghan War, Cold War reenactment groups

---

## 📊 CURRENT RESULTS

### Verified Contacts Collected: **23 Groups**

**By Contact Type:**
- ✅ With Email: **6 groups**
- 🌐 With Website Only: **17 groups**
- 📞 With Phone: **1 group**

**By Region:**
- 🇺🇸 USA: 12 groups
- 🇦🇺 Australia: 6 groups
- 🇬🇧 UK/Europe: 4 groups
- 🇨🇦 Canada: 1 group

**Data Export:**
- JSON: `modules/scraping/results/reenactment_clubs_quick_20251102_101718.json`
- CSV: `modules/scraping/results/reenactment_clubs_quick_20251102_101718.csv`

---

## 🎯 KEY FINDINGS

### Verified Email Contacts (6):
1. **Re-enact SA** (Australia)
   📧 cplusk@bigpond.com.au
   ☎️ +61 403 175 353
   📍 86 Baker Street Glengowrie SA 5044

2. **Finland At War**
   📧 info@atwar.fi
   🌍 Finland (WWII Winter/Continuation War)

3. **Finland At War UK**
   📧 finlandatwar@gmail.com
   🌍 United Kingdom

4. **Air Transport Auxiliary Re-Enactment Group**
   📧 carolechalmers1@gmail.com
   🌍 UK (WWII ATA)

5. **29th Division Living History Group**
   📧 29th.id.lhu@gmail.com
   🌍 USA (WWII)

6. **National Museum of the Pacific War**
   📧 ghanson@nimitzfoundation.org
   👤 Grant Hanson (Living History Coordinator)
   🌍 Texas, USA

### Major Groups with Websites (No Public Email):
- AUSREENACT (NSW, Australia) - https://www.ausreenact.com.au/
- WWII Historical Reenactment Society (USA) - https://worldwartwohrs.org/
- 26th Infantry Division - Yankee Division (USA) - https://26yd.com/
- California Historical Group (USA) - https://www.chgww2.net/
- Geelong Military Re-enactment Group (Australia) - http://geelongmrg.com/
- Alberta World War Living History Association (Canada) - https://www.awwlha.com/

---

## 🛠️ TOOLS CREATED

### 1. Known Groups Database
**File:** `modules/scraping/data/known_groups.json`
**Contains:** 23 manually researched and verified groups

### 2. Quick Collector Script
**File:** `modules/scraping/scripts/quick_collector.py`
**Purpose:** Load and export known groups
**Usage:** `python quick_collector.py`

### 3. Email Extractor
**File:** `modules/scraping/scripts/extract_emails_from_websites.py`
**Purpose:** Extract emails from individual websites
**Usage:** Provide list of URLs, extracts contact emails

### 4. Mass Website Collector
**File:** `modules/scraping/scripts/mass_website_collector.py`
**Purpose:** Scan directories, collect websites, extract emails
**Status:** Created but requires optimization

### 5. Apollo API Search
**File:** `modules/scraping/scripts/apollo_reenactment_search.py`
**Purpose:** Search organizations via Apollo API
**Status:** API returning 403 (rate limit/permissions issue)

---

## 📚 DATA SOURCES IDENTIFIED

### Primary Directories (High Value):
1. **Historic-UK Living History Directory**
   🔗 https://www.historic-uk.com/LivingHistory/ReenactorsDirectory/
   📄 24 pages of UK-based groups with contact info

2. **WWII Dog Tags - Reenacting Units**
   🔗 https://wwiidogtags.com/ww2-reenacting-units/
   📄 Comprehensive US/International listing

3. **Living History Archive**
   🔗 https://www.livinghistoryarchive.com/group/ww2-reenactment-groups
   📄 Groups from USA, UK, Europe, Australia

4. **Milsurpia - WW2 Reenactors**
   🔗 https://www.milsurpia.com/reenactment-groups/world-war-2-reenactors
   📄 Searchable directory of units

5. **ReenactmentHQ - Unit List**
   🔗 https://reenactmenthq.com/reenactment-unit-list/
   📄 Modern listing with contact forms

6. **Reenactor.net - WWII Organizations**
   🔗 https://www.reenactor.net/index.php?page=70
   📄 Parent organizations and events

### Regional Resources:

**Australia:**
- Australasian Living History Federation - https://www.alhf.org.au/mem_grps.html
- Australian Re-enactors Association - http://re-enactors.org.au/

**Canada:**
- Limited dedicated directories found
- Alberta WWLHA is main contact point

**Europe:**
- Epic Militaria Groups - https://www.epicmilitaria.com/reenactment
- Country-specific searches needed (Germany, France, Poland)

---

## 🚀 STRATEGY TO REACH 300+ CONTACTS

### Phase 1: Automated Website Crawling (Est. 100-150 contacts)
**Approach:** Systematically crawl directory websites and extract group links

**Steps:**
1. Parse all 24 pages of Historic-UK (UK groups with direct emails)
2. Scrape WWIIDogTags unit list (50+ US groups)
3. Process Milsurpia directory (40+ groups)
4. Extract from Living History Archive listings
5. For each website found → visit → extract email from contact page

**Script:** Use `mass_website_collector.py` (needs debugging)
**Time Estimate:** 2-3 hours automated runtime
**Expected Yield:** 100-150 unique contacts

### Phase 2: Apollo API Organizations (Est. 50-100 contacts)
**Approach:** Fix Apollo API integration and search for organizations

**Keywords to search:**
- "historical reenactment"
- "WWII reenactment"
- "living history"
- "military reenactment"
- "war reenactment societies"

**Issue:** Currently getting 403 errors
**Solution Needed:**
- Verify API key permissions
- Check rate limits
- Try alternative search parameters

**Expected Yield:** 50-100 organizations with websites

### Phase 3: Manual Research - High-Value Sources (Est. 50-100 contacts)

**Facebook Groups (Extract admin emails):**
- Search "WWII reenactment" groups
- Contact group admins for official emails

**Event Organizers:**
- D-Day events (Conneaut, Normandy)
- Battle reenactments (check event websites for organizer contacts)

**Museum Living History Programs:**
- National WWII Museum (New Orleans)
- Imperial War Museum (UK)
- Australian War Memorial

**Expected Yield:** 50-100 verified contacts

### Phase 4: Targeted Country Searches (Est. 50-100 contacts)

**USA - State-by-State:**
- Search "{State} WWII reenactment groups"
- Check state historical societies

**Germany/Austria:**
- Search "Geschichtsdarstellung Zweiter Weltkrieg"
- Check history clubs websites

**France:**
- Search "reconstitution historique seconde guerre mondiale"

**Poland:**
- Search "rekonstrukcja historyczna II wojna"

**Expected Yield:** 50-100 additional European groups

---

## 📋 IMMEDIATE NEXT STEPS

### Option A: Quick Manual Expansion (Recommended)
1. Visit each of 17 websites we have (no email yet)
2. Find contact page / email manually
3. Add to database
4. **Time:** 1-2 hours
5. **Yield:** ~10-15 new emails

### Option B: Fix & Run Mass Collector
1. Debug `mass_website_collector.py` (add print buffering fix)
2. Run on 4 main directories
3. Let script run overnight
4. **Time:** 6-8 hours automated
5. **Yield:** 100-150 contacts

### Option C: Hire VA / Use Service
1. Hire Virtual Assistant on Upwork
2. Provide them with directory list
3. Task: Extract all contact emails
4. **Cost:** $50-100
5. **Time:** 1-2 days
6. **Yield:** 200-300 contacts

---

## 🔧 TECHNICAL NOTES

### Why Web Scraping is Challenging:
1. **No centralized database** - groups are dispersed across hundreds of independent websites
2. **Contact info hidden** - most require visiting individual "Contact" pages
3. **Rate limiting** - directories block aggressive scraping
4. **Dynamic content** - many sites use JavaScript (need Selenium, not allowed per project rules)
5. **Format variety** - each website structures data differently

### Constraints Applied:
- ✅ HTTP-only scraping (requests + BeautifulSoup)
- ❌ No Selenium/browser automation
- ❌ No Firecrawl or external scraping services
- ✅ Respect rate limits (2-5 second delays)

---

## 💡 RECOMMENDATIONS

### For Quick Results (1-2 days):
1. **Manual Processing** of 17 known websites (extract emails)
2. **Contact Major Organizations** (WWII HRS, ALHF) - ask for member lists
3. **Facebook Group Mining** - join groups, collect admin contacts

### For 300+ Contacts (1 week):
1. **Fix and optimize** mass collector script
2. **Run automated collection** on all directories (overnight)
3. **Apollo API debugging** - get organization data
4. **Supplement with manual research** for remaining gap

### Alternative Approach:
Instead of collecting 300 individual clubs, target **umbrella organizations**:
- WWII Historical Reenactment Society (USA) - has member units list
- Australasian Living History Federation - directory of Australian groups
- These organizations can provide bulk contact lists for their members

---

## 📊 FILES GENERATED

1. **Known Groups JSON:**
   `modules/scraping/data/known_groups.json` (23 groups)

2. **Quick Export JSON:**
   `modules/scraping/results/reenactment_clubs_quick_20251102_101718.json`

3. **Quick Export CSV:**
   `modules/scraping/results/reenactment_clubs_quick_20251102_101718.csv`

4. **Historic-UK Test:**
   `modules/scraping/results/historic_uk_test_20251102_100129.json` (33 groups from 3 pages)

---

## ✅ CONCLUSIONS

**Current Status:**
✅ Solid foundation with 23 verified groups (6 emails, 17 websites)
✅ Multiple collection tools created and ready
✅ Comprehensive list of data sources identified
⏳ Need more time/resources to scale to 300+

**Realistic Timeline:**
- **Quick wins (50 contacts):** 1-2 days
- **Moderate scale (100-150):** 3-5 days
- **Full target (300+):** 1-2 weeks

**Best Next Action:**
Contact **umbrella organizations** (WWII HRS, ALHF, ARA) and request member directories - this is faster than scraping 300 individual websites.

---

**Generated:** 2025-11-02
**Project:** Cold Outreach - new
**Module:** modules/scraping
