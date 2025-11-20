# 🚀 Hospitality Leads Collection - Quick Start

## TL;DR
Collect **3,000 restaurant, cafe, and hotel leads** from Australia + New Zealand for **$5.70** in **2-3 hours**.

---

## ⚡ Super Quick Start (3 Commands)

```bash
# 1. Test category (30 seconds, $0.02)
python modules/apify/scripts/test_hospitality_category.py

# 2. Full collection (2-3 hours, $5.70)
python modules/apify/scripts/australia_hospitality_scraper.py

# 3. Results ready!
# File: modules/apify/results/hospitality_au_nz_TIMESTAMP.csv
```

---

## 📊 What You'll Get

### 3,000 High-Quality Leads
- ✅ **1,500 Australia** (Sydney, Melbourne, Brisbane, etc.)
- ✅ **1,500 New Zealand** (Auckland, Wellington, Christchurch)

### 30 Premium Categories
```
Restaurants:     restaurant, cafe, pizzeria, italian, chinese, thai,
                 indian, japanese, sushi, seafood, steak, mexican,
                 french, vietnamese, fast_food, breakfast, bistro

Quick Service:   sandwich_shop, hamburger, bakery, coffee_shop,
                 ice_cream_shop

Bars:            bar, pub, wine_bar

Accommodation:   hotel, motel, bed_and_breakfast, hostel, resort_hotel
```

### Rich Data Fields
```csv
name,email,phone,website,address,city,rating,reviews,category
Sunrise Cafe,info@sunrise.com.au,0412345678,sunrise.com.au,"123 Main St",Sydney,4.5,127,cafe
```

**Data Coverage:**
- 📧 Email: 75-85%
- 📞 Phone: 95-98%
- 🌐 Website: 80-90%
- ⭐ Reviews: 90%

---

## 💰 Cost Breakdown

```
3,000 leads × $0.0019/lead = $5.70

Compare to:
- Buying leads: $0.10-0.50 each = $300-1,500
- Your cost: $5.70
- Savings: 98% cheaper! 🎉
```

**Free Tier Option:**
Apify gives $5 free credits → Pay only $0.70!

---

## 🎯 Perfect For

### SaaS Products
- POS systems
- Booking software
- Inventory management
- Online ordering platforms
- Table reservation systems

### Services
- Payment processing
- Marketing/SEO services
- Website development
- Social media management
- Accounting software

### Tech Solutions
- Delivery integration
- Review management
- Loyalty programs
- Staff scheduling
- Email automation

---

## 📋 Prerequisites

**1. Apify API Key**
```bash
# Sign up at: https://apify.com
# Free account gives $5 credit
# Copy API key to .env file
```

**2. Environment Setup**
```bash
# Add to .env file:
APIFY_API_KEY=your_key_here
```

**3. Python Dependencies**
```bash
py -m pip install apify-client requests python-dotenv
```

---

## 🔍 Test First (Recommended!)

Before spending $5.70, test with **10 leads** ($0.02):

```bash
python modules/apify/scripts/test_hospitality_category.py
```

**You'll see:**
- Sample restaurant data
- Data quality stats
- Field availability
- Verify categories work

**Takes:** 30 seconds
**Cost:** $0.02

---

## 🚀 Full Collection

When test looks good:

```bash
python modules/apify/scripts/australia_hospitality_scraper.py
```

**What happens:**
1. Starts 60 actor runs (30 categories × 2 countries)
2. Collects 50 leads per category per country
3. Shows progress in real-time
4. Saves to CSV automatically
5. Prints summary statistics

**Runtime:** 2-3 hours (automatic, can walk away)
**Cost:** $5.70
**Output:** `modules/apify/results/hospitality_au_nz_TIMESTAMP.csv`

---

## 📂 Results Location

```
modules/apify/results/
└── hospitality_au_nz_20251121_143022.csv  ← Your file
```

**CSV Preview:**
```csv
name,email,phone,website,address,city,country,source_country,source_category,rating,reviews
The Local Cafe,hello@localcafe.com.au,0412345678,localcafe.com.au,"45 Smith St",Melbourne,AU,Australia,cafe,4.7,234
Auckland Hotel,info@auckhotel.co.nz,021987654,auckhotel.co.nz,"78 Queen St",Auckland,NZ,New Zealand,hotel,4.3,567
```

