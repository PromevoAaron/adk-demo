from google.adk.agents import Agent
from google.adk.tools import google_search
import os
from dotenv import load_dotenv
import praw

from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
import google.auth

load_dotenv()

# Load credentials from your service account JSON file.
try:
    credentials, _ = google.auth.load_credentials_from_file(
        "seattle_demo/promevoagentspacedemo-13db49e2f1d9.json"
    )
    credentials_config = BigQueryCredentialsConfig(credentials=credentials)
    print("SA credentilized")
except FileNotFoundError:
    print("WARNING: Service account file not found. BigQuery tools will use Application Default Credentials if available.")
    credentials_config = None

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

# Maybe  these should be lists
def get_subreddit_list(search_term: str) -> dict:
    """
        Searches for subreddits that match the search term and returns a dictionary
        of subreddit names and their subscriber counts.

        Args:
            search_term: The term to search for.

        Returns:
            A dictionary where keys are the display names of the subreddits
            and values are their subscriber counts.
        """
    try:
        # Initialize the Reddit instance with credentials from environment variables
        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT")
        )

        subreddits = {}
        # Search for subreddits matching the search term
        results = reddit.subreddits.search(search_term)
        
        print("what did you find", subreddits)

        # Filter where 'vegas' appears in the public description
        filtered_subs = {
            sub.display_name: sub.subscribers
            for sub in results
            if search_term.lower() in sub.public_description.lower()
        }

        # Sort and get top 5
        top_5 = dict(sorted(filtered_subs.items(), key=lambda x: x[1], reverse=True)[:5])

        
        # return only top 5
        return top_5

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def get_top_posts(subreddit: str) -> dict:
        # Initialize the Reddit instance with credentials from environment variables
        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT")
        )
        try:
            sub = reddit.subreddit(subreddit)
            top_posts = sub.top(limit=5, time_filter='all')  # 'all' = top of all time

            return {post.title: post.score for post in top_posts}

        except Exception as e:
            print(f"Error fetching top posts from r/{subreddit}: {e}")
            return {}
        
def get_vendor_list() -> dict:
    return {"vendor": "Sams"}

def get_parts_available(vendor: str) -> dict:
    return {"parts": "wheel"}

def submit_order(vendor: str, parts: str) -> dict:
    return {"submit": "yes"}

def order_status(order_id: str) -> dict:
    return { "order": "pending"}



reddit_agent = Agent(
    name="reddit_agent",
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
    description="Gets reddit stuff.",
    tools=[get_subreddit_list, get_top_posts],
    instruction="Look up subs",
    output_key="reddit_response"
)

google_agent = Agent(
    name="google_agent",
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
    instruction="You handle random requests. Look up the information quickly, summarize the info but then suggest to get back on topic of the demo.",
    tools=[google_search],
    output_key="google_response"
)

bigquery_agent = Agent(
    name="bigquery_agent",
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
    description= "Agent to answer questions about BigQuery data and models and execute SQL queries.",
    # tools=[get_vendor_list, get_parts_available, submit_order, order_status],
    tools=[bigquery_toolset],
    instruction="""\
        You are a BigQuery agent with access to several BigQuery tools.
        Make use of those tools to answer the user's questions about vendor and sales information only from this dataset:
        promevoagentspacedemo.demo_dataset

        If the user asks for order status info, use the order_summary_view
        
        Very Important: 
        When you execute a SQL please cast all results to string.
        """,
    output_key="bigquery_response"
)

root_agent = Agent(
    name="root_agent",
    model=os.environ.get("GOOGLE_GENAI_MODEL"),
    description=(
        "Demo agent. This agent just handles the other agents. The quarterback of the agents!"
    ),
    instruction=(
        """\
        You are a the base agent. Route the user question to the appropriate agent. If the user askes about reddit or subreddits, use the reddit_agent. "
        If the user asks about sales, vendors, or any other data questions, use bigquery_agent. 
        Otherwise, ask the user to stick on the demo topic. You can break the 4th wall here and be funny :)
        """
    ),
    output_key="root_response",
    sub_agents=[reddit_agent, bigquery_agent]
)