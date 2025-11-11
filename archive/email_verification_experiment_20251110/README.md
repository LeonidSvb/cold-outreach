# Email Pattern Verification Experiment

**Date:** 2025-11-10
**Status:** Discontinued
**Success Rate:** 0% (0/10 test cases)

## Purpose

Attempt to find business emails for local businesses (HVAC, electricians, etc.) using:
1. Pattern generation (info@, contact@, service@, etc.)
2. SMTP verification (free, no API costs)

## Why It Failed

### Root Cause
Mail servers block SMTP RCPT TO verification attempts to prevent email fishing/harvesting.

### Specific Issues
1. **Anti-fishing protection**: Most mail servers return "550 User not found" even for valid emails
2. **Non-standard patterns**: Local businesses don't use info@/contact@ (use personal emails instead)
3. **Missing MX records**: 40% of tested businesses had no mail server configured
4. **Timeout/blocks**: Servers disconnect or timeout verification attempts

## Test Results

**Tested:** 10 electrician businesses from Florida
**Pattern tested:** 8-10 per business (info, contact, hello, sales, support, service, office, admin, emergency, schedule)
**Valid emails found:** 0
**Invalid responses:** 60%
**No MX records:** 40%

## Better Alternative

**Website Scraping Approach:**
- Scrape contact/about/team pages directly
- Extract existing emails from HTML (mailto: links, text)
- Expected success rate: 40-60%
- Cost: $0 (same as pattern guessing)

## Technology Used

- Python 3.12
- `smtplib` (built-in)
- `dns.resolver` (dnspython library)
- SMTP RCPT TO verification
- DNS MX record lookup

## Files

- `business_email_finder.py` - Main script (547 lines)
- `email_verification_test_20251110.csv` - Test results (10 businesses)

## Conclusion

SMTP verification technology works correctly, but pattern guessing approach is ineffective for cold email discovery. Direct website scraping is the recommended approach for finding business contact emails.
