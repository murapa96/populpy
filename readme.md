# Populpy

This is a Python script that allows you to search Google and get the search results, trend popularity, and common searches for a given query.

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/murapa96/google-search-tool.git
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

3. Set up the environment variables:

   - `google_search_api_key`: Your Google Custom Search API key
   - `custom_search_engine_id`: Your Google Custom Search Engine ID
   - `google_trends_api_key`: Your Google Trends API key

4. Run the script:

   ```
   python main.py -q "query" -c "country"
   ```

   Replace "query" with your search query and "country" with the country you want to search in (default is "Spain").

   You can also add the `-w` or `--wordcloud` option to generate a wordcloud with the most common searches:

   ```
   python main.py -q "query" -c "country" -w "wordcloud.png"
   ```

   Replace "wordcloud.png" with the path where you want to save the wordcloud image.

## Usage

The script takes two command-line arguments:

- `-q` or `--query`: The query to search on Google
- `-c` or `--country`: The country to search in (default is "Spain")
- `-w` or `--wordcloud`: The path to save the wordcloud image (optional)

The script will output the search results, trend popularity, and common searches to the console, and also export them to a CSV file named `results.csv`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

