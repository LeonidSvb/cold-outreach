# Australia + New Zealand Hospitality Leads Strategy

## 🎯 Overview

Comprehensive scraping of **restaurants, cafes, hotels, and accommodation** businesses across Australia and New Zealand.

---

## 📊 Collection Plan

### Target Categories (30 Priority)

#### **Tier 1: Core Dining (10 categories)**
High-volume, essential food service businesses
```
1. restaurant           - General restaurants (largest segment)
2. cafe                 - Cafes and coffee shops
3. coffee_shop          - Specialty coffee venues
4. bar                  - Bars and drinking establishments
5. pub                  - Pubs (especially strong in AU/NZ)
6. fast_food_restaurant - Quick service restaurants
7. pizzeria             - Pizza restaurants
8. bakery               - Bakeries and pastry shops
9. breakfast_restaurant - Breakfast/brunch spots
10. italian_restaurant  - Italian cuisine (popular in AU/NZ)
```

#### **Tier 2: Accommodation (5 categories)**
Hotels, motels, and lodging businesses
```
11. hotel               - Full-service hotels
12. motel               - Roadside motels
13. bed_and_breakfast   - B&Bs and guest houses
14. hostel              - Hostels and backpacker lodges
15. resort_hotel        - Resort properties
```

#### **Tier 3: Specialty Dining (10 categories)**
Ethnic and specialty restaurants
```
16. chinese_restaurant    - Chinese cuisine
17. thai_restaurant       - Thai cuisine (very popular)
18. indian_restaurant     - Indian cuisine
19. japanese_restaurant   - Japanese cuisine
20. sushi_restaurant      - Sushi specialists
21. seafood_restaurant    - Seafood (strong in coastal AU/NZ)
22. steak_house           - Steakhouses
23. mexican_restaurant    - Mexican cuisine
24. french_restaurant     - French fine dining
25. vietnamese_restaurant - Vietnamese cuisine
```

#### **Tier 4: Quick Service & Specialty (5 categories)**
Fast casual and niche venues
```
26. sandwich_shop       - Sandwich and sub shops
27. hamburger_restaurant - Burger joints
28. ice_cream_shop      - Ice cream parlors
29. wine_bar            - Wine bars and tasting rooms
30. bistro              - Casual bistros
```

---

## 💰 Economics

### Free Tier Optimization

**Apify Free Tier:**
- $5 free credits on signup
- 100 leads per category limit (to maximize free value)

**Collection Strategy:**
```
30 categories × 2 countries × 50 leads = 3,000 leads
Cost: 3,000 × $0.0019 = $5.70

Strategy: Use $5 free credit + ~$0.70 overage
```

### Cost Breakdown
```
Australia: 30 categories × 50 leads = 1,500 leads ($2.85)
New Zealand: 30 categories × 50 leads = 1,500 leads ($2.85)
────────────────────────────────────────────────────
TOTAL: 3,000 hospitality leads ($5.70)
```

**Value Proposition:**
- Industry average: $0.10-0.50 per B2B lead
- Your cost: $0.0019 per lead
- **ROI: 50-250x cheaper than buying leads!**

---

## 🚀 Usage

### Quick Start

**1. Test with single category (30 seconds, ~$0.10):**
```bash
python modules/apify/scripts/test_apify_actor.py
```

**2. Full hospitality collection (2-3 hours, $5.70):**
```bash
python modules/apify/scripts/australia_hospitality_scraper.py
```

### What to Expect

**Runtime:**
- 60 actor runs (30 categories × 2 countries)
- ~3 minutes per run average
- **Total: 2-3 hours** (runs automatically)

**Output:**
```
modules/apify/results/hospitality_au_nz_20251121_HHMMSS.csv
```

**CSV Columns:**
```csv
name,email,phone,website,address,city,country,source_country,source_category
Sunrise Cafe,info@sunrise.com.au,0412345678,sunrise.com.au,"123 Main St",Sydney,AU,Australia,cafe
```

---

## 📈 Expected Data Quality

Based on Apify actor performance in hospitality sector:

| Field | Coverage | Quality |
|-------|----------|---------|
| **Business Name** | 100% | Excellent |
| **Phone** | 95-98% | Excellent |
| **Email** | 75-85% | Good |
| **Website** | 80-90% | Excellent |
| **Address** | 100% | Excellent |
| **Reviews** | 90% | Excellent |

**Why hospitality has better data:**
- Online presence mandatory (bookings, orders)
- Customer-facing businesses (need to be found)
- Google Business Profile compliance
- Review culture (TripAdvisor, Google, Yelp)

---

## 🎯 Cold Outreach Potential

### Perfect Use Cases for These Leads

**1. Restaurant Management Software**
- POS systems
- Inventory management
- Staff scheduling
- Online ordering platforms

**2. Marketing Services**
- Social media management
- Google Business optimization
- Online reputation management
- Email marketing automation

**3. Payment Processing**
- Merchant services
- POS hardware
- Online payment gateways
- Tip management systems

**4. Delivery & Logistics**
- Food delivery integration
- DoorDash/UberEats optimization
- Delivery fleet management

**5. Hospitality Tech**
- Booking systems (hotels/B&Bs)
- Table reservation software
- Customer loyalty programs
- Review management tools

**6. Business Services**
- Accounting software
- Payroll services
- Insurance (specialized hospitality)
- Cleaning/maintenance services

---

## 📊 Segmentation Strategy

### By Category Type

**High-Touch Service (Best for complex solutions):**
- Hotels, resorts, B&Bs
- Fine dining restaurants
- Longer sales cycles but higher value

**Volume Players (Best for transactional products):**
- Fast food, cafes, coffee shops
- Quick service restaurants
- Shorter sales cycles, lower ticket

