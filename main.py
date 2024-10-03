import openai
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apscheduler.schedulers.blocking import BlockingScheduler
import time

# Set up your API keys
OPENAI_API_KEY = 'your_openai_api_key'
GOOGLE_NEWS_API_KEY = 'your_google_news_api_key'
BLOGGER_API_KEY = 'your_blogger_api_key'
BLOGGER_BLOG_ID = 'your_blogger_blog_id'

# OpenAI configuration
openai.api_key = OPENAI_API_KEY

# GDELT API configuration
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = "technology"
MAX_ARTICLES = 150

def get_news_articles():
    params = {
        'query': DEFAULT_QUERY,
        'mode': 'artlist',
        'maxrecords': MAX_ARTICLES,
        'format': 'json'
    }
    response = requests.get(GDELT_URL, params=params)

    # Check if the response is valid and contains articles
    if response.status_code != 200:
        print(f"Error fetching articles, Status Code: {response.status_code}")
        return []

    articles = response.json().get('articles', [])
    return articles

def generate_blog_content(article_title, article_description, article_content):
    messages = [
        {
            "role": "system", 
            "content": "You are a helpful assistant who writes engaging blog posts about technology."
        },
        {
            "role": "user", 
            "content": f"Create a blog post about technology. Use the following title and summary:\n\nTitle: {article_title}\n\nSummary: {article_description}\n\nContent: {article_content}\n\nExpand the content with additional insights about the topic."
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=messages,
        max_tokens=1000
    )

    return response['choices'][0]['message']['content']

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

    for article in articles:
        title = article.get('title')
        description = article.get('seendate')  # Fallback to seen date if no description
        content = article.get('socialimage')   # Fallback to social image if no content
        language = article.get('language')

        if language != 'English':
            print(f"Skipping non-English article: {title}")
            continue

        if not title or not description or not content:
            print(f"Missing detailed content, generating content from title and description: {title}")
            content = description if description else "Technology news update"

        # Use ChatGPT to generate the blog content
        blog_content = generate_blog_content(title, description, content)

        # Post the generated content to Blogger
        post_to_blogger(blog_content, title)
        break
    else:
        print("No valid articles to publish.")

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
