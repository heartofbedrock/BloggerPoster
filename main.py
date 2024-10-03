import openai
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apscheduler.schedulers.blocking import BlockingScheduler

# Set up your API keys
OPENAI_API_KEY = 'your_openai_api_key'
BLOGGER_API_KEY = 'your_blogger_api_key'
BLOGGER_BLOG_ID = 'your_blogger_blog_id'

# OpenAI configuration
openai.api_key = OPENAI_API_KEY

# Function to get news articles from GDELT API
def get_news_articles():
    gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc?query=technology&mode=artlist&maxrecords=10&format=json&filter=lang:english"

    response = requests.get(gdelt_url, params=params)
    
    # Debugging: Print raw response content
    print(f"API response: {response.text}")
    
    # Check if the request was successful
    if response.status_code == 200:
        articles = response.text.split('\n')
        article_list = []
        
        for article in articles:
            # Articles are returned in a tab-separated format: URL, Title, Date, Source, etc.
            if article.strip():  # Ignore empty lines
                article_data = article.split('\t')
                if len(article_data) >= 4:  # Ensure we have at least title, URL, date, and source
                    article_list.append({
                        'title': article_data[2],  # Title of the article
                        'url': article_data[0],  # URL of the article
                        'publishedAt': article_data[3],  # Date of publication
                        'source': article_data[4]  # Source of the article
                    })
        # Debugging: Print parsed articles
        print(f"Parsed articles: {article_list}")
        
        return article_list
    else:
        print(f"Error fetching articles: {response.status_code}")
        return []

# Function to generate blog content using GPT
def generate_blog_content(article_title, article_url):
    prompt = f"Create a blog post about the following article titled '{article_title}'. You can find the article here: {article_url}. Please summarize and expand the content of the article, adding additional insights."

    response = openai.Completion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=1000
    )
    return response['choices'][0]['text']

# Function to post the generated content to Blogger
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

# Function to fetch articles and publish blog posts
def fetch_and_publish():
    print("Fetching and publishing a new blog post...")
    articles = get_news_articles()

    if not articles:
        print("No articles found.")
        return

    article = articles[0]  # Get the latest article
    title = article.get('title')
    url = article.get('url')

    # Use GPT to generate blog content
    blog_content = generate_blog_content(title, url)

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
