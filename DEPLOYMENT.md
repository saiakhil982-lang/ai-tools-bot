# 🚀 Deployment Guide

This guide will help you deploy the AI Tools Chatbot to Streamlit Community Cloud.

## Step-by-Step Deployment

### 1. Fork the Repository

1. Go to the GitHub repository
2. Click the **Fork** button in the top right
3. This creates a copy in your GitHub account

### 2. Deploy to Streamlit Community Cloud

1. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your forked repository
5. Set the main file path to: `streamlit_app.py`
6. Click **"Deploy"**

The app will be live in a few minutes! 🎉

### 3. Set Up GitHub Actions (Optional but Recommended)

To enable daily scraping and email alerts:

1. **Go to your repository on GitHub**
2. **Navigate to Settings → Secrets and variables → Actions**
3. **Add the following secrets:**

   #### Required for Email Alerts:
   - `SMTP_USER`: Your Gmail address
   - `SMTP_PASS`: Your Gmail App Password (see README.md for how to create)
   - `EMAIL_TO`: Email address to receive alerts

   #### Optional:
   - `PRODUCTHUNT_API_KEY`: Product Hunt API key (if you want Product Hunt scraping)

4. **Test the workflow:**
   - Go to **Actions** tab
   - Click **"Daily AI Tools Scraper"**
   - Click **"Run workflow"** to test manually

### 4. Verify Everything Works

1. **Check the Streamlit app:**
   - Visit your deployed app URL
   - Try asking: "Show me finance AI tools"
   - Verify tools are displayed

2. **Check GitHub Actions:**
   - Go to Actions tab
   - Verify the workflow runs successfully
   - Check logs for any errors

3. **Test email alerts:**
   - Manually trigger the workflow
   - Check your email for the alert

## Troubleshooting

### App won't load
- Check that `data/sample_ai_tools.csv` exists in the repository
- Verify all dependencies are in `requirements.txt`
- Check Streamlit Cloud logs for errors

### Email not sending
- Verify Gmail App Password is correct (16 characters, no spaces)
- Check that 2-Step Verification is enabled on your Google account
- Review GitHub Actions logs for SMTP errors

### Scraper not finding tools
- Product Hunt API key may be invalid (check API dashboard)
- GitHub Trending HTML may have changed (check scraper logs)
- Verify network connectivity in Actions logs

## Next Steps

- Customize categories in `streamlit_app.py`
- Add more scrapers in the `scrapers/` directory
- Adjust scraping schedule in `.github/workflows/daily_scrape.yml`
- Add more features to the chatbot!

## Support

If you encounter issues:
1. Check the README.md for detailed instructions
2. Review GitHub Actions logs
3. Check Streamlit Cloud logs
4. Open an issue on GitHub

Happy deploying! 🚀

