"""
Merge and Write Utility
Merges scraped tools, deduplicates by URL, sorts by launch_date, and writes to CSV.

This script:
- Reads existing data/tools.csv
- Merges with new tools from scrapers
- Deduplicates by URL (keeps most recent)
- Sorts by launch_date (newest first)
- Writes back to data/tools.csv
- Returns list of newly added tools for email alerts
"""

import sys
import json
import subprocess
from io import StringIO
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TOOLS_CSV = DATA_DIR / "tools.csv"
SAMPLE_CSV = DATA_DIR / "sample_ai_tools.csv"

def merge_and_write():
    """
    Merge scraped tools, deduplicate, sort, and write to CSV.
    
    This function reads tools.csv (which may have been updated by scrapers),
    compares it to the previous state, and returns new tools.
    
    Returns:
        list: List of newly added tool dictionaries
    """
    # Load existing tools (before scrapers ran)
    existing_df = pd.DataFrame()
    existing_urls = set()
    
    # Try to load previous state from a backup or check git diff
    # For simplicity, we'll compare current tools.csv to what was there before
    # In practice, scrapers append to tools.csv, so we need to track the baseline
    
    # Load current tools.csv (after scrapers have run)
    if TOOLS_CSV.exists():
        try:
            current_df = pd.read_csv(TOOLS_CSV)
            print(f"📂 Loaded {len(current_df)} tools from {TOOLS_CSV}")
        except Exception as e:
            print(f"⚠️ Error reading tools.csv: {str(e)}")
            current_df = pd.DataFrame()
    else:
        current_df = pd.DataFrame()
    
    # If tools.csv is empty or doesn't exist, initialize from sample
    if current_df.empty and SAMPLE_CSV.exists():
        try:
            current_df = pd.read_csv(SAMPLE_CSV)
            print(f"📂 Initialized from sample CSV: {len(current_df)} tools")
        except Exception as e:
            print(f"⚠️ Error reading sample CSV: {str(e)}")
    
    # For detecting new tools, we'll use a simple approach:
    # Save a hash/set of URLs to a temp file, or use git to track changes
    # For now, we'll write new tools to a temp file that alert script can read
    NEW_TOOLS_FILE = DATA_DIR / "new_tools.json"
    
    # Try to get baseline from git (if available)
    try:
        # Get tools.csv from previous commit
        result = subprocess.run(
            ["git", "show", "HEAD:data/tools.csv"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            existing_df = pd.read_csv(StringIO(result.stdout))
            existing_urls = set(existing_df["url"].astype(str).tolist())
            print(f"📂 Found {len(existing_df)} tools in previous commit")
    except:
        # No previous commit or not in git - assume all current tools are "existing"
        existing_urls = set(current_df["url"].astype(str).tolist()) if not current_df.empty else set()
    
    # Find new tools (by URL)
    if not current_df.empty:
        current_urls = set(current_df["url"].astype(str).tolist())
        new_urls = current_urls - existing_urls
        
        if new_urls:
            new_tools_df = current_df[current_df["url"].astype(str).isin(new_urls)]
            new_tools_list = new_tools_df.to_dict("records")
            print(f"✨ Found {len(new_tools_list)} new tools")
            
            # Save new tools to JSON file for alert script
            try:
                with open(NEW_TOOLS_FILE, "w") as f:
                    json.dump(new_tools_list, f, indent=2)
            except:
                pass
        else:
            new_tools_list = []
            print("ℹ️ No new tools found")
            # Clear new tools file
            if NEW_TOOLS_FILE.exists():
                NEW_TOOLS_FILE.unlink()
    else:
        new_tools_list = []
    
    # Deduplicate by URL (keep most recent)
    if not current_df.empty:
        current_df = current_df.drop_duplicates(subset=["url"], keep="last")
        
        # Sort by launch_date (newest first)
        if "launch_date" in current_df.columns:
            current_df["launch_date"] = pd.to_datetime(current_df["launch_date"], errors="coerce")
            current_df = current_df.sort_values("launch_date", ascending=False, na_position="last")
            # Convert back to string for CSV
            current_df["launch_date"] = current_df["launch_date"].dt.strftime("%Y-%m-%d")
        
        # Ensure all required columns exist
        required_cols = ["id", "name", "description", "url", "category", "primary_category", "source", "launch_date"]
        for col in required_cols:
            if col not in current_df.columns:
                current_df[col] = ""
        
        # Write to CSV
        current_df.to_csv(TOOLS_CSV, index=False)
        print(f"💾 Saved {len(current_df)} tools to {TOOLS_CSV}")
    
    return new_tools_list


if __name__ == "__main__":
    new_tools = merge_and_write()
    if new_tools:
        print(f"\n📧 {len(new_tools)} new tool(s) will be included in email alert:")
        for tool in new_tools[:5]:  # Show first 5
            print(f"   - {tool.get('name', 'Unknown')}: {tool.get('url', 'No URL')}")

