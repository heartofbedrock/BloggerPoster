import openai
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apscheduler.schedulers.blocking import BlockingScheduler
import time

# Set up your API keys
OPENAI_API_KEY = 'your_openai_api_key'
BLOGGER_API_KEY = 'your_blogger_api_key'
BLOGGER_BLOG_ID = 'your_blogger_blog_id'

# OpenAI configuration
openai.api_key = OPENAI_API_KEY

def get_news_articles():
    gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        'query': 'technology',  # Specify the keyword you want to fetch articles for
        'mode': 'artlist',  # Article list mode
        'maxrecords': 10,  # Number of articles to fetch
        'format': 'json',  # Ensure the response is in JSON format
        'filter': 'lang:english'  # Filter articles to only English language
    }

    response = requests.get(gdelt_url, params=params)

    if response.status_code == 200:
        return response.json().get('articles', [])
    else:
        print(f"Error fetching articles: {response.status_code}")
        return []

def generate_blog_content(article_title, article_description, article_content):
    prompt = f"Create a blog post about technology. Use the following title and summary:\n\nTitle: {article_title}\n\nSummary: {article_description}\n\nContent: {article_content}\n\nExpand the content with additional insights about the topic."

    response = openai.Completion.create(
        model="gpt-4", 
        prompt=prompt, 
        max_tokens=1000
    )
    return response['choices'][0]['text']

def post_to_blogger(blog_content, title):
    try:
        service = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)
        post_body = {
            'title': title,
            'content': blog_content
        }
        post = service.posts().insert(blogId=BLOGGER_BLOG_ID, body=post_body).execute()
        print(f"Posted to Blogger: {post['url']}")
    except HttpError as e:
        print(f"An error occurred: {e}")

def fetch_and_publish():
    print("Fetching and publishing a new blog post...")
    articles = get_news_articles()

    if not articles:
        print("No articles found.")
        return

    article = articles[0]  # Get the latest article
    title = article.get('title')
    description = article.get('seendescription', article.get('summary', ''))  # Use seendescription or summary as a fallback
    content = article.get('body', '')  # Use body of the article

    if not title or not description or not content:
        print("Missing information in the article, skipping...")
        return

    # Use ChatGPT to generate the blog content
    blog_content = generate_blog_content(title, description, content)

    # Post the generated content to Blogger
    post_to_blogger(blog_content, title)

# Scheduler setup to run every hour
scheduler = BlockingScheduler()

# Schedule the task to run every hour
scheduler.add_job(fetch_and_publish, 'interval', hours=1)

if __name__ == "__main__":
    try:
        print("Starting the scheduler to post every hour.")
        fetch_and_publish()  # Run the task immediately at start
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
