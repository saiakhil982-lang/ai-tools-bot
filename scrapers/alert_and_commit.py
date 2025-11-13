"""
Alert and Commit Script
Sends email alerts for new tools and commits changes to git.

This script:
- Checks if there are new tools (passed via environment or file)
- Sends email via SMTP (Gmail) if new tools found
- Commits updated tools.csv to git repository
- Uses GitHub Actions secrets for email credentials
"""

import os
import sys
import json
import smtplib
import subprocess
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
TOOLS_CSV = DATA_DIR / "tools.csv"

def send_email_alert(new_tools):
    """
    Send email alert with new tools.
    
    Args:
        new_tools: List of tool dictionaries
    
    Returns:
        bool: True if email sent successfully
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_to = os.getenv("EMAIL_TO")
    
    if not all([smtp_user, smtp_pass, email_to]):
        print("ℹ️ Email credentials not configured. Skipping email alert.")
        print("   To enable: Set SMTP_USER, SMTP_PASS, and EMAIL_TO in GitHub Secrets")
        return False
    
    if not new_tools:
        print("ℹ️ No new tools to alert about.")
        return False
    
    try:
        # Create email
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email_to
        msg["Subject"] = f"🤖 New AI Tools Discovered ({len(new_tools)} new tool(s))"
        
        # Email body
        body = f"""
        <html>
        <body>
        <h2>New AI Tools Discovered!</h2>
        <p>We found {len(new_tools)} new AI tool(s) today:</p>
        <ul>
        """
        
        for tool in new_tools:
            name = tool.get("name", "Unknown Tool")
            url = tool.get("url", "#")
            category = tool.get("category", "general")
            description = tool.get("description", "No description")
            launch_date = tool.get("launch_date", "Unknown date")
            
            body += f"""
            <li>
                <strong><a href="{url}">{name}</a></strong><br>
                Category: {category}<br>
                Description: {description}<br>
                Launched: {launch_date}
            </li>
            """
        
        body += """
        </ul>
        <p>Check out your Streamlit app to see all tools!</p>
        <p><small>This is an automated email from your AI Tools Chatbot scraper.</small></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "html"))
        
        # Send email via Gmail SMTP
        print(f"📧 Sending email to {email_to}...")
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False


def commit_changes():
    """
    Commit updated tools.csv to git repository.
    
    Returns:
        bool: True if commit successful
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("ℹ️ Not in a git repository. Skipping commit.")
            return False
        
        # Check if there are changes
        result = subprocess.run(
            ["git", "status", "--porcelain", str(TOOLS_CSV)],
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            print("ℹ️ No changes to commit.")
            return False
        
        # Configure git (if in GitHub Actions)
        github_actor = os.getenv("GITHUB_ACTOR")
        if github_actor:
            subprocess.run(
                ["git", "config", "user.name", github_actor],
                check=False
            )
            subprocess.run(
                ["git", "config", "user.email", f"{github_actor}@users.noreply.github.com"],
                check=False
            )
        
        # Add and commit
        subprocess.run(["git", "add", str(TOOLS_CSV)], check=True)
        
        commit_message = f"🤖 Update AI tools database - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push (if in GitHub Actions, GITHUB_TOKEN will be used)
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            # Set up remote URL with token
            repo = os.getenv("GITHUB_REPOSITORY")
            if repo:
                remote_url = f"https://{github_token}@github.com/{repo}.git"
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=False)
        
        subprocess.run(["git", "push"], check=True)
        
        print("✅ Changes committed and pushed to repository!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git operation failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error committing changes: {str(e)}")
        return False


def main():
    """
    Main function: Check for new tools, send email, commit changes.
    """
    
    # Try to load new tools from JSON file (created by merge_and_write.py)
    NEW_TOOLS_FILE = DATA_DIR / "new_tools.json"
    new_tools = []
    
    if NEW_TOOLS_FILE.exists():
        try:
            with open(NEW_TOOLS_FILE, "r") as f:
                new_tools = json.load(f)
            print(f"📧 Found {len(new_tools)} new tools to alert about")
        except Exception as e:
            print(f"⚠️ Error reading new_tools.json: {str(e)}")
    
    # Fallback: Try to detect new tools by comparing to git
    if pd is not None and not new_tools and TOOLS_CSV.exists():
        try:
            # Get current tools
            current_df = pd.read_csv(TOOLS_CSV)
            
            # Try to get previous version from git
            result = subprocess.run(
                ["git", "show", "HEAD:data/tools.csv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                previous_df = pd.read_csv(StringIO(result.stdout))
                previous_urls = set(previous_df["url"].astype(str).tolist())
                current_urls = set(current_df["url"].astype(str).tolist())
                new_urls = current_urls - previous_urls
                
                if new_urls:
                    new_tools_df = current_df[current_df["url"].astype(str).isin(new_urls)]
                    new_tools = new_tools_df.to_dict("records")
                    print(f"📧 Detected {len(new_tools)} new tools via git comparison")
        except Exception:
            # Git comparison failed, skip
            pass
    elif pd is None:
        print("ℹ️ Pandas not installed. Skipping git comparison for new tools.")
    
    # Send email if new tools found
    if new_tools:
        send_email_alert(new_tools)
        # Clean up JSON file after sending
        if NEW_TOOLS_FILE.exists():
            try:
                NEW_TOOLS_FILE.unlink()
            except:
                pass
    else:
        print("ℹ️ No new tools to alert about.")
    
    # Commit changes
    commit_changes()


if __name__ == "__main__":
    main()

