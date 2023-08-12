import requests
import os
from dotenv import load_dotenv
import argparse
import csv
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Load variables from .env file
load_dotenv()

# Access the google_search_api_key variable
google_search_api_key = os.environ.get('google_search_api_key')
custom_search_engine_id = os.environ.get('custom_search_engine_id')
google_trends_api_key = os.environ.get('google_trends_api_key')


def get_google_search_results(query, api_key, cx, country):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cx}&key={api_key}&cr={country}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        search_results = [(item["title"], item["link"]) for item in items]
        return search_results
    else:
        print(f"Error: {response.status_code}")
        return []


def get_google_search_trends(query, api_key, country):
    url = f"https://trends.googleapis.com/trends/api/dailytrends?hl=en-US&tz=240&geo={country}&ed={query}&ns=15"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        trends = data.get("default", {}).get("trendingSearchesDays", [])
        if trends:
            trend = trends[0]["trendingSearches"][0]
            return trend["title"]["query"], trend["formattedTraffic"]
    else:
        print(f"Error: {response.status_code}")

    return query, "N/A"


def get_google_common_searches(query, api_key, cx, country):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cx}&key={api_key}&cr={country}&num=10"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        queries = data.get("queries", {}).get("nextPage", [])
        if queries:
            return [q["title"] for q in queries]
    else:
        print(f"Error: {response.status_code}")

    return []


def create_wordcloud(common_searches, path):
    text = " ".join(common_searches)
    wordcloud = WordCloud(
        width=800, height=800, background_color='white', min_font_size=10).generate(text)
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q", "--query", help="Query to search on Google", required=True)
    parser.add_argument("-c", "--country",
                        help="Country to search in", default="Spain")
    parser.add_argument("-w", "--wordcloud",
                        help="Path to save the wordcloud image")
    args = parser.parse_args()

    query = args.query
    country = args.country

    search_results = get_google_search_results(
        query, google_search_api_key, custom_search_engine_id, country)
    trend_query, trend_popularity = get_google_search_trends(
        query, google_trends_api_key, country)
    common_searches = get_google_common_searches(
        query, google_search_api_key, custom_search_engine_id, country)

    if args.wordcloud:
        create_wordcloud(common_searches, args.wordcloud)

    # Export search results, trend popularity and common searches to CSV
    with open('results.csv', mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(['Search Results'])
        for idx, result in enumerate(search_results, 1):
            writer.writerow([f"{idx}. {result[0]} - {result[1]}"])
        writer.writerow([''])
        writer.writerow(['Trend Popularity'])
        writer.writerow([f"{trend_query} - {trend_popularity}"])
        writer.writerow([''])
        writer.writerow(['Common Searches'])
        for idx, search in enumerate(common_searches, 1):
            writer.writerow([f"{idx}. {search}"])

    print("Resultados de búsqueda de Google:")
    for idx, result in enumerate(search_results, 1):
        print(f"{idx}. {result[0]} - {result[1]}")

    print("\nPopularidad en Google Trends:")
    print(f"{trend_query} - {trend_popularity}")

    print("\nBúsquedas comunes en Google:")
    for idx, search in enumerate(common_searches, 1):
        print(f"{idx}. {search}")


if __name__ == "__main__":
    main()
