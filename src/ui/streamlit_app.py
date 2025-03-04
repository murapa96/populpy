import streamlit as st
from pytrends.request import TrendReq
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now import with the correct path structure
from src.services.search_providers import (
    GoogleSearchProvider,
    DuckDuckGoSearchProvider,
    BingSearchProvider
)
from src.services.search_service import SearchService
from src.services.analytics import (
    create_trend_chart,
    create_geo_chart,
    create_related_topics_chart
)
from src.services.google_service import (
    get_google_related_searches,
    get_top_results_for_related_searches,
    create_wordcloud,
    get_google_search_trends
)
from src.models.search import SearchManager
import os
from dotenv import load_dotenv
import tempfile
import time
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_session_state() -> None:
    """Initialize session state with default settings if not already present."""
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            # Use consistent env variable names with README
            'google_search_api_key': os.getenv('GOOGLE_API_KEY', ''),
            'custom_search_engine_id': os.getenv('SEARCH_ENGINE_ID', ''),
            'country': 'ES',
            'timeframe': 'today 5-y',
            'max_results': 5,
            'search_providers': ['Google', 'DuckDuckGo', 'Bing'],
            'bing_api_key': os.getenv('BING_API_KEY', ''),
            'show_trends': True,
            'show_geo': True,
            'show_topics': True
        }
    if 'search_manager' not in st.session_state:
        st.session_state.search_manager = SearchManager()

def show_search_engine_settings() -> None:
    """Display search configuration options."""
    with st.expander("⚙️ Configuración de búsqueda", expanded=False):
        st.subheader("Opciones de búsqueda")
        
        # Country selection
        countries = ['ES', 'US', 'MX', 'AR', 'CO', 'PE', 'CL']
        current_country = st.session_state.settings['country']
        default_index = 0 if current_country not in countries else countries.index(current_country)
        
        st.session_state.settings['country'] = st.selectbox(
            "País",
            options=countries,
            index=default_index
        )
        
        # Time period selection
        st.session_state.settings['timeframe'] = st.select_slider(
            "Periodo de tiempo",
            options=['today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'],
            value=st.session_state.settings['timeframe']
        )
        
        # Results count
        st.session_state.settings['max_results'] = st.slider(
            "Número máximo de resultados",
            min_value=1,
            max_value=10,
            value=st.session_state.settings['max_results']
        )

        # Search providers
        st.subheader("Proveedores de búsqueda")
        st.session_state.settings['search_providers'] = st.multiselect(
            "Selecciona los proveedores",
            options=['Google', 'DuckDuckGo', 'Bing'],
            default=st.session_state.settings['search_providers']
        )

        # Bing API key
        if 'Bing' in st.session_state.settings['search_providers']:
            st.session_state.settings['bing_api_key'] = st.text_input(
                "API Key de Bing",
                value=st.session_state.settings['bing_api_key'],
                type="password"
            )

        # Visualization options
        st.subheader("Visualizaciones")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.settings['show_trends'] = st.checkbox(
                "Tendencias temporales",
                value=st.session_state.settings['show_trends']
            )
        
        with col2:
            st.session_state.settings['show_geo'] = st.checkbox(
                "Distribución geográfica",
                value=st.session_state.settings['show_geo']
            )
        
        with col3:
            st.session_state.settings['show_topics'] = st.checkbox(
                "Temas relacionados",
                value=st.session_state.settings['show_topics']
            )

        # Reset button
        if st.button("Restaurar valores por defecto"):
            init_session_state()
            st.experimental_rerun()

def show_api_settings() -> None:
    """Display API configuration options."""
    with st.expander("🔑 Configuración de APIs", expanded=False):
        st.subheader("APIs de Google")
        
        st.session_state.settings['google_search_api_key'] = st.text_input(
            "API Key de Google Search",
            value=st.session_state.settings['google_search_api_key'],
            type="password",
            help="Introduce tu API Key de Google Custom Search"
        )
        
        st.session_state.settings['custom_search_engine_id'] = st.text_input(
            "ID del Motor de Búsqueda",
            value=st.session_state.settings['custom_search_engine_id'],
            help="Introduce el ID de tu motor de búsqueda personalizado"
        )

