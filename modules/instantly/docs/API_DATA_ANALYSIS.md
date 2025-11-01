# Instantly API v2 - Complete Data Analysis

Based on real API endpoint testing (Nov 1, 2025)

---

## ✅ WORKING ENDPOINTS (Full Data Available)

### 1. `/campaigns` - Campaign Configuration
**Method:** GET
**Response:** `{items: [...], next_starting_after: "..."}`
**Records:** 5 campaigns found

**Data Structure:**
```json
{
  "id": "8ad64aaf-8294-4538-8400-4a99dcf016e8",
  "name": "Marketing agencies",
  "status": 1,  // 1=Active, 2=Paused, 3=Completed, -1=Unhealthy, -2=Bounce
  "timestamp_created": "2025-09-12T10:02:21.146Z",
  "timestamp_updated": "2025-10-30T01:09:44.198Z",
  "pl_value": 100,

  // CAMPAIGN SCHEDULE
  "campaign_schedule": {
    "schedules": [{
      "name": "New schedule",
      "timing": {"from": "07:00", "to": "19:00"},
      "days": {1:true, 2:true, 3:true, 4:true, 5:true, 6:true},
      "timezone": "America/Detroit"
    }],
    "start_date": "",
    "end_date": ""
  },

  // EMAIL SEQUENCES (FULL CAMPAIGN STEPS!)
  "sequences": [{
    "steps": [
      {
        "type": "email",
        "delay": 2,
        "variants": [{
          "subject": "{{firstName}},  12 qual appointments → $14.5K?",
          "body": "<div>{{personalization}}...</div>"
        }]
      },
      {
        "type": "email",
        "delay": 1,
        "variants": [{
          "subject": "following up",
          "body": "<div>{{firstName}} - figured you might've missed this...</div>"
        }]
      }
    ]
  }],

  // SETTINGS
  "text_only": true,
  "first_email_text_only": false,
  "email_list": [],
  "daily_limit": 900,
  "stop_on_reply": true,
  "email_tag_list": ["5bf588e3-...", "7e4dc321-..."],
  "link_tracking": false,
  "open_tracking": false,
  "stop_on_auto_reply": false,

  // ROUTING RULES
  "provider_routing_rules": [
    {
      "action": "send",
      "recipient_esp": ["all", "google"],
      "sender_esp": ["google"]
    }
  ],

  "organization": "c6ea1bfd-6fac-4e41-925c-4628477e2954",
  "owned_by": "4da98da8-2c37-4bf7-84da-1b76914b6dcb"
}
```

**RICHNESS:** ⭐⭐⭐⭐⭐ (MOST DETAILED!)
- Full campaign configuration
- Email sequences with templates
- Schedules and timezones
- Routing rules
- All settings

---

### 2. `/campaigns/analytics` - Campaign Metrics
**Method:** GET
**Response:** Array of campaigns
**Records:** 4 campaigns

**Data Structure:**
```json
{
  "campaign_name": "Marketing agencies",
  "campaign_id": "8ad64aaf-8294-4538-8400-4a99dcf016e8",
  "campaign_status": 2,
  "campaign_is_evergreen": false,

  // LEAD STATS
  "leads_count": 735,
  "contacted_count": 552,
  "completed_count": 152,
  "new_leads_contacted_count": 552,

  // EMAIL PERFORMANCE
  "emails_sent_count": 700,
  "open_count": 0,
  "reply_count": 4,
  "link_click_count": 0,
  "bounced_count": 18,
  "unsubscribed_count": 0,

  // OPPORTUNITIES
  "total_opportunities": 0,
  "total_opportunity_value": 0
}
```

**RICHNESS:** ⭐⭐⭐⭐
- Summary metrics only
- No sequences or details

---

### 3. `POST /leads/list` - Lead Data
**Method:** POST
**Payload:** `{"campaign_id": "...", "limit": 100}`
**Max Limit:** 100 (NOT 1000!)
**Response:** `{items: [...], next_starting_after: "..."}`
**Records:** 735 leads in Campaign 1 alone

