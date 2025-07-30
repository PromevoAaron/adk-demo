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
cred_file = os.environ.get("SA_JSON_FILE") 

# try if the file exists
credentials_config = None
if os.path.exists(cred_file):
    try:
        # Load file from current directory.
        credentials, _ = google.auth.load_credentials_from_file(cred_file)
        credentials_config = BigQueryCredentialsConfig(credentials=credentials)
        print("SA credentilized from json file")
    except Exception as e:
        print(f"Error loading credentials from file: {e}")
else:
    print(f"WARNING: Service account file '{cred_file}' not found. BigQuery tools will use Application Default Credentials if available.")
    try:
        # If the file does not exist, use Application Default Credentials
        credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(credentials=credentials)
        print("SA credentialized from Application Default Credentials")
    except Exception as e:
        print(f"Error loading Application Default Credentials: {e}")

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

# Maybe  these should be lists
def get_top_subreddit_posts(search_term: str) -> dict:
    """
        Searches for posts related to the search term.

        Args:
            search_term: The term to search for.

        Returns:
            A dictionary where each article is posted The most important item is the subreddit.
        """
    print(f"Searching for subreddits with term: {search_term}")
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
        
        for submission in reddit.subreddit("all").search(search_term, sort="relevance", time_filter="month", limit=10):
            # if the submission is SFW, save it
            if submission.over_18 == False:
                subreddits[submission.id] = {
                    "subreddit": submission.subreddit.display_name,
                    "title": submission.title,
                    # "score": submission.score,
                    # "comments": submission.num_comments,
                }
        return subreddits

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def get_relevant_posts(subreddit: str) -> dict:
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
    description="This agent is designed to query the Reddit API using the custom functions listed in the tools list below.",
    tools=[get_relevant_posts, get_top_subreddit_posts],
    instruction="If a dictionary is returned, format it nicely (tabular if applicable). The user will need this information to do research on Reddit.",
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
        If the user ask for a part list, you may need to join vendors and vendor parts to provide relevant information.
        If the user wants to create/add/submit/enter an order, add the required data to the orders table.
        
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
        You are the Seattle ADK Demo agent!

        [Goal]
        Route traffic to the appropriate subagents.

        [Instructions]
        Follow the steps.
        1. Introduce yourself as the "Seattle ADK Demo Agent".
        2. Ask how you can help the user.
        3. If the user asks about reddit or subreddits, use the reddit_agent.
        4. If the user asks about sales, vendors, or any other data questions, use the bigquery_agent.  
        5. Otherwise, use your LLM training to attempt the question, but then quickly steer the agent back to the topic of the demo. 
        """
    ),
    output_key="root_response",
    sub_agents=[reddit_agent, bigquery_agent]
)