# Populpy

This script allows users to fetch related searches for a given query from Google Trends, and for each related search, it retrieves the date it was most popular and its popularity score. Additionally, it has the capability to generate a word cloud based on these related searches and fetches top search results for them using the Google Custom Search API.

## Setup

### Prerequisites

1. Python 3.x
2. A Google Cloud account with access to the Custom Search API
3. A configured Custom Search Engine

### Installation

1. Clone this repository:

```bash
git clone https://github.com/murapa96/populpy
cd populpy
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### `.env` Configuration

You need to create a `.env` file in the root directory of the project with the following structure:

```env
google_search_api_key=YOUR_GOOGLE_SEARCH_API_KEY
custom_search_engine_id=YOUR_CUSTOM_SEARCH_ENGINE_ID
```

Replace `YOUR_GOOGLE_SEARCH_API_KEY` with your Google Search API key and `YOUR_CUSTOM_SEARCH_ENGINE_ID` with your Custom Search Engine ID.
You can edit *example.env* and rename it to *.env*


## Usage

### Basic Usage

To run the script with a query:

```bash
python main.py -q "YOUR_QUERY"
```

Replace `YOUR_QUERY` with the query you want to analyze.

### Additional Options

- To specify a country for the search:

```bash
python main.py -q "YOUR_QUERY" -c "COUNTRY_CODE"
```

Replace `COUNTRY_CODE` with the desired country's code (e.g., `us` for the United States, `es` for Spain).

- To generate a word cloud for the related searches:

```bash
python main.py -q "YOUR_QUERY" -w "PATH_TO_SAVE_IMAGE"
```

Replace `PATH_TO_SAVE_IMAGE` with the path where you'd like to save the generated word cloud image.

## Contributing

If you'd like to contribute, please fork the repository and make changes as you'd like. Pull requests are warmly welcome.

## License

This project is open-sourced software licensed under the MIT license.
