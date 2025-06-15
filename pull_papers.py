import os
import requests
import logging
import time  # Add time module for sleep functionality
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin

# Configure logging
def setup_logging(log_level=logging.INFO, log_file=None):
    """Set up logging configuration"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Create logger
    logger = logging.getLogger("paper_puller")
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger

# Initialize logger with default settings
logger = setup_logging()

HEADERS = {"User-Agent": "Mozilla/5.0"}

def daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def get_arxiv_ids(date: datetime):
    url = f"https://huggingface.co/papers/date/{date.strftime('%Y-%m-%d')}"
    logger.info(f"Fetching papers from {url}")
    
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Select the first 5 paper links and extract the arXiv ID
        anchors = soup.select("div.w-full h3 a")[:5]
        arxiv_ids = [a["href"].split("/")[-1] for a in anchors]  # Get just the arXiv ID
        
        logger.info(f"Found {len(arxiv_ids)} papers for {date.strftime('%Y-%m-%d')}")
        logger.debug(f"ArXiv IDs: {arxiv_ids}")
        return arxiv_ids
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing papers from {url}: {e}")
        raise

def download_arxiv_pdf(arxiv_id: str, dest_folder: str, filename: str):
    filepath = os.path.join(dest_folder, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"File already exists: {filepath}, skipping download")
        print(f"    ↳ Already downloaded: {filename}")
        return
    
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    logger.info(f"Downloading {pdf_url}")
    
    try:
        resp = requests.get(pdf_url, stream=True, headers=HEADERS)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Successfully downloaded: {pdf_url} to {filepath}")
            print(f"    ↳ Downloaded: {pdf_url}")
        else:
            logger.warning(f"PDF not found for {arxiv_id} (status {resp.status_code})")
            print(f"    ❌ PDF not found for {arxiv_id} (status {resp.status_code})")
    except Exception as e:
        logger.error(f"Error downloading {pdf_url}: {e}")
        raise

def main(start_date, end_date, out_dir="papers"):
    logger.info(f"Starting paper download from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"Output directory: {out_dir}")
    
    os.makedirs(out_dir, exist_ok=True)
    logger.debug(f"Ensured output directory exists: {out_dir}")

    for dt in daterange(start_date, end_date):
        logger.info(f"Processing date: {dt.strftime('%Y-%m-%d')}")
        print(f"\n=== {dt.strftime('%Y-%m-%d')} ===")
        
        try:
            arxiv_ids = get_arxiv_ids(dt)
        except Exception as e:
            error_msg = f"Failed to get paper links for {dt}: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            continue

        for i, arxiv_id in enumerate(arxiv_ids, 1):
            filename = f"{dt.strftime('%Y%m%d')}_paper{i}_{arxiv_id}.pdf"
            try:
                download_arxiv_pdf(arxiv_id, out_dir, filename)
                # Add 1 second sleep between paper downloads
                if i < len(arxiv_ids):  # Don't sleep after the last paper
                    logger.debug("Sleeping for 1 second before next download")
                    time.sleep(1)
            except Exception as e:
                error_msg = f"Error downloading {arxiv_id}: {e}"
                logger.error(error_msg)
                print(f"    ❌ {error_msg}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--out", default="papers", help="Output folder")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Configure logging based on command line arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level=log_level, log_file=args.log_file)
    
    logger.debug("Script started with arguments: " + str(vars(args)))

    try:
        sd = datetime.strptime(args.start, "%Y-%m-%d")
        ed = datetime.strptime(args.end, "%Y-%m-%d")
        main(sd, ed, args.out)
        logger.info("Script completed successfully")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"❌ Critical error: {e}")
        exit(1)