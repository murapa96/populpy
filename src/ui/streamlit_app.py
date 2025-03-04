import streamlit as st
from pytrends.request import TrendReq
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_session_state():
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            # Use consistent env variable names with README
            'google_search_api_key': os.getenv('GOOGLE_API_KEY', ''),
            'custom_search_engine_id': os.getenv('SEARCH_ENGINE_ID', ''),
            'country': 'ES',
            'timeframe': 'today 5-y',
            'max_results': 5,
            'theme': 'light',
            'search_providers': ['Google', 'DuckDuckGo', 'Bing'],
            'bing_api_key': os.getenv('BING_API_KEY', ''),
            'show_trends': True,
            'show_geo': True,
            'show_topics': True
        }
    if 'search_manager' not in st.session_state:
        st.session_state.search_manager = SearchManager()

def show_search_engine_settings():
    with st.expander("⚙️ Configuración de búsqueda", expanded=False):
        st.subheader("Opciones de búsqueda")
        countries = ['ES', 'US', 'MX', 'AR', 'CO', 'PE', 'CL']
        current_country = st.session_state.settings['country']
        default_index = 0 if current_country not in countries else countries.index(current_country)
        
        st.session_state.settings['country'] = st.selectbox(
            "País",
            options=countries,
            index=default_index
        )
        st.session_state.settings['timeframe'] = st.select_slider(
            "Periodo de tiempo",
            options=['today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'],
            value=st.session_state.settings['timeframe']
        )
        st.session_state.settings['max_results'] = st.slider(
            "Número máximo de resultados",
            min_value=1,
            max_value=10,
            value=st.session_state.settings['max_results']
        )

        # Proveedores de búsqueda
        st.subheader("Proveedores de búsqueda")
        st.session_state.settings['search_providers'] = st.multiselect(
            "Selecciona los proveedores",
            options=['Google', 'DuckDuckGo', 'Bing'],
            default=st.session_state.settings['search_providers']
        )

        if 'Bing' in st.session_state.settings['search_providers']:
            st.session_state.settings['bing_api_key'] = st.text_input(
                "API Key de Bing",
                value=st.session_state.settings['bing_api_key'],
                type="password"
            )

        # Mostrar opciones adicionales
        st.subheader("Visualizaciones")
        st.session_state.settings['show_trends'] = st.checkbox(
            "Mostrar tendencias temporales",
            value=st.session_state.settings['show_trends']
        )
        st.session_state.settings['show_geo'] = st.checkbox(
            "Mostrar distribución geográfica",
            value=st.session_state.settings['show_geo']
        )
        st.session_state.settings['show_topics'] = st.checkbox(
            "Mostrar temas relacionados",
            value=st.session_state.settings['show_topics']
        )

        # Botón para restaurar valores por defecto
        if st.button("Restaurar valores por defecto"):
            init_session_state()
            st.experimental_rerun()

def show_api_settings():
    with st.expander("🔑 Configuración de APIs", expanded=False):
        st.subheader("APIs de Google")
        st.session_state.settings['google_search_api_key'] = st.text_input(
            "API Key de Google Search",
            value=st.session_state.settings['google_search_api_key'],
            type="password"
        )
        st.session_state.settings['custom_search_engine_id'] = st.text_input(
            "ID del Motor de Búsqueda",
            value=st.session_state.settings['custom_search_engine_id']
        )

def show_history():
    st.sidebar.header("📚 Historial de búsquedas")
    recent_searches = st.session_state.search_manager.get_recent_searches()
    
    for search in recent_searches:
        st.sidebar.markdown(
            f'''
            <div class="sidebar-search-item">
                <strong>🔍 {search.query}</strong><br>
                🌍 {search.country}<br>
                ⏰ {search.timestamp.strftime('%Y-%m-%d %H:%M')}<br>
                <button class="custom-button" onclick="window.location.href='?load={search.id}'">🔄 Cargar</button>
                <button class="custom-button" onclick="window.location.href='?delete={search.id}'">🗑️ Eliminar</button>
            </div>
            ''',
            unsafe_allow_html=True
        )

def show_theme_button():
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown('<div class="main-title">📊 PopulPy - Análisis de Tendencias de Google</div>', unsafe_allow_html=True)
    with col2:
        theme_icon = "🌞" if st.session_state.settings.get('theme', 'light') == 'light' else "🌜"
        if st.button(theme_icon):
            # Cambiar el tema
            new_theme = 'dark' if st.session_state.settings['theme'] == 'light' else 'light'
            st.session_state.settings['theme'] = new_theme
            st.experimental_rerun()

