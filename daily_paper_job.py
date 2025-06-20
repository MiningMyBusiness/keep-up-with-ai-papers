#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime, timedelta
import logging
from pathlib import Path
from markitdown import MarkItDown
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("daily_paper_job.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def extract_paper_info(pdf_path):
    """Extract paper information from the filename."""
    filename = os.path.basename(pdf_path)
    # Extract date and arxiv ID from filename pattern: YYYYMMDD_paperN_XXXX.XXXXX.pdf
    match = re.match(r'(\d{8})_paper(\d+)_(.+)\.pdf', filename)
    if match:
        date_str, paper_num, arxiv_id = match.groups()
        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        return {
            'date': date,
            'number': int(paper_num),
            'arxiv_id': arxiv_id,
            'filename': filename,
            'path': pdf_path
        }
    return None


def generate_markdown(papers_dir, markdown_dir, start_date, end_date):
    """Generate markdown summary of papers."""
    # ... existing code ...
    
    # Process each paper and create individual markdown files
    processed_files = []
    for paper in papers:
        arxiv_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"
        huggingface_url = f"https://huggingface.co/papers/{paper['arxiv_id']}"
        
        # Create individual markdown filename
        md_filename = f"{os.path.splitext(paper['filename'])[0]}.md"
        md_path = os.path.join(markdown_dir, md_filename)
        
        try:
            logger.info(f"Processing PDF with MarkItDown: {paper['path']}")
            paper_summary = markitdown.convert(paper['path']).text_content
            
            # Create markdown content
            content = f"# Paper: {paper['arxiv_id']}\n\n"
            content += f"- **Date**: {paper['date']}\n"
            content += f"- **Paper Number**: {paper['number']}\n"
            content += f"- **ArXiv ID**: [{paper['arxiv_id']}]({arxiv_url})\n"
            content += f"- **HuggingFace Link**: [View on HuggingFace]({huggingface_url})\n\n"
            
            if paper_summary:
                content += "## Paper\n\n"
                content += f"{paper_summary}\n"
            else:
                content += "## Summary\n\n"
                content += "Failed to extract paper as markdown.\n"
            
            # Write markdown file with UTF-8 encoding
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created markdown for paper: {md_path}")
            processed_files.append(md_path)
            
        except Exception as e:
            logger.error(f"Error processing PDF {paper['path']}: {e}")
    
    logger.info(f"Processed {len(processed_files)} papers into markdown files")
    
    # Return the list of processed markdown files
    return processed_files

def run_paper_puller(start_date, end_date, papers_dir):
    """Run the pull_papers.py script to download papers."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pull_papers.py")
    
    cmd = [
        sys.executable,
        script_path,
        "--start", start_date.strftime("%Y-%m-%d"),
        "--end", end_date.strftime("%Y-%m-%d"),
        "--out", papers_dir
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Paper pulling completed successfully")
        logger.debug(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running pull_papers.py: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def main():
    """Main function to run the daily paper job."""
    # Define directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    papers_dir = os.path.join(base_dir, "papers")
    markdown_dir = os.path.join(base_dir, "summaries")
    
    # Calculate date range (yesterday and today)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    
    logger.info(f"Starting daily paper job for {yesterday.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    
    # Run paper puller
    success = run_paper_puller(yesterday, today, papers_dir)
    
    if success:
        # Generate markdown summary
        markdown_files = generate_markdown(papers_dir, markdown_dir, yesterday, today)
        if markdown_files:
            logger.info(f"Daily paper job completed successfully. Markdown files created: {', '.join(markdown_files)}")
        else:
            logger.info("Daily paper job completed successfully. No new markdown files created.")
    else:
        logger.error("Daily paper job failed due to errors in paper pulling.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Unhandled exception in daily paper job: {e}")
        sys.exit(1)