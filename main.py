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

def get_news_articles():
    url = f"https://newsapi.org/v2/everything?q=technology&sortBy=publishedAt&apiKey={GOOGLE_NEWS_API_KEY}"
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles

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
    description = article.get('description')
    content = article.get('content')

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
