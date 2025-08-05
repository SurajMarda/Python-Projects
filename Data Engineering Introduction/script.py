import os
import sys
import csv
import requests
import logging
import boto3
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup

# Configure logging for better feedback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# It's highly recommended to use environment variables for sensitive credentials
# rather than hardcoding them or importing from a local file that might be committed.
# For example:
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# If you must use a file for local development, ensure 'auth.py' is in .gitignore.
try:
    from auth import ACCESS_KEY, SECRET_KEY
except ImportError:
    logging.error("auth.py not found or ACCESS_KEY/SECRET_KEY not defined. "
                  "Please ensure your AWS credentials are set as environment variables "
                  "or defined in auth.py (and auth.py is in .gitignore).")
    # Fallback to environment variables if auth.py is not available
    ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
    SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Define constants for better readability and easier modification
SOURCE_URL = 'http://127.0.0.1:5500/'
CSV_FILE_NAME = 'data.csv'
S3_BUCKET_NAME = 'aws-data-engineering-csv-etl-pipeline-demo'
S3_OBJECT_KEY = 'data.csv' # The name of the file in the S3 bucket

def fetch_and_parse_data(url: str) -> list[dict]:
    """
    Fetches web content from the given URL and parses it to extract article data.

    Args:
        url (str): The URL of the web page to scrape.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an article
                    with 'headline', 'summary', and 'link'. Returns an empty list on failure.
    """
    logging.info(f"Attempting to fetch data from: {url}")
    try:
        response = requests.get(url, timeout=10) # Add a timeout for robustness
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.Timeout:
        logging.error(f"Request timed out when fetching from {url}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    articles_data = []

    articles = soup.find_all('article')
    if not articles:
        logging.warning("No 'article' tags found on the page. Check HTML structure or URL.")
        return []

    for i, article in enumerate(articles):
        try:
            headline_tag = article.h2.a
            summary_tag = article.p

            headline = headline_tag.text.strip() if headline_tag else 'N/A'
            summary = summary_tag.text.strip() if summary_tag else 'N/A'
            link = headline_tag["href"].strip() if headline_tag and "href" in headline_tag.attrs else 'N/A'

            articles_data.append({
                'headline': headline,
                'summary': summary,
                'link': link
            })
        except AttributeError as e:
            logging.warning(f"Could not parse article {i+1} due to missing elements: {e}")
            continue # Skip to the next article if elements are missing

    logging.info(f"Successfully extracted {len(articles_data)} articles.")
    return articles_data

def write_data_to_csv(data: list[dict], file_name: str):
    """
    Writes a list of dictionaries to a CSV file.

    Args:
        data (list[dict]): The data to write, where each dict is a row.
        file_name (str): The name of the CSV file to create/overwrite.
    """
    if not data:
        logging.warning("No data to write to CSV. Skipping CSV creation.")
        return

    logging.info(f"Writing data to CSV file: {file_name}")
    try:
        with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['headline', 'summary', 'link'] # Define headers explicitly
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data successfully written to {file_name}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {file_name}: {e}")

def upload_to_s3(file_path: str, bucket_name: str, object_key: str, access_key: str, secret_key: str):
    """
    Uploads a file to an AWS S3 bucket.

    Args:
        file_path (str): The path to the file to upload.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key (path) for the object in the S3 bucket.
        access_key (str): AWS Access Key ID.
        secret_key (str): AWS Secret Access Key.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found at {file_path}. Cannot upload to S3.")
        return

    if not access_key or not secret_key:
        logging.error("AWS credentials not provided. Cannot upload to S3.")
        return

    logging.info(f"Attempting to upload {file_path} to S3 bucket '{bucket_name}' as '{object_key}'")
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        # Check if bucket exists, create if not (handle potential race conditions or permissions)
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' already exists.")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                logging.info(f"Bucket '{bucket_name}' does not exist. Creating it now.")
                s3_client.create_bucket(Bucket=bucket_name)
                logging.info(f"Bucket '{bucket_name}' created successfully.")
            else:
                logging.error(f"Error checking or creating bucket '{bucket_name}': {e}")
                return

        with open(file_path, "rb") as f:
            s3_client.upload_fileobj(f, bucket_name, object_key)
        logging.info('File uploaded to S3 successfully!')
    except ClientError as e:
        logging.error(f"AWS S3 client error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during S3 upload: {e}")

def main():
    """
    Main function to orchestrate the web scraping, CSV writing, and S3 upload process.
    """
    logging.info("Starting ETL pipeline...")

    # 1. Fetch and parse data
    articles_data = fetch_and_parse_data(SOURCE_URL)
    if not articles_data:
        logging.error("No data extracted. Exiting.")
        sys.exit(1) # Exit with an error code

    # 2. Write data to CSV
    write_data_to_csv(articles_data, CSV_FILE_NAME)
    if not os.path.exists(CSV_FILE_NAME):
        logging.error("CSV file was not created. Exiting.")
        sys.exit(1)

    # 3. Upload to AWS S3
    upload_to_s3(CSV_FILE_NAME, S3_BUCKET_NAME, S3_OBJECT_KEY, ACCESS_KEY, SECRET_KEY)

    logging.info('ETL Task Completed Sucessfully!')

if __name__ == '__main__':
    main()