**Data Structure:**
```json
{
  "id": "00113f1e-b4a9-4d29-871c-a9b8f2da7a61",
  "timestamp_created": "2025-09-12T10:09:54.426Z",
  "timestamp_updated": "2025-09-12T10:09:54.426Z",
  "organization": "c6ea1bfd-6fac-4e41-925c-4628477e2954",

  // LEAD INFO
  "email": "dan@emerge2.com",
  "first_name": "Dan",
  "last_name": "Reid",
  "company_name": "Emerge2",
  "company_domain": "emerge2.com",
  "phone": "+12159472080",

  // STATUS
  "status": 3,  // 0=Active, 1=Contacted, 2=Replied, 3=Completed, etc.
  "email_open_count": 0,
  "email_reply_count": 0,
  "email_click_count": 0,

  // CAMPAIGN
  "campaign": "8ad64aaf-8294-4538-8400-4a99dcf016e8",

  // PERSONALIZATION
  "personalization": "Hey Dan, awesome to see you lead marketing at Emerge2...",

  // FULL PAYLOAD (all custom fields!)
  "payload": {
    "firstName": "Dan",
    "lastName": "Reid",
    "companyName": "Emerge2",
    "personalization": "Hey Dan...",
    "email": "dan@emerge2.com",
    "jobTitle": "CEO",
    "linkedIn": "http://linkedin.com/in/...",
    "location": "Waterloo",
    "phone": "+1234567890"
  },

  // CONTACT HISTORY
  "status_summary": {
    "lastStep": {
      "from": "arthur@alphamicroltd.org",
      "stepID": "0_1_0",
      "timestamp_executed": "2025-09-15T11:04:20.549Z"
    }
  },

  "timestamp_last_contact": "2025-09-15T11:04:20.549Z",
  "timestamp_last_touch": "2025-09-15T11:04:20.549Z",

  // UPLOAD
  "upload_method": "manual",  // or "api"
  "list_id": "e747badb-0211-411d-bf87-7699260ea914",
  "uploaded_by_user": "4da98da8-2c37-4bf7-84da-1b76914b6dcb",
  "assigned_to": "4da98da8-2c37-4bf7-84da-1b76914b6dcb",

  // ESP
  "esp_code": 1  // 1=Gmail, 2=Outlook, 3=Yahoo, 999=Unknown
}
```

**RICHNESS:** ⭐⭐⭐⭐⭐ (EXTREMELY DETAILED!)
- Full lead information
- Custom fields in payload
- LinkedIn, phone, location
- Contact history
- Status tracking

**PAGINATION:** Yes! Use `next_starting_after` to get next 100

---

### 4. `/accounts` - Email Accounts
**Method:** GET
**Response:** `{items: [...], next_starting_after: "..."}`
**Records:** 10 accounts found

**Data Structure:**
```json
{
  "email": "leo@dosystemhustle.com",
  "status": 1,  // 1=Active, -1=Inactive
  "warmup_status": 1,
  "stat_warmup_score": 87.5,
  "organization": "c6ea1bfd-6fac-4e41-925c-4628477e2954",
  "timestamp_created": "2025-08-20T10:15:30.000Z",
  "provider": "google",
  "daily_limit": 50
}
```

**RICHNESS:** ⭐⭐⭐
- Account status
- Warmup scores
- Daily limits

---

### 5. `/campaigns/analytics/overview` - Global Overview
**Method:** GET
**Response:** Single object

**Data Structure:**
```json
{
  "open_count": 62,
  "open_count_unique": 45,
  "open_count_unique_by_step": [20, 15, 10],

  "link_click_count": 0,
  "link_click_count_unique": 0,
  "link_click_count_unique_by_step": [],

  "reply_count": 13,
  "reply_count_unique": 11,
  "reply_count_unique_by_step": [4, 5, 2],

  "bounced_count": 60,
  "unsubscribed_count": 0,
  "emails_sent_count": 1668,
  "new_leads_contacted_count": 1161,

  "total_opportunities": 2,
  "total_opportunity_value": 200,
  "total_interested": 0,
  "total_meeting_booked": 0,
  "total_meeting_completed": 0,
  "total_closed": 0
}
```

**RICHNESS:** ⭐⭐⭐⭐
- Account-wide metrics
- By-step breakdowns

---

### 6. `/campaigns/analytics/daily` - Daily Metrics
**Method:** GET
**Query:** `?start_date=2025-08-03&end_date=2025-11-01`
**Response:** Array of daily records
**Records:** 18 days found

**Data Structure:**
```json
{
  "date": "2025-09-15",
  "sent": 150,
  "opened": 0,
  "unique_opened": 0,
  "replies": 2,
  "unique_replies": 2,
  "clicks": 0,
  "unique_clicks": 0,
  "opportunities": 0,
  "unique_opportunities": 0
}
```