def show_history() -> None:
    """Display search history in the sidebar."""
    st.sidebar.header("📚 Historial de búsquedas")
    recent_searches = st.session_state.search_manager.get_recent_searches()
    
    if not recent_searches:
        st.sidebar.info("No hay búsquedas recientes")
        return
    
    for search in recent_searches:
        with st.sidebar.expander(f"🔍 {search.query}"):
            st.write(f"🌍 {search.country}")
            st.write(f"⏰ {search.timestamp.strftime('%Y-%m-%d %H:%M')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Cargar", key=f"load_{search.id}"):
                    st.experimental_set_query_params(load=search.id)
                    st.experimental_rerun()
            with col2:
                if st.button("🗑️ Eliminar", key=f"delete_{search.id}"):
                    st.experimental_set_query_params(delete=search.id)
                    st.experimental_rerun()

def load_custom_css() -> None:
    """Load custom CSS for styling."""
    css = """
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1e88e5;
    }
    
    .search-result-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1e88e5;
        transition: transform 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .search-result-card:hover {
        transform: translateX(5px);
    }
    
    .chart-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #1e88e5;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 20px auto;
        display: block;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def get_trends_data_with_retry(query: str, retries: int = 3, delay: int = 2) -> Optional[TrendReq]:
    """
    Get PyTrends data with retry logic
    
    Args:
        query: Search query
        retries: Number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        PyTrends object if successful, None otherwise
    """
    for attempt in range(retries):
        try:
            if attempt > 0:
                time.sleep(delay)
                
            # Initialize PyTrends
            pytrends = TrendReq(hl='es')
            pytrends.build_payload(
                [query],
                timeframe=st.session_state.settings['timeframe'],
                geo=st.session_state.settings['country']
            )
            return pytrends
            
        except Exception as e:
            logger.warning(f"PyTrends retry {attempt+1}/{retries} failed: {str(e)}")
            
            # Only show warning on last attempt
            if attempt == retries - 1:
                st.warning(f"⚠️ Error al conectar con Google Trends: {str(e)}")
                
    return None

def main() -> None:
    """Main application function."""
    # Configure page
    st.set_page_config(
        page_title="PopulPy - Análisis de Tendencias",
        page_icon="📊",
        layout="wide"
    )
    
    # Load environment variables and initialize state
    load_dotenv()
    init_session_state()
    load_custom_css()
    
    # Display page header
    st.markdown("<h1 class='main-header'>📊 PopulPy - Análisis de Tendencias de Búsqueda</h1>", unsafe_allow_html=True)
    
    # Show sidebar components
    show_history()
    
    # Show settings
    col1, col2 = st.columns(2)
    with col1:
        show_search_engine_settings()
    with col2:
        show_api_settings()
    
    # Search input
    initial_query = ""
    query_params = st.experimental_get_query_params()
    
    # Handle loading a previous search
    if 'load' in query_params:
        search_id = query_params['load'][0]
        loaded_search = st.session_state.search_manager.get_search_by_id(search_id)
        if loaded_search:
            st.session_state.settings.update(loaded_search.settings)
            initial_query = loaded_search.query
    else:
        initial_query = st.session_state.get('last_query', '')
    
    # Handle deleting a search
    if 'delete' in query_params:
        search_id = query_params['delete'][0]
        if st.session_state.search_manager.delete_search(search_id):
            st.experimental_set_query_params()
            st.experimental_rerun()
    
    # Main search input
    query = st.text_input(
        "🔍 Introduce un término de búsqueda:",
        value=initial_query,
        help="Escribe lo que quieres buscar y presiona Enter"
    )
    st.session_state['last_query'] = query
    
    # Skip processing if no query
    if not query:
        return
    
    # Verify API keys
    if not st.session_state.settings['google_search_api_key'] or not st.session_state.settings['custom_search_engine_id']:
        st.error("⚠️ Por favor, configura las APIs de Google en el menú 'Configuración de APIs'")
        return
    
    # Initialize PyTrends
    with st.spinner('Conectando con Google Trends...'):
        pytrends = get_trends_data_with_retry(query)
        
        if pytrends is None:
            st.error("❌ No se pudo conectar con Google Trends después de varios intentos.")
            return
    
    # Perform search
    with st.spinner('🔄 Buscando información...'):
        try:
            # Configure search parameters
            search_config = {
                'api_key': st.session_state.settings['google_search_api_key'],
                'cx': st.session_state.settings['custom_search_engine_id'],
                'bing_api_key': st.session_state.settings['bing_api_key']
            }
            
            # Fetch search results from selected providers
            search_results = SearchService.get_all_results(
                query,
                st.session_state.settings['search_providers'],
                search_config
            )
            
            # Get trends data once and reuse it
            trends_data = None
            geo_data = None
            related_topics = None
            
            # Only fetch additional data if visualization is enabled
            if st.session_state.settings['show_trends']:
                try:
                    trends_data = get_google_search_trends(query, pytrends)
                except Exception as e:
                    logger.warning(f"Error getting trends data: {str(e)}")
            
            if st.session_state.settings['show_geo']:
                try:
                    geo_data = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
                except Exception as e:
                    logger.warning(f"Error getting geographic data: {str(e)}")
                    
            if st.session_state.settings['show_topics']:
                try:
                    related_topics = pytrends.related_topics()
                except Exception as e:
                    logger.warning(f"Error getting related topics: {str(e)}")
            
            # Save search to history
            st.session_state.search_manager.add_search(
                query=query,
                settings=st.session_state.settings.copy(),
                country=st.session_state.settings['country'],
                results=search_results
            )
            
            # Show warning if no results found
            if not any(search_results.values()):
                st.warning("⚠️ No se encontraron resultados de búsqueda.")
                return
            
            # Display results
            col1, col2 = st.columns([2, 1])
            
            # Display search results
            with col1:
                st.header("🔍 Resultados de búsqueda")
                
                # Process each provider's results
                tabs = st.tabs([f"{provider} ({len(results)})" for provider, results in search_results.items()])
                
                for i, (provider, results) in enumerate(search_results.items()):
                    with tabs[i]:
                        if results:
                            for result in results:
                                st.markdown(
                                    f'<div class="search-result-card">• <a href="{result["link"]}" target="_blank">{result["title"]}</a></div>',
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info(f"ℹ️ No hay resultados disponibles de {provider}.")
            
            # Display visualizations
            with col2:
                # Word cloud
                st.header("☁️ Nube de palabras")
                with st.container():
                    wordcloud_data = [result['title'] for provider_results in search_results.values() for result in provider_results]
                    
                    if wordcloud_data:
                        with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                            try:
                                create_wordcloud(
                                    wordcloud_data,
                                    tmp.name,
                                    background_color='white',
                                    colormap='viridis'
                                )
                                st.image(tmp.name)
                            except Exception as e:
                                st.error(f"Error al generar la nube de palabras: {str(e)}")
                    else:
                        st.info("ℹ️ No hay suficientes datos para generar una nube de palabras.")
                
                # Trends chart
                if st.session_state.settings['show_trends'] and trends_data is not None:
                    st.header("📈 Tendencias temporales")
                    with st.container():
                        if trends_data and isinstance(trends_data, dict) and trends_data.get('dates'):
                            st.plotly_chart(create_trend_chart(trends_data, query), use_container_width=True)
                        else:
                            st.info("ℹ️ No hay datos de tendencias disponibles.")
                
                # Geographic chart
                if st.session_state.settings['show_geo'] and geo_data is not None:
                    st.header("🗺️ Distribución geográfica")
                    with st.container():
                        if not geo_data.empty and query in geo_data.columns:
                            geo_chart = create_geo_chart(geo_data, query)
                            if geo_chart is not None:
                                st.plotly_chart(geo_chart, use_container_width=True)
                            else:
                                st.info("ℹ️ No hay suficientes datos geográficos.")
                        else:
                            st.info("ℹ️ No hay datos geográficos disponibles.")
                
                # Related topics
                if st.session_state.settings['show_topics'] and related_topics is not None:
                    st.header("🔗 Temas relacionados")
                    with st.container():
                        if related_topics and query in related_topics:
                            topic_data = related_topics[query].get('top', None)
                            if topic_data is not None and not topic_data.empty:
                                topics_chart = create_related_topics_chart({'top': topic_data}, query)
                                if topics_chart is not None:
                                    st.plotly_chart(topics_chart, use_container_width=True)
                                else:
                                    st.info("ℹ️ No hay suficientes temas relacionados.")
                            else:
                                st.info("ℹ️ No hay temas relacionados disponibles.")
                        else:
                            st.info("ℹ️ No hay datos de temas relacionados.")
                    
        except Exception as e:
            logger.error(f"Error in search process: {str(e)}", exc_info=True)
            st.error(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()