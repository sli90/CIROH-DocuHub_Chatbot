# Firecrawl API Setup Guide

This guide will help you set up a Firecrawl API key for the CIROH Documentation Scraper.

## What is Firecrawl?

Firecrawl is a powerful web scraping API that handles:
- JavaScript rendering
- Automatic retries
- Rate limiting
- Content extraction
- Markdown conversion

## Getting Your API Key

### Step 1: Create an Account

1. Visit [https://www.firecrawl.dev](https://www.firecrawl.dev)
2. Click "Get Started" or "Sign Up"
3. Create an account using:
   - Email and password
   - Google account
   - GitHub account

### Step 2: Access Your Dashboard

1. Log in to your Firecrawl account
2. Navigate to the dashboard
3. Look for "API Keys" section

### Step 3: Generate API Key

1. Click "Create New API Key" or similar button
2. Give your key a name (e.g., "CIROH Docs Scraper")
3. Copy the generated API key
4. **Important**: Save this key securely - you won't be able to see it again!

### Step 4: Configure the Scraper

1. Open the `.env` file in your project directory
2. Replace `your_firecrawl_api_key_here` with your actual API key:
   ```
   FIRECRAWL_API_KEY=fc-your-actual-api-key-here
   ```
3. Save the file

## API Limits

### Free Tier
- 500 credits per month
- Each scrape uses 1 credit
- Perfect for this project (only ~40 pages)

### Paid Tiers
- Growth: $19/month for 10,000 credits
- Scale: $99/month for 100,000 credits
- Enterprise: Custom pricing

## Best Practices

1. **Keep Your API Key Secret**
   - Never commit `.env` to version control
   - Don't share your API key publicly
   - Use environment variables in production

2. **Monitor Usage**
   - Check your dashboard regularly
   - The scraper logs API responses
   - Failed requests don't consume credits

3. **Rate Limiting**
   - The scraper includes automatic delays
   - Respects Firecrawl's rate limits
   - Uses exponential backoff for retries

## Troubleshooting

### Invalid API Key Error
```
Error: Invalid API key
```
**Solution**: Double-check your API key in `.env` file

### Rate Limit Exceeded
```
Error: 429 - Too Many Requests
```
**Solution**: Wait a few minutes and retry, or increase delay in settings

### Out of Credits
```
Error: Insufficient credits
```
**Solution**: Check your dashboard and upgrade plan if needed

## Alternative: Using Without Firecrawl

If you can't use Firecrawl, the scraper includes a fallback method using BeautifulSoup. However, this may not work well with JavaScript-heavy pages.

To use fallback mode:
1. Set `ENABLE_FALLBACK_SCRAPING=true` in `.env`
2. Leave `FIRECRAWL_API_KEY` empty
3. Run the scraper normally

Note: Results may be less accurate without Firecrawl.

## Security Notes

- API keys are tied to your account
- You can revoke keys anytime from dashboard
- Use read-only keys when possible
- Monitor API usage for unusual activity

## Support

- Firecrawl Documentation: [https://docs.firecrawl.dev](https://docs.firecrawl.dev)
- Firecrawl Support: support@firecrawl.dev
- Project Issues: Open an issue on GitHub