def load_custom_css():
    """Load custom CSS with theme support"""
    try:
        # Cargar el CSS personalizado
        css_file = os.path.join(os.path.dirname(__file__), '..', 'static', 'styles.css')
        streamlit_css_file = os.path.join(os.path.dirname(__file__), '..', 'static', 'streamlit_styles.css')
        
        css_content = ""
        
        # Load main styles
        try:
            with open(css_file) as f:
                css_content += f.read()
        except FileNotFoundError:
            logger.error(f"CSS file not found: {css_file}")
        
        # Load Streamlit specific styles
        try:
            with open(streamlit_css_file) as f:
                css_content += f.read()
        except FileNotFoundError:
            logger.error(f"Streamlit CSS file not found: {streamlit_css_file}")
        
        # Definir variables de tema
        theme = st.session_state.settings.get('theme', 'light')
        if theme == 'light':
            theme_variables = """
            :root {
            --populpy-primary-color: #ff4b4b;
            --populpy-background-color: #ffffff;
            --populpy-secondary-background: #f0f2f6;
            --populpy-text-color: #333333;
            --populpy-link-color: #ff4b4b;

            --populpy-gradient-start: #1e88e5;
            --populpy-gradient-end: #00ACC1;
            --populpy-box-shadow-color: rgba(0,0,0,0.1);
            --populpy-hover-background: #e9ecef;
            --populpy-card-border-color: #1e88e5;

            --populpy-spinner-border-color: #f3f3f3;
            --populpy-spinner-border-top-color: #1e88e5;
            }
            """
        else:
            theme_variables = """
            :root {
            --populpy-background-color: #0e1117;
            --populpy-secondary-background: #262730;
            --populpy-text-color: #fafafa;
            --populpy-link-color: #ff4b4b;

            --populpy-gradient-start: #1e88e5;
            --populpy-gradient-end: #00ACC1;
            --populpy-box-shadow-color: rgba(255,255,255,0.1);
            --populpy-hover-background: #444654;
            --populpy-card-border-color: #1e88e5;

            --populpy-spinner-border-color: #444654;
            --populpy-spinner-border-top-color: #1e88e5;
            }
            """
        
        # Apply theme wrapper
        st.markdown(f'<style>{theme_variables}\n{css_content}</style>', unsafe_allow_html=True)
        
        # Add theme class to body for proper theming
        st.markdown(f'<div class="theme-{theme}">', unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error loading CSS: {str(e)}")
        # Provide fallback styling
        st.markdown('<style>body { font-family: sans-serif; }</style>', unsafe_allow_html=True)

def close_theme_div():
    # Cerrar el div de la clase de tema
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<style>body{{opacity:1}}</style>', unsafe_allow_html=True)

def get_trends_data_with_retry(query, retries=2, delay=2):
    """Función mejorada para reintentos de PyTrends"""
    for attempt in range(retries):
        try:
            time.sleep(delay)
            # Inicializar PyTrends sin timezone
            pytrends = TrendReq(hl='es')  # Usar idioma español por defecto
            pytrends.build_payload(
                [query],
                timeframe=st.session_state.settings['timeframe'],
                geo=st.session_state.settings['country']
            )
            return pytrends
        except Exception as e:
            if attempt == retries - 1:
                st.warning(f"⚠️ Reintento {attempt + 1} fallido: {str(e)}")
            time.sleep(delay)
    return None

def main():
    st.set_page_config(
        page_title="PopulPy - Análisis de Tendencias",
        page_icon="📊",
        layout="wide"
    )
    
    # Inicializar estado
    load_dotenv()
    init_session_state()

    # Mostrar historial en sidebar
    show_history()

    # Mostrar botón de cambio de tema y título
    show_theme_button()

    # Mostrar configuraciones encima del contenido principal
    show_search_engine_settings()
    show_api_settings()
    # Cargar y aplicar estilos CSS personalizados
    load_custom_css()
    # Input para la búsqueda
    initial_query = ""
    query_params = st.experimental_get_query_params()
    if 'load' in query_params:
        search_id = query_params['load'][0]
        loaded_search = st.session_state.search_manager.get_search_by_id(search_id)
        if loaded_search:
            st.session_state.settings.update(loaded_search.settings)
            initial_query = loaded_search.query
    else:
        initial_query = st.session_state.get('last_query', '')

    query = st.text_input("🔍 Introduce un término de búsqueda:", value=initial_query)
    st.session_state['last_query'] = query

    # Check if we need to handle URL parameters for deleting searches
    query_params = st.experimental_get_query_params()
    if 'delete' in query_params:
        search_id = query_params['delete'][0]
        if st.session_state.search_manager.delete_search(search_id):
            # Clear the URL parameter after deletion
            st.experimental_set_query_params()
            st.experimental_rerun()

    if query:
        if not st.session_state.settings['google_search_api_key'] or not st.session_state.settings['custom_search_engine_id']:
            st.error("⚠️ Por favor, configura las APIs de Google en el menú 'Configuración de APIs'")
            close_theme_div()
            return
        
        try:
            # Simplificar la configuración de PyTrends
            pytrends = get_trends_data_with_retry(query)
            
            if pytrends is None:
                st.error("❌ No se pudo conectar con Google Trends después de varios intentos.")
                close_theme_div()
                return

        except Exception as e:
            st.error(f"❌ Error al conectar con Google Trends: {str(e)}")
            close_theme_div()
            return
                
        st.markdown('<div class="loading-spinner"></div>', unsafe_allow_html=True)
        with st.spinner('🔄 Buscando información...'):
            try:
                # Configurar los parámetros de búsqueda
                search_config = {
                    'api_key': st.session_state.settings['google_search_api_key'],
                    'cx': st.session_state.settings['custom_search_engine_id'],
                    'bing_api_key': st.session_state.settings['bing_api_key']
                }

                # Realizar búsquedas usando el servicio de búsqueda
                search_results = SearchService.get_all_results(
                    query,
                    st.session_state.settings['search_providers'],
                    search_config
                )
                
                # Guardar la búsqueda en el historial después de obtener resultados
                st.session_state.search_manager.add_search(
                    query=query,
                    settings=st.session_state.settings.copy(),
                    country=st.session_state.settings['country'],
                    results=search_results
                )
                
                # Mostrar resultados y estadísticas con manejo de errores
                if not any(search_results.values()):
                    st.warning("⚠️ No se encontraron resultados de búsqueda.")
                    close_theme_div()
                    return

                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.header("🔍 Resultados de búsqueda")
                    for provider, results in search_results.items():
                        with st.expander(f"Resultados de {provider}", expanded=True):
                            if results:
                                for result in results:
                                    st.markdown(
                                        f'<div class="search-result-card">• <a href="{result["link"]}">{result["title"]}</a></div>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.info(f"ℹ️ No hay resultados disponibles de {provider}.")

                with col2:
                    # Generar y mostrar nube de palabras
                    st.header("☁️ Nube de palabras")
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                        wordcloud_data = [result['title'] for provider_results in search_results.values() for result in provider_results]
                        if wordcloud_data:
                            create_wordcloud(
                                wordcloud_data,
                                tmp.name,
                                background_color='white' if st.session_state.settings['theme'] == 'light' else 'black',
                                colormap='viridis'
                            )
                            st.image(tmp.name)
                        else:
                            st.info("ℹ️ No hay suficientes datos para generar una nube de palabras.")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Visualizaciones
                    if st.session_state.settings['show_trends']:
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        try:
                            trends_data = get_google_search_trends(query, pytrends)
                            if trends_data is not None and isinstance(trends_data, dict) and trends_data:
                                st.plotly_chart(create_trend_chart(trends_data, query))
                            else:
                                st.info("ℹ️ No hay datos de tendencias disponibles.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener tendencias: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if st.session_state.settings['show_geo']:
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        try:
                            pytrends_obj = get_trends_data_with_retry(query)
                            if pytrends_obj:
                                geo_data = pytrends_obj.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
                                if not geo_data.empty and query in geo_data.columns:
                                    geo_chart = create_geo_chart(geo_data, query)
                                    if geo_chart is not None:
                                        st.plotly_chart(geo_chart)
                                    else:
                                        st.info("ℹ️ No hay suficientes datos geográficos.")
                                else:
                                    st.info("ℹ️ No hay datos geográficos disponibles.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener datos geográficos: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if st.session_state.settings['show_topics']:
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        try:
                            pytrends_obj = get_trends_data_with_retry(query)
                            if pytrends_obj:
                                related_topics = pytrends_obj.related_topics()
                                if related_topics and query in related_topics:
                                    topic_data = related_topics[query].get('top', None)
                                    if topic_data is not None and not topic_data.empty:
                                        topics_chart = create_related_topics_chart({'top': topic_data}, query)
                                        if topics_chart is not None:
                                            st.plotly_chart(topics_chart)
                                        else:
                                            st.info("ℹ️ No hay suficientes temas relacionados.")
                                    else:
                                        st.info("ℹ️ No hay temas relacionados disponibles.")
                                else:
                                    st.info("ℹ️ No hay datos de temas relacionados.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener temas relacionados: {str(e)}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
            except Exception as e:
                logger.error(f"Error in search process: {str(e)}", exc_info=True)
                st.error(f"❌ Error general: {str(e)}")
    close_theme_div()

if __name__ == "__main__":
    main()