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
        'maxrecords': 150,  # Number of articles to fetch
        'format': 'json'  # Ensure the response is in JSON format
    }

    try:
        response = requests.get(gdelt_url, params=params)
        
        # Log the status code and content for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        # Check if response is valid
        if response.status_code == 200:
            try:
                articles = response.json().get('articles', [])
                if not articles:
                    print("No articles found in the response.")
                else:
                    print(f"Fetched {len(articles)} articles.")
                return articles
            except requests.exceptions.JSONDecodeError:
                print("Error decoding the JSON response. Check API response.")
                return []
        else:
            print(f"Error fetching articles: {response.status_code}. Retrying...")
            return []

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

def translate_to_english(text, language):
    prompt = f"Translate the following {language} text into English:\n\n{text}"

    response = openai.Completion.create(
        model="gpt-4",
        prompt=prompt,
        max_tokens=1000
    )

    return response['choices'][0]['text']

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
    while True:  # Loop until a valid English article is found
        print("Fetching and publishing a new blog post...")
        articles = get_news_articles()

        if not articles:
            print("No articles found. Retrying...")
            time.sleep(10)  # Wait a bit before retrying
            continue

        for article in articles:
            # Ensure the article contains necessary fields
            title = article.get('title', 'Untitled Article')  # Fallback if title is missing
            description = article.get('seendescription', article.get('summary', 'No description available.'))  # Fallback if description is missing
            content = article.get('body', article.get('extrasummary'))  # Trying multiple possible content fields
            
            # If content is still None, try to create a fallback using title and description
            if not content:
                print(f"Missing detailed content, generating content from title and description: {title}")
                content = f"{title} - {description}"

            language = article.get('language', 'English')

            # If the article is not in English, translate it
            if language.lower() != 'english':
                print(f"Translating non-English article from {language}: {title}")
                content = translate_to_english(content, language)

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
