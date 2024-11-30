import argparse
import logging
import os
import csv
from dotenv import load_dotenv
from pytrends.request import TrendReq

from src.services.google_service import (
    get_top_results_for_related_searches,
    create_wordcloud
)

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="Query to search on Google", required=True)
    parser.add_argument("-c", "--country", help="Country to search in", default="es")
    parser.add_argument("-w", "--wordcloud", help="Path to save the wordcloud image")
    return parser.parse_args()

def save_related_searches_to_csv(related_searches, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['Related Search', 'Result 1', 'Result 2', 'Result 3', 'Result 4', 'Result 5']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for search, results in related_searches.items():
            row = {'Related Search': search}
            for i, result in enumerate(results, 1):
                row[f"Result {i}"] = result
            writer.writerow(row)

if __name__ == "__main__":
    args = parse_args()
    load_dotenv()
    pytrends = TrendReq()
    
    try:
        related_searches_with_results = get_top_results_for_related_searches(
            args.query, 
            pytrends, 
            os.getenv("google_search_api_key"), 
            os.getenv("custom_search_engine_id")
        )
        
        save_related_searches_to_csv(related_searches_with_results, f"{args.query}_related_searches.csv")
        
        if args.wordcloud:
            related_searches = list(related_searches_with_results.keys())
            create_wordcloud(related_searches, args.wordcloud)
            
    except Exception as e:
        logger.error(f"Error durante la ejecución: {str(e)}")
