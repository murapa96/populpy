#!/usr/bin/env python3
"""
PopulPy - Command Line Interface
Use this module to access PopulPy features from the command line
"""
import argparse
import logging
import os
import csv
import sys
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from pytrends.request import TrendReq
    from src.services.google_service import (
        get_top_results_for_related_searches,
        create_wordcloud,
        get_google_search_trends,
        get_google_related_searches
    )
except ImportError as e:
    logger.error(f"Required package not found: {e}")
    logger.error("Please install required packages using: pip install -r requirements.txt")
    sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PopulPy - Analyze search trends across multiple providers"
    )
    parser.add_argument("-q", "--query", 
                      help="Query to search on Google", 
                      required=True)
    parser.add_argument("-c", "--country", 
                      help="Country code to search in (e.g., ES, US)", 
                      default="ES")
    parser.add_argument("-t", "--timeframe", 
                      help="Timeframe for trend analysis (e.g., 'today 5-y')", 
                      default="today 5-y")
    parser.add_argument("-w", "--wordcloud", 
                      help="Path to save the wordcloud image", 
                      default="wordcloud.png")
    parser.add_argument("-o", "--output",
                      help="Output file path for related searches data",
                      default=None)
    parser.add_argument("--no-wordcloud", 
                      help="Skip generating wordcloud", 
                      action="store_true")
    return parser.parse_args()

def save_related_searches_to_csv(related_searches: Dict[str, List[str]], 
                               filename: str) -> None:
    """
    Save related searches and their results to a CSV file.
    
    Args:
        related_searches: Dictionary with related searches and their results
        filename: Path to save the CSV file
    """
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Related Search', 'Result 1', 'Result 2', 'Result 3', 'Result 4', 'Result 5']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            
            for search, results in related_searches.items():
                row = {'Related Search': search}
                for i, result in enumerate(results, 1):
                    if i <= 5:  # Ensure we don't go beyond our fieldnames
                        row[f"Result {i}"] = result
                writer.writerow(row)
                
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving results to {filename}: {e}")
        
def main() -> None:
    """Main entry point for the CLI application."""
    args = parse_args()
    load_dotenv()
    
    # Verify required environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    cx_id = os.getenv("SEARCH_ENGINE_ID")
    
    if not api_key or not cx_id:
        logger.error("Missing required environment variables. Please set GOOGLE_API_KEY and SEARCH_ENGINE_ID.")
        sys.exit(1)
    
    try:
        # Initialize PyTrends
        logger.info(f"Initializing PyTrends for query '{args.query}' in {args.country}")
        pytrends = TrendReq(hl=args.country.lower())
        pytrends.build_payload([args.query], timeframe=args.timeframe, geo=args.country)
        
        # Get related searches
        logger.info("Getting related searches...")
        related_searches = get_google_related_searches(args.query, pytrends)
        
        if not related_searches:
            logger.warning("No related searches found")
            return
            
        # Get search results for related searches
        logger.info("Getting search results for related searches...")
        related_searches_with_results = get_top_results_for_related_searches(
            args.query, pytrends, api_key, cx_id
        )
        
        # Save results to CSV if requested
        output_file = args.output or f"{args.query.replace(' ', '_')}_related_searches.csv"
        save_related_searches_to_csv(related_searches_with_results, output_file)
        
        # Create wordcloud if requested
        if not args.no_wordcloud:
            logger.info(f"Creating wordcloud at {args.wordcloud}...")
            create_wordcloud(related_searches, args.wordcloud)
            logger.info(f"Wordcloud saved to {args.wordcloud}")
        
        logger.info("Analysis complete!")
        
    except KeyboardInterrupt:
        logger.info("Operation canceled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