---

## 💡 Pro Tips

### 1. Best Categories for Your Offer

**Need high email coverage?**
→ Focus on: hotel, restaurant, cafe (80-90% have emails)

**Need phone numbers?**
→ All categories excellent (95%+ have phones)

**Want established businesses?**
→ Filter by reviews > 50 (reliable, operating long-term)

### 2. Optimize Collection

**Limited budget?**
→ Reduce to top 15 categories = 1,500 leads ($2.85)

**Want more leads?**
→ Increase max_results to 100 per category = 6,000 leads ($11.40)

**Other regions?**
→ Easy to add UK, Ireland, Singapore, Canada

### 3. Post-Collection

**Email Verification:**
- Hunter.io, ZeroBounce, NeverBounce
- Expect 10-15% invalid rate

**Segmentation:**
- By category (restaurants vs hotels)
- By location (major cities first)
- By rating (4+ stars = quality)
- By review count (>50 = established)

**Outreach Timing:**
- Restaurants: Tue-Thu, 2-4pm
- Hotels: Mon-Fri, 9-11am
- Cafes: Mon-Fri, 10am-12pm

---

## 🔧 Customization

### Change Categories

Edit `australia_hospitality_scraper.py`:

```python
CATEGORIES = {
    'Australia': [
        {'category': 'korean_restaurant', 'max_results': 50},  # Add new
        {'category': 'buffet_restaurant', 'max_results': 50},
        # ... your categories
    ]
}
```

### Adjust Lead Counts

```python
# Get more leads per category
{'category': 'restaurant', 'max_results': 100},  # 100 each

# Free tier optimization (stay under 100 limit)
{'category': 'restaurant', 'max_results': 50},   # 50 each
```

### Add More Countries

```python
CATEGORIES = {
    'Australia': [...],
    'New Zealand': [...],
    'United Kingdom': [...],    # Add GB
    'Singapore': [...],          # Add SG
}

COUNTRY_CODES = {
    'Australia': 'AU',
    'New Zealand': 'NZ',
    'United Kingdom': 'GB',      # Add code
    'Singapore': 'SG',           # Add code
}
```

---

## 📚 Full Documentation

**Strategy & Economics:**
→ `modules/apify/docs/HOSPITALITY_STRATEGY.md`

**All Available Categories (135+):**
→ `modules/apify/scripts/hospitality_categories.txt`

**General Apify Usage:**
→ `modules/apify/README.md`

**Build vs Buy Analysis:**
→ `docs/learning/apify-анализ-build-vs-buy.md`

---

## ⚠️ Important Notes

### Rate Limiting
- Script includes automatic 10-second delays
- Don't modify delays (prevents rate limits)
- Total runtime: 2-3 hours (normal)

### Error Handling
- Auto-retry on failures
- Partial results saved if interrupted
- Progress tracked throughout

### Free Tier
- $5 monthly credit (resets each month)
- No credit card required
- Perfect for testing before scaling

### Category Availability
- Not all categories in all regions
- Script handles empty results gracefully
- Some specialty cuisines may be rare

---

## 🆘 Troubleshooting

**"Failed to start run: 401"**
→ Check APIFY_API_KEY in .env file

**"Run failed: FAILED"**
→ Category name might be invalid, try test script first

**"No results returned"**
→ Category doesn't exist in that region, try alternative

**"Rate limit exceeded"**
→ Script already has delays, if persists increase delay time

---

## 📞 Support

**Questions?**
- Check documentation in `modules/apify/docs/`
- Review Apify actor page: https://apify.com/xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps

**Next Steps:**
1. Run test script
2. Review sample data
3. Run full collection
4. Enrich & validate data
5. Start cold outreach!

---

**Ready to collect 3,000 hospitality leads for $5.70?**

```bash
# Test first!
python modules/apify/scripts/test_hospitality_category.py

# Then full run
python modules/apify/scripts/australia_hospitality_scraper.py
```

🚀 **Good luck with your cold outreach campaigns!**
