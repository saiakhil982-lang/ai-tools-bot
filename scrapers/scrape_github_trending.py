"""
GitHub Trending Scraper
Respectfully scrapes GitHub Trending page for AI/ML repositories.

This script:
- Fetches GitHub Trending page HTML
- Extracts repository names, URLs, and descriptions
- Filters for AI/ML related repos
- Saves to data/tools.csv
- Uses respectful rate limiting and error handling
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = DATA_DIR / "tools.csv"

def scrape_github_trending():
    """
    Scrape GitHub Trending for AI/ML repositories.
    
    Returns:
        list: List of tool dictionaries
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("⚠️ Required libraries not found. Install with: pip install requests beautifulsoup4")
        return []
    
    # AI/ML keywords to filter repositories
    ai_keywords = [
        "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
        "neural", "nlp", "llm", "gpt", "transformer", "pytorch", "tensorflow",
        "chatbot", "computer vision", "cv", "reinforcement learning"
    ]
    
    tools = []
    
    try:
        # GitHub Trending URL (no API key needed, but be respectful)
        url = "https://github.com/trending"
        
        print("🔍 Fetching GitHub Trending repositories...")
        
        # Add headers to appear more like a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ GitHub Trending returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find repository items (GitHub's HTML structure may change)
        # Look for articles with class containing "Box-row"
        repo_items = soup.find_all("article", class_=lambda x: x and "Box-row" in x)
        
        if not repo_items:
            # Alternative: try finding by h2 tags with repo links
            repo_items = soup.find_all("h2", class_=lambda x: x and "h3" in str(x))
        
        print(f"📦 Found {len(repo_items)} repository items")
        
        for item in repo_items[:25]:  # Limit to top 25
            try:
                # Extract repository name and URL
                link_elem = item.find("a", href=True)
                if not link_elem:
                    continue
                
                repo_path = link_elem["href"]
                repo_name = repo_path.strip("/")
                
                # Extract description
                desc_elem = item.find("p", class_=lambda x: x and "col-9" in str(x))
                if not desc_elem:
                    # Try alternative description location
                    desc_elem = item.find("p")
                
                description = desc_elem.get_text(strip=True) if desc_elem else "No description"
                
                # Check if it's AI/ML related
                name_lower = repo_name.lower()
                desc_lower = description.lower()
                
                is_ai = any(keyword in name_lower or keyword in desc_lower for keyword in ai_keywords)
                
                if is_ai:
                    repo_url = f"https://github.com{repo_path}"
                    
                    tool = {
                        "id": f"github-{repo_name.replace('/', '-')}",
                        "name": repo_name,
                        "description": description or "GitHub repository",
                        "url": repo_url,
                        "category": "devtools,github",
                        "primary_category": "devtools",
                        "source": "github-trending",
                        "launch_date": datetime.now().isoformat()
                    }
                    tools.append(tool)
            except Exception as e:
                # Skip items that can't be parsed
                continue
        
        print(f"✅ Found {len(tools)} AI/ML repositories from GitHub Trending")
        
        # Be respectful - add a small delay
        time.sleep(1)
        
        return tools
        
    except Exception as e:
        print(f"❌ Error scraping GitHub Trending: {str(e)}")
        print("   Note: GitHub's HTML structure may have changed. This scraper may need updates.")
        return []


if __name__ == "__main__":
    tools = scrape_github_trending()
    
    if tools:
        # Load existing tools
        existing_df = pd.DataFrame()
        if OUTPUT_CSV.exists():
            try:
                existing_df = pd.read_csv(OUTPUT_CSV)
                if not existing_df.empty and "primary_category" not in existing_df.columns:
                    existing_df["primary_category"] = (
                        existing_df["category"].astype(str).str.split(",").str[0].fillna("general")
                    )
            except:
                pass
        
        # Create new DataFrame
        new_df = pd.DataFrame(tools)
        if not new_df.empty and "primary_category" not in new_df.columns:
            new_df["primary_category"] = (
                new_df["category"].astype(str).str.split(",").str[0].fillna("general")
            )
        
        # Get existing URLs to avoid duplicates
        existing_urls = set(existing_df["url"].astype(str).tolist()) if not existing_df.empty else set()
        new_urls = set(new_df["url"].astype(str).tolist())
        
        # Filter out tools that already exist
        new_tools_df = new_df[~new_df["url"].astype(str).isin(existing_urls)]
        
        if not new_tools_df.empty:
            # Combine and save
            if not existing_df.empty:
                combined_df = pd.concat([existing_df, new_tools_df], ignore_index=True)
            else:
                combined_df = new_tools_df
            
            # Save (merge script will handle final deduplication and sorting)
            combined_df.to_csv(OUTPUT_CSV, index=False)
            print(f"💾 Added {len(new_tools_df)} new tools, total: {len(combined_df)}")
        else:
            print("ℹ️ All tools already exist in database")
    else:
        print("ℹ️ No new tools to save")

