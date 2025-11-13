"""
Product Hunt Scraper
Fetches AI tools from Product Hunt API and saves to CSV.

This script:
- Uses Product Hunt GraphQL API if PRODUCTHUNT_API_KEY is available
- Extracts AI/ML related products
- Saves to data/tools.csv (or creates it if it doesn't exist)
- Exits cleanly if API key is not available (won't fail GitHub Actions)
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = DATA_DIR / "tools.csv"

def scrape_producthunt():
    """
    Scrape Product Hunt for AI tools.
    
    Returns:
        list: List of tool dictionaries
    """
    api_key = os.getenv("PRODUCTHUNT_API_KEY")
    
    if not api_key:
        print("ℹ️ PRODUCTHUNT_API_KEY not found. Skipping Product Hunt scraping.")
        print("   To enable: Add PRODUCTHUNT_API_KEY to GitHub Secrets or .env file")
        return []
    
    try:
        import requests
        
        # Product Hunt GraphQL query
        # Note: Product Hunt API requires authentication and has rate limits
        query = """
        query {
            posts(first: 50, order: VOTES) {
                edges {
                    node {
                        id
                        name
                        tagline
                        url
                        website
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                        createdAt
                    }
                }
            }
        }
        """
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print("🔍 Fetching tools from Product Hunt API...")
        response = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            json={"query": query},
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"⚠️ Product Hunt API error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return []
        
        data = response.json()
        
        # Check for errors in GraphQL response
        if "errors" in data:
            print(f"⚠️ GraphQL errors: {data['errors']}")
            return []
        
        tools = []
        ai_keywords = ["ai", "artificial intelligence", "machine learning", "ml", "nlp", "neural", "deep learning"]
        
        for edge in data.get("data", {}).get("posts", {}).get("edges", []):
            node = edge["node"]
            
            # Filter for AI/ML related tools
            name = node.get("name", "").lower()
            tagline = node.get("tagline", "").lower()
            topics = [t["node"]["name"].lower() for t in node.get("topics", {}).get("edges", [])]
            
            # Check if it's AI-related
            is_ai = any(keyword in name or keyword in tagline for keyword in ai_keywords)
            is_ai = is_ai or any(keyword in " ".join(topics) for keyword in ai_keywords)
            
            if is_ai:
                categories = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
                category = categories[0].lower().replace(" ", "-") if categories else "general"
                
                # Map common categories
                category_mapping = {
                    "fintech": "finance",
                    "developer-tools": "devtools",
                    "customer-support": "customer-support",
                    "content-marketing": "content",
                    "marketing": "marketing"
                }
                category = category_mapping.get(category, category)
                
                tool = {
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                    "description": node.get("tagline", ""),
                    "url": node.get("website") or node.get("url", ""),
                    "category": category,
                    "source": "producthunt",
                    "launch_date": node.get("createdAt", datetime.now().isoformat())
                }
                tools.append(tool)
        
        print(f"✅ Found {len(tools)} AI tools from Product Hunt")
        return tools
        
    except ImportError:
        print("⚠️ 'requests' library not found. Install with: pip install requests")
        return []
    except Exception as e:
        print(f"❌ Error scraping Product Hunt: {str(e)}")
        return []


if __name__ == "__main__":
    tools = scrape_producthunt()
    
    if tools:
        # Load existing tools
        existing_df = pd.DataFrame()
        if OUTPUT_CSV.exists():
            try:
                existing_df = pd.read_csv(OUTPUT_CSV)
            except:
                pass
        
        # Create new DataFrame
        new_df = pd.DataFrame(tools)
        
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

