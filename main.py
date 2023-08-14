import argparse
import logging
import os
import csv
from datetime import datetime

import matplotlib.pyplot as plt
from wordcloud import WordCloud
from pytrends.request import TrendReq
from dotenv import load_dotenv
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="Query to search on Google", required=True)
    parser.add_argument("-c", "--country", help="Country to search in", default="es")
    parser.add_argument("-w", "--wordcloud", help="Path to save the wordcloud image")
    return parser.parse_args()


def get_google_related_searches(query, pytrends):
    pytrends.build_payload(kw_list=[query], timeframe='today 5-y')
    related_queries = pytrends.related_queries()
    return related_queries.get(query, {}).get('top', {}).get('query', []).tolist()


def get_google_search_trends(query, pytrends):
    pytrends.build_payload(kw_list=[query], timeframe='today 5-y')
    trends_df = pytrends.interest_over_time()
    if not trends_df.empty:
        trend = trends_df[query].idxmax()
        trend_popularity = trends_df[query].max()
        return trend.strftime('%Y-%m-%d'), trend_popularity
    else:
        return None, None


def create_wordcloud(related_searches, path):
    text = " ".join(related_searches)
    wordcloud = WordCloud(width=800, height=800, background_color='white', min_font_size=10).generate(text)
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(path)


def get_top_results_for_related_searches(query, pytrends, api_key, cx):
    related_searches = get_google_related_searches(query, pytrends)[:5]
    base_url = "https://www.googleapis.com/customsearch/v1"
    results = {}
    for search in related_searches:
        response = requests.get(base_url, params={"key": api_key, "cx": cx, "q": search})
        if response.status_code == 200:
            items = response.json().get("items", [])[:5]
            results[search] = [item["title"] for item in items]
    return results


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


def main():
    args = parse_args()
    load_dotenv()
    pytrends = TrendReq()
    related_searches_with_results = get_top_results_for_related_searches(
        args.query, 
        pytrends, 
        os.getenv("google_search_api_key"), 
        os.getenv("custom_search_engine_id")
    )
    save_related_searches_to_csv(related_searches_with_results, f"{args.query}_related_searches.csv")
    logger.info(f"Related Searches and their top results for {args.query}:")
    for search, results in related_searches_with_results.items():
        logger.info(f"\n{search}:")
        for result in results:
            logger.info(f" - {result}")
    if args.wordcloud:
        related_searches = list(related_searches_with_results.keys())
        create_wordcloud(related_searches, args.wordcloud)


if __name__ == "__main__":
    main()
