# Google Places API - Setup Instructions

## How to Get Your API Key

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a Project"** → **"New Project"**
3. Enter project name (e.g., "Lead Generation")
4. Click **"Create"**

### Step 2: Enable Google Places API

1. In the search bar, type: **"Places API"**
2. Click on **"Places API (New)"**
3. Click **"Enable"**
4. Also enable **"Geocoding API"** (search and enable it too)

### Step 3: Create API Key

1. Go to **"Credentials"** (left sidebar)
2. Click **"+ Create Credentials"** → **"API Key"**
3. Your API key will be generated: `AIzaSyC...` (copy it!)

### Step 4: Restrict API Key (Important for Security)

1. Click on your newly created API key
2. Under **"API restrictions"**:
   - Select **"Restrict key"**
   - Check:
     - ✅ Places API (New)
     - ✅ Geocoding API
3. Under **"Application restrictions"** (optional):
   - Select **"HTTP referrers"**
   - Add your domain (e.g., `*.streamlit.app/*`)
4. Click **"Save"**

### Step 5: Enable Billing (Required)

**Google Places API requires billing enabled, but you get:**
- **$200 free credit per month**
- You won't be charged until you exceed this

**To enable billing:**
1. Go to **"Billing"** (left sidebar)
2. Click **"Link a billing account"**
3. Follow the steps to add a payment method
4. You'll get $200 monthly credit automatically

### Step 6: Test Your API Key

Paste your API key in the Streamlit app and try a small test query!

---

## Pricing Information

### Free Tier
- **$200 credit per month** = ~6,000 Place Details requests
- Automatically applied to all Google Cloud APIs

### Costs per Request
- **Nearby Search**: $0.032 per request
- **Place Details**: $0.017 per request
- **Geocoding**: $0.005 per request

### Example Cost Calculation

**Scenario:** Scrape 20 cities, 30 results per city

- Geocoding: 20 cities × $0.005 = **$0.10**
- Nearby Search: 20 cities × $0.032 = **$0.64**
- Place Details: 600 places × $0.017 = **$10.20**
- **Total: ~$11** (well within $200 free tier!)

---

## Security Best Practices

### DO:
- ✅ Restrict API key to only needed APIs (Places + Geocoding)
- ✅ Add HTTP referrer restrictions
- ✅ Set up billing alerts (e.g., notify at $50)
- ✅ Monitor usage in Google Cloud Console
- ✅ Keep API key private (never commit to GitHub)

### DON'T:
- ❌ Share your API key publicly
- ❌ Use same key for multiple projects
- ❌ Leave unrestricted API key
- ❌ Commit API key to version control

---

## Troubleshooting

### "This API project is not authorized to use this API"
**Solution:** Enable "Places API (New)" in your project

### "You must enable Billing on the Google Cloud Project"
**Solution:** Follow Step 5 above to enable billing

### "API key not valid"
**Solution:**
- Check if you copied full key (starts with `AIzaSy...`)
- Verify API restrictions don't block your request
- Wait 5 minutes after creating key (propagation time)

### "QUOTA_EXCEEDED"
**Solution:**
- Check usage in Google Cloud Console
- You've exceeded $200 free tier
- Either wait for next month or add more budget

---

## Where to Enter API Key

### Personal Mode (Local Use)
Create `.env` file in project root:
```
GOOGLE_MAPS_API_KEY=AIzaSyC...your-key-here
```

### Shared Mode (Public App)
Enter API key directly in the Streamlit UI when prompted.
Your key is stored only in your browser session and never saved to disk.

---

## Additional Resources

- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service/overview)
- [Pricing Calculator](https://mapsplatform.google.com/pricing/)
- [API Key Best Practices](https://developers.google.com/maps/api-security-best-practices)

---

## Need Help?

If you encounter issues:
1. Check [Google Cloud Console](https://console.cloud.google.com/) for error messages
2. Verify billing is enabled
3. Check API usage/quotas
4. Review API key restrictions
