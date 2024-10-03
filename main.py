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
        'maxrecords': 100,  # Number of articles to fetch
        'format': 'json',  # Ensure the response is in JSON format
        'filter': 'lang:english'  # Filter articles to only English language
    }

    response = requests.get(gdelt_url, params=params)

    if response.status_code == 200:
        articles = response.json().get('articles', [])
        if not articles:
            print("No articles found in the response.")
        else:
            print(f"Fetched {len(articles)} articles.")
        return articles
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
    while True:  # Loop until a valid article is found
        print("Fetching and publishing a new blog post...")
        articles = get_news_articles()

        if not articles:
            print("No articles found. Retrying...")
            time.sleep(10)  # Wait a bit before retrying
            continue

        for article in articles:
            # Ensure the article is in English and contains necessary fields
            if article.get('language') != 'English':
                print(f"Skipping non-English article: {article.get('title', 'No title')}")
                continue

            title = article.get('title', 'Untitled Article')  # Fallback if title is missing
            description = article.get('seendescription', article.get('summary', 'No description available.'))  # Fallback if description is missing
            content = article.get('body', article.get('extrasummary', 'No content available.'))  # Fallback if content is missing

            if not content or content == 'No content available.':
                print("Missing content in the article, skipping...")
                continue

            # Use ChatGPT to generate the blog content
            blog_content = generate_blog_content(title, description, content)

            # Post the generated content to Blogger
            post_to_blogger(blog_content, title)

            # Once a valid article is published, exit the loop
            return

        print("No valid articles to publish. Retrying...")
        time.sleep(10)  # Wait a bit before retrying

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
