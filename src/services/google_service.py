import requests
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def get_google_related_searches(query, pytrends):
    pytrends.build_payload([query])
    related_queries = pytrends.related_queries()
    if query in related_queries and 'top' in related_queries[query]:
        return [item['query'] for item in related_queries[query]['top'].to_dict('records')]
    return []

def get_google_search_trends(query: str, pytrends) -> dict:
    """
    Get Google Trends data for a search query
    """
    try:
        # Build the payload
        pytrends.build_payload([query])
        
        # Get interest over time
        interest_over_time_df = pytrends.interest_over_time()
        
        if interest_over_time_df.empty:
            return {'dates': [], 'values': []}
            
        # Convert datetime index to strings and values to lists
        return {
            'dates': interest_over_time_df.index.astype(str).tolist(),
            'values': interest_over_time_df[query].tolist()
        }
        
    except Exception as e:
        print(f"Error getting trends data: {str(e)}")
        return {'dates': [], 'values': []}

def create_wordcloud(related_searches, path, background_color='white', colormap='viridis'):
    text = ' '.join(related_searches)
    wordcloud = WordCloud(
        width=800, 
        height=400,
        background_color=background_color,
        colormap=colormap
    ).generate(text)
    
    plt.figure(figsize=(10,5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()

def get_top_results_for_related_searches(query, pytrends, api_key, cx):
    related_searches = get_google_related_searches(query, pytrends)
    results = {}
    
    for search in related_searches:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cx,
            'q': search,
            'num': 5
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            results[search] = [item['title'] for item in items]
        
    return results