**RICHNESS:** ⭐⭐⭐
- Daily performance trends
- Can filter by campaign_id

---

### 7. `/campaigns/analytics/steps` - Step Analytics
**Method:** GET
**Query:** `?campaign_id={id}`
**Response:** Array of steps
**Records:** 2-3 steps per campaign

**Data Structure:**
```json
{
  "step": 1,
  "variant": 0,
  "sent": 500,
  "opened": 0,
  "unique_opened": 0,
  "replies": 3,
  "unique_replies": 3,
  "clicks": 0,
  "unique_clicks": 0
}
```

**RICHNESS:** ⭐⭐⭐
- Step-by-step performance
- A/B variant tracking

---

## ❌ NOT WORKING ENDPOINTS

### 1. `/emails` - Email Details
**Status:** 400 Bad Request
**Error:** `limit must be <= 100`
**Issue:** Need to test with limit=100 and pagination

### 2. `POST /leads/list` without campaign_id
**Status:** 400 Bad Request
**Issue:** campaign_id is REQUIRED

---

## 📊 DATA VOLUME ESTIMATES

Based on Campaign 1 analytics:

```
Campaigns:       4-5 total
Leads:           735+ (Campaign 1 alone!)
                 Estimated 1,000-2,000 total across all campaigns

Accounts:        10 email accounts

Daily Analytics: 18 days recorded (can go back 90+ days)

Steps:           2-3 per campaign = 8-12 total

Campaigns Config: RICH data (sequences, schedules, templates)
```

---

## 🎯 RECOMMENDED DATA COLLECTION STRATEGY

### Priority 1: Core Data (Must Have)
1. ✅ `/campaigns` - Full campaign configurations
2. ✅ `POST /leads/list` - All leads (with pagination!)
3. ✅ `/accounts` - Email accounts
4. ✅ `/campaigns/analytics` - Campaign metrics

### Priority 2: Analytics (Nice to Have)
5. ✅ `/campaigns/analytics/overview` - Global summary
6. ✅ `/campaigns/analytics/daily` - Daily trends (last 90 days)
7. ✅ `/campaigns/analytics/steps` - Step performance

### Priority 3: Detailed Events (If Available)
8. ⚠️ `/emails` - Individual email events (need to test limit=100)

---

## 🔧 CRITICAL FIXES NEEDED

### 1. Leads Collection
**OLD (Wrong):**
```python
data = {"campaign_id": campaign_id, "limit": 1000}  # ❌ FAILS!
response = api_call("/leads/list", POST, data)
leads = response.get('leads', [])  # ❌ Wrong key!
```

**NEW (Correct):**
```python
data = {"campaign_id": campaign_id, "limit": 100}  # ✅ Max limit
response = api_call("/leads/list", POST, data)
leads = response.get('items', [])  # ✅ Correct key!

# Pagination
next_cursor = response.get('next_starting_after')
while next_cursor:
    data = {"campaign_id": campaign_id, "limit": 100, "starting_after": next_cursor}
    response = api_call("/leads/list", POST, data)
    leads.extend(response.get('items', []))
    next_cursor = response.get('next_starting_after')
```

### 2. Response Parsing
**All endpoints return:** `{items: [...], next_starting_after: "..."}`
**NOT:** `{leads: [...]}` or `{data: [...]}`

---

## 📈 TOTAL DATA AVAILABLE

```
✅ Campaigns Configuration:     5 campaigns × RICH data
✅ Campaigns Analytics:          4 campaigns × metrics
✅ Leads:                        1,000-2,000 leads × DETAILED info
✅ Accounts:                     10 accounts
✅ Daily Analytics:              18+ days × metrics
✅ Steps Analytics:              8-12 steps × performance
✅ Global Overview:              1 summary

TOTAL RECORDS:                   ~1,500-2,500 records
RICHNESS:                        VERY HIGH (full payloads, history, templates)
```

---

## 🚀 NEXT STEPS

1. **Update collect_data.py:**
   - Fix limit to 100
   - Fix response parsing (`items` not `leads`)
   - Add pagination support
   - Test /emails with limit=100

2. **Database Schema:**
   - Add tables for campaign configuration
   - Add pagination tracking
   - Store `next_starting_after` for incremental sync

3. **Run Full Collection:**
   - Collect all leads (with pagination)
   - Collect all campaign configs
   - Test emails endpoint

---

**Created:** 2025-11-01
**Status:** Ready for implementation
**Estimated total data:** 1,500-2,500 detailed records
