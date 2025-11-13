"""
AI Tools Chatbot - Streamlit Application
A beginner-friendly chatbot that shows latest AI tools and provides category-specific recommendations.

This app:
- Fetches AI tools from Product Hunt API (if available) or CSV fallback
- Provides category-specific recommendations (finance, customer support, content, etc.)
- Uses free Hugging Face models for summarization (with template fallback)
- Displays tools with clickable URLs and launch dates
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# Try to import transformers for AI summarization (optional)
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False

HF_MODEL_NAME = "distilgpt2"

# Configure page
st.set_page_config(
    page_title="AI Tools Chatbot",
    page_icon="🤖",
    layout="wide"
)

if not TRANSFORMERS_AVAILABLE:
    st.info(
        "Using the built-in summary template. Install the optional transformers package to enable AI-written summaries."
    )

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Path to data files
DATA_DIR = Path("data")
SAMPLE_CSV = DATA_DIR / "sample_ai_tools.csv"
TOOLS_CSV = DATA_DIR / "tools.csv"

def get_ai_tools(category=None, q=None):
    """
    Fetch AI tools from Product Hunt API or CSV fallback.
    
    Args:
        category: Filter by category (e.g., 'finance', 'customer-support', 'content')
        q: Search query string
    
    Returns:
        pandas.DataFrame: DataFrame with columns: id, name, description, url, category, source, launch_date
    """
    # Try Product Hunt API first (if API key is available)
    producthunt_api_key = os.getenv("PRODUCTHUNT_API_KEY")
    
    if producthunt_api_key:
        try:
            # Product Hunt GraphQL endpoint
            import requests
            
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
                "Authorization": f"Bearer {producthunt_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.producthunt.com/v2/api/graphql",
                json={"query": query},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tools = []
                
                for edge in data.get("data", {}).get("posts", {}).get("edges", []):
                    node = edge["node"]
                    categories = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
                    category_str = categories[0] if categories else "general"
                    
                    tools.append({
                        "id": node.get("id", ""),
                        "name": node.get("name", ""),
                        "description": node.get("tagline", ""),
                        "url": node.get("website") or node.get("url", ""),
                        "category": category_str.lower().replace(" ", "-"),
                        "source": "producthunt",
                        "launch_date": node.get("createdAt", "")
                    })
                
                df = pd.DataFrame(tools)
                
                # Apply filters
                if category:
                    df = df[df["category"].str.contains(category, case=False, na=False)]
                if q:
                    df = df[
                        df["name"].str.contains(q, case=False, na=False) |
                        df["description"].str.contains(q, case=False, na=False)
                    ]
                
                if not df.empty:
                    return df
        except Exception as e:
            st.warning(f"⚠️ Product Hunt API error: {str(e)}. Falling back to CSV.")
    
    # Fallback to CSV files
    csv_path = TOOLS_CSV if TOOLS_CSV.exists() else SAMPLE_CSV
    
    if not csv_path.exists():
        st.error(f"❌ Data file not found: {csv_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path)
        
        # Ensure required columns exist
        required_cols = ["name", "description", "url", "category", "source", "launch_date"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        
        # Apply filters
        if category:
            df = df[df["category"].str.contains(category, case=False, na=False)]
        if q:
            df = df[
                df["name"].str.contains(q, case=False, na=False) |
                df["description"].str.contains(q, case=False, na=False)
            ]
        
        return df
    except Exception as e:
        st.error(f"❌ Error reading CSV: {str(e)}")
        return pd.DataFrame()


def summarize_tools(tools_list, user_question):
    """
    Generate a summary and recommendation for the tools list.
    
    Uses Hugging Face transformers if available, otherwise falls back to template.
    
    Args:
        tools_list: List of tool dictionaries or DataFrame
        user_question: User's question/query
    
    Returns:
        str: Summary text
    """
    if isinstance(tools_list, pd.DataFrame):
        tools_list = tools_list.to_dict("records")
    
    if not tools_list:
        return "No tools found matching your criteria."
    
    # Try using transformers if available
    if TRANSFORMERS_AVAILABLE:
        try:
            generator = st.session_state.get("hf_generator")
            if generator is None:
                generator = pipeline(
                    "text-generation",
                    model=HF_MODEL_NAME,
                    max_new_tokens=80,
                    do_sample=False,
                    pad_token_id=50256,
                )
                st.session_state["hf_generator"] = generator

            prompt_text = (
                "Summarize the following AI tools in two short sentences and recommend the best fit for the user's request.\n"
                f"User request: {user_question or 'General discovery'}\n"
                "Tools:\n"
            )
            for tool in tools_list[:5]:
                prompt_text += (
                    f"- Name: {tool.get('name', 'Unknown')}; "
                    f"Category: {tool.get('category', 'general')}; "
                    f"Description: {tool.get('description', 'No description')}\n"
                )
            prompt_text += "Summary:"

            generated = generator(
                prompt_text,
                max_new_tokens=80,
                num_return_sequences=1,
                do_sample=False,
            )
            generated_text = generated[0]["generated_text"]
            completion = generated_text[len(prompt_text):].strip()

            # Clean up the generated text to keep it concise
            if completion:
                first_paragraph = completion.split("\n")[0].strip()
                if len(first_paragraph) > 0:
                    return first_paragraph
        except Exception:
            # Fall back to template if transformers fails
            pass
    
    # Template-based fallback (always works)
    num_tools = len(tools_list)
    categories = set(tool.get("category", "general") for tool in tools_list)
    category_str = ", ".join(list(categories)[:3])
    
    top_tools = tools_list[:3]
    tool_names = ", ".join([tool.get("name", "Unknown") for tool in top_tools])
    
    summary = f"""
    Found {num_tools} AI tool(s) matching your query.
    
    Categories: {category_str if category_str else 'general'}
    
    Top recommendations:
    {tool_names}
    
    These tools can help with: {user_question.lower() if user_question else 'various tasks'}
    """
    
    return summary.strip()


def render_tools_list(df):
    """
    Display tools in a nice format with clickable URLs.
    
    Args:
        df: pandas.DataFrame with tool data
    """
    if df.empty:
        st.info("No tools found. Try a different category or search term.")
        return
    
    st.subheader(f"📊 Found {len(df)} tool(s)")
    
    # Display tools in columns
    for idx, row in df.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {row.get('name', 'Unknown Tool')}")
                st.markdown(f"**Description:** {row.get('description', 'No description available')}")
                
                # Category badge
                category = row.get('category', 'general')
                st.markdown(f"**Category:** `{category}`")
                
                # Launch date
                launch_date = row.get('launch_date', '')
                if launch_date:
                    try:
                        # Try to format date
                        if isinstance(launch_date, str):
                            date_obj = pd.to_datetime(launch_date, errors='coerce')
                            if pd.notna(date_obj):
                                formatted_date = date_obj.strftime("%Y-%m-%d")
                                st.markdown(f"**Launched:** {formatted_date}")
                    except:
                        st.markdown(f"**Launched:** {launch_date}")
            
            with col2:
                url = row.get('url', '')
                if url:
                    st.markdown(f"[🔗 Visit Tool]({url})")
                else:
                    st.markdown("🔗 No URL available")
                
                source = row.get('source', 'unknown')
                st.markdown(f"**Source:** `{source}`")
            
            st.divider()


# Main UI
st.title("🤖 AI Tools Chatbot")
st.markdown("""
Welcome! I can help you discover the latest AI tools and provide category-specific recommendations.
Ask me about tools for **finance**, **customer support**, **content creation**, **development**, or any other category!
""")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Category filter
    categories = ["all", "finance", "customer-support", "content", "devtools", "marketing", "productivity"]
    selected_category = st.selectbox("Filter by Category", categories)
    category_filter = None if selected_category == "all" else selected_category
    
    # Enable alerts section
    st.divider()
    st.subheader("📧 Email Alerts")
    st.markdown("""
    Get notified when new AI tools are discovered!
    
    To enable email alerts:
    1. Go to your GitHub repository
    2. Navigate to Settings → Secrets and variables → Actions
    3. Add these secrets:
       - `SMTP_USER`: Your Gmail address
       - `SMTP_PASS`: Your Gmail App Password
       - `EMAIL_TO`: Email address to receive alerts
    4. The daily scraper will automatically send you emails!
    
    See README.md for detailed instructions.
    """)
    
    if st.button("📖 View Setup Instructions"):
        st.info("Check the README.md file in the repository for complete setup instructions.")

# Chat interface
st.header("💬 Chat")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about AI tools (e.g., 'Show me finance tools' or 'What tools help with content creation?')"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Searching for AI tools..."):
            # Extract category from prompt (simple keyword matching)
            detected_category = None
            category_keywords = {
                "finance": ["finance", "financial", "money", "banking", "investment"],
                "customer-support": ["support", "customer", "service", "helpdesk", "chatbot"],
                "content": ["content", "writing", "blog", "article", "copy"],
                "devtools": ["development", "code", "programming", "developer", "api"],
                "marketing": ["marketing", "social", "advertising", "campaign"],
                "productivity": ["productivity", "task", "project", "management", "workflow"]
            }
            
            prompt_lower = prompt.lower()
            for cat, keywords in category_keywords.items():
                if any(keyword in prompt_lower for keyword in keywords):
                    detected_category = cat
                    break
            
            # Use detected category or sidebar filter
            search_category = detected_category or category_filter
            
            # Search for tools
            tools_df = get_ai_tools(category=search_category, q=prompt)
            
            if not tools_df.empty:
                # Generate summary
                summary = summarize_tools(tools_df, prompt)
                st.markdown(summary)
                
                st.markdown("---")
                
                # Display tools
                render_tools_list(tools_df)
            else:
                st.markdown("I couldn't find any tools matching your query. Try asking about a specific category like 'finance tools' or 'content creation tools'.")
    
    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Found {len(tools_df)} tool(s) matching your query." if not tools_df.empty else "No tools found."
    })

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🤖 AI Tools Chatbot | Data refreshes daily via GitHub Actions</p>
    <p>Built with Streamlit | Uses free APIs and open-source models</p>
</div>
""", unsafe_allow_html=True)