**Specialty Venues (Best for niche solutions):**
- Wine bars, bistros, ethnic restaurants
- Unique pain points per category
- Medium complexity

### By Geography

**Australia Opportunities:**
- Larger market (67M population + tourism)
- Higher GDP per capita
- Strong food culture (multicultural)
- Major cities: Sydney, Melbourne, Brisbane

**New Zealand Opportunities:**
- Smaller but premium market
- Tourism-heavy (international visitors)
- English-speaking (easy outreach)
- Major cities: Auckland, Wellington, Christchurch

---

## 🔧 Customization Options

### Add More Categories

Edit `australia_hospitality_scraper.py`:

```python
CATEGORIES = {
    'Australia': [
        # Add your category
        {'category': 'korean_restaurant', 'max_results': 50},
        {'category': 'buffet_restaurant', 'max_results': 50},
        # etc...
    ]
}
```

### Adjust Lead Limits

```python
# For premium accounts (no 100 limit):
{'category': 'restaurant', 'max_results': 200},  # Get more leads

# For free tier optimization:
{'category': 'restaurant', 'max_results': 50},   # Stay under 100
```

### Change Geographic Split

```python
# 70% Australia, 30% New Zealand
'Australia': [...],  # max_results: 70 each
'New Zealand': [...],  # max_results: 30 each

# 50/50 split (current)
Both: 50 each
```

---

## 🔍 Additional Categories Available

See `hospitality_categories.txt` for **full list of 135+ categories** including:

**Specialty Dining:**
- korean_restaurant, greek_restaurant, lebanese_restaurant
- ramen_restaurant, noodle_shop, dumpling_restaurant
- vegetarian_restaurant, vegan_restaurant

**Bars & Nightlife:**
- cocktail_bar, sports_bar, karaoke_bar
- brewery, winery, distillery

**Quick Service:**
- taco_restaurant, burrito_restaurant
- fish_and_chips, kebab_shop

**Accommodation:**
- guest_house, serviced_apartment
- campground, rv_park

**Food Services:**
- catering, meal_delivery, food_court

---

## 📋 Data Fields Available

### Core Fields (Always Present)
- `name` - Business name
- `phone` - Phone number
- `address` - Full address
- `city` - City
- `country` - AU or NZ
- `source_country` - Which country run
- `source_category` - Which category run

### Rich Fields (Usually Present)
- `email` - Email address (75-85% coverage)
- `website` / `url` - Website URL (80-90%)
- `google_maps_url` - Google Maps link
- `review_score` - Average rating (1-5)
- `reviews_number` - Total review count
- `street` - Street address component

### Social Media (If Available)
- `facebook` - Facebook page URL
- `instagram` - Instagram profile
- `linkedin` - LinkedIn company page

### Business Info
- `google_business_categories` - All assigned categories

---

## ⚠️ Important Notes

### Rate Limiting
Script includes automatic delays:
- 10 seconds between runs
- Prevents Apify rate limits
- Total runtime: 2-3 hours

### Error Handling
Built-in resilience:
- Automatic retries on failure
- Partial results saved on interruption
- Progress tracking throughout

### Free Tier Limits
Apify free account:
- $5 monthly credit
- Resets each month
- No credit card required for signup

### Category Validation
Not all categories may be available in all regions:
- Some specialty cuisines rare in certain areas
- Actor will return empty if no businesses found
- Script handles this gracefully

---

## 🎓 Best Practices

### Data Enrichment Post-Collection

**1. Email Verification**
- Use Hunter.io, ZeroBounce, or NeverBounce
- Validate deliverability before outreach
- Expected: 10-15% invalid/bounce rate

**2. Phone Validation**
- Check format consistency
- Verify area codes
- Consider SMS validation for high-value leads

**3. Website Checks**
- Verify sites are live (not all will be)
- Check for contact forms
- Assess technology stack (if relevant to your offer)

**4. Review Analysis**
- Filter by review count (>10 reviews = established)
- Sort by rating (4+ stars = quality businesses)
- Recent reviews = currently operating

### Outreach Optimization

**Timing:**
- Restaurants: Tue-Thu, 2-4pm (between lunch/dinner rush)
- Hotels: Mon-Fri, 9-11am (front desk available)
- Cafes: Mon-Fri, 10am-12pm (post-morning rush)

**Messaging:**
- Industry-specific pain points
- Quick value proposition (they're busy)
- Clear CTA (book call, demo, trial)

**Multi-Channel:**
- Email primary channel
- Phone follow-up (if no email response)
- LinkedIn for decision-makers (hotels, chains)

---

## 📞 Support & Next Steps

### Troubleshooting

**"Actor failed" error:**
- Check category spelling
- Verify APIFY_API_KEY in .env
- Try test script first

**"No results returned":**
- Category may not exist in region
- Try alternative category name
- Check Apify actor documentation

**"Rate limit exceeded":**
- Script already includes delays
- If still occurring, increase delay in code
- Consider spreading runs over multiple days

### Extending to Other Markets

Want to expand beyond AU/NZ?

**Easy additions (English-speaking):**
- United Kingdom (GB)
- Ireland (IE)
- Singapore (SG)
- Canada (CA)

**Medium difficulty (high English proficiency):**
- Netherlands (NL)
- Sweden (SE)
- Denmark (DK)
- Norway (NO)

Just modify country codes in script!

---

## 📚 Resources

**Apify Actor Page:**
https://apify.com/xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps

**Google Business Categories:**
https://support.google.com/business/answer/3038177

**Project Documentation:**
- `modules/apify/README.md` - General Apify usage
- `docs/learning/apify-анализ-build-vs-buy.md` - Economic analysis

---

**Created:** 2025-11-21
**Last Updated:** 2025-11-21
**Status:** Production Ready ✅
