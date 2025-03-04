import streamlit as st
from pytrends.request import TrendReq
from src.services.search_providers import (
    GoogleSearchProvider,
    DuckDuckGoProvider,
    BingSearchProvider
)
from src.services.analytics import (
    create_trend_chart,
    create_geo_chart,
    create_related_topics_chart
)
from src.services.google_service import (
    get_google_related_searches,
    get_top_results_for_related_searches,
    create_wordcloud,
    get_google_search_trends  # Add this import
)
from src.models import SearchManager
import os
from dotenv import load_dotenv
import tempfile
import pandas as pd
from urllib3.util import Retry
import json

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

@dataclass
class SearchResult:
    id: str
    query: str
    timestamp: datetime
    country: str
    settings: Dict[str, Any]
    results: Dict[str, Any]

    def sanitize(self):
        """Remove sensitive information before storing"""
        sensitive_keys = [
            'google_search_api_key',
            'custom_search_engine_id',
            'bing_api_key'
        ]
        sanitized = self.__dict__.copy()
        sanitized['settings'] = {
            k: v for k, v in sanitized['settings'].items() 
            if k not in sensitive_keys
        }
        return sanitized

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_cached_recent_searches(search_manager, limit: int = 10) -> List[SearchResult]:
    return search_manager.get_recent_searches(limit)

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_cached_search(search_manager, search_id: str) -> Optional[SearchResult]:
    return search_manager.get_search(search_id)

class SearchManager:
    def __init__(self):
        self.searches: List[SearchResult] = []
        self.current_search: Optional[SearchResult] = None

    def add_search(self, query: str, settings: Dict[str, Any], country: str) -> str:
        # Remove sensitive information from settings before storing
        filtered_settings = {
            k: v for k, v in settings.items() 
            if k not in ['google_search_api_key', 'custom_search_engine_id', 'bing_api_key']
        }
        
        search_id = str(uuid.uuid4())
        search = SearchResult(
            id=search_id,
            query=query,
            timestamp=datetime.now(),
            country=country,
            settings=filtered_settings,
            results={}
        )
        self.searches.append(search)
        self.current_search = search
        return search_id

    def update_search_results(self, search_id: str, results: Dict[str, Any]) -> None:
        for search in self.searches:
            if search.id == search_id:
                search.results.update(results)
                self.current_search = search
                break

    def get_recent_searches(self, limit: int = 10) -> List[SearchResult]:
        return sorted(self.searches, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_search(self, search_id: str) -> Optional[SearchResult]:
        return next((s for s in self.searches if s.id == search_id), None)

    def delete_search(self, search_id: str) -> None:
        self.searches = [s for s in self.searches if s.id != search_id]
        if self.current_search and self.current_search.id == search_id:
            self.current_search = None

    @st.cache_resource
    def _initialize_providers(self, settings):
        """Initialize search providers with caching"""
        providers = {}
        if 'Google' in settings['search_providers']:
            providers['Google'] = GoogleSearchProvider(
                settings['google_search_api_key'],
                settings['custom_search_engine_id']
            )
        if 'DuckDuckGo' in settings['search_providers']:
            providers['DuckDuckGo'] = DuckDuckGoProvider()
        if 'Bing' in settings['search_providers']:
            providers['Bing'] = BingSearchProvider(settings['bing_api_key'])
        return providers

    @st.cache_data(ttl=300)
    def search_with_provider(self, provider, query: str) -> List[Dict]:
        """Cached search execution"""
        return provider.search(query)

def init_session_state():
    if 'settings' not in st.session_state:
        st.session_state.settings = {
            'google_search_api_key': os.getenv('google_search_api_key', ''),
            'custom_search_engine_id': os.getenv('custom_search_engine_id', ''),
            'country': 'ES',
            'timeframe': 'today 5-y',
            'max_results': 5,
            'theme': 'light',  # Cambiado a minúsculas
            'search_providers': ['Google', 'DuckDuckGo', 'Bing'],
            'bing_api_key': os.getenv('bing_api_key', ''),
            'show_trends': True,
            'show_geo': True,
            'show_topics': True
        }
    if 'search_manager' not in st.session_state:
        st.session_state.search_manager = SearchManager()
    if 'theme_changed' not in st.session_state:
        st.session_state.theme_changed = False

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
    recent_searches = get_cached_recent_searches(st.session_state.search_manager)
    
    for search in recent_searches:
        with st.sidebar.expander(f"🔍 {search.query}", expanded=False):
            st.write(f"🌍 País: {search.country}")
            st.write(f"⏰ Fecha: {search.timestamp.strftime('%Y-%m-%d %H:%M')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Cargar", key=f"load_{search.id}"):
                    return search
            with col2:
                if st.button("🗑️ Eliminar", key=f"delete_{search.id}"):
                    st.session_state.search_manager.delete_search(search.id)
                    st.experimental_rerun()
    return None

def show_theme_button():
    col1, col2 = st.columns([10, 1])
    with col1:
        st.title("📊 PopulPy - Análisis de Tendencias de Google")
    with col2:
        theme_icon = "🌞" if st.session_state.settings.get('theme', 'light') == 'light' else "🌜"
        if st.button(theme_icon):
            # Cambiar el tema
            new_theme = 'dark' if st.session_state.settings['theme'] == 'light' else 'light'
            st.session_state.settings['theme'] = new_theme
            
            # Actualizar el archivo config.toml
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.streamlit', 'config.toml')
            with open(config_path, 'w') as f:
                f.write(f'[theme]\nbase = "{new_theme}"')
            
            st.experimental_rerun()

class AppState:
    def __init__(self):
        if 'initialized' not in st.session_state:
            self.initialize_state()

    def initialize_state(self):
        st.session_state.update({
            'initialized': True,
            'settings': self.get_default_settings(),
            'search_manager': SearchManager(),
            'current_query': '',
            'search_results': {},
            'trends_data': None,
            'geo_data': None,
            'topics_data': None,
            'error': None
        })

    @staticmethod
    def get_default_settings():
        return {
            'google_search_api_key': os.getenv('google_search_api_key', ''),
            'custom_search_engine_id': os.getenv('custom_search_engine_id', ''),
            'country': 'ES',
            'timeframe': 'today 5-y',
            'max_results': 5,
            'theme': 'light',
            'search_providers': ['Google', 'DuckDuckGo', 'Bing'],
            'bing_api_key': os.getenv('bing_api_key', ''),
            'show_trends': True,
            'show_geo': True,
            'show_topics': True
        }

    @staticmethod
    def reset():
        st.session_state.clear()
        st.experimental_rerun()

    @st.cache_resource
    def _initialize_pytrends(self, country: str) -> TrendReq:
        """Initialize PyTrends with caching"""
        return TrendReq(
            hl=country,
            timeout=(10,25),
            requests_args={
                'verify': True,
                'timeout': 30,
                'retry': Retry(
                    total=2,
                    backoff_factor=0.5,
                    allowed_methods=frozenset(['GET', 'POST'])
                )
            }
        )

def main():
    st.set_page_config(
        page_title="PopulPy - Análisis de Tendencias",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize app state
    app_state = AppState()

    # Mostrar historial en sidebar
    loaded_search = show_history()

    # Mostrar botón de cambio de tema y título
    show_theme_button()

    # Mostrar configuraciones encima del contenido principal
    show_search_engine_settings()
    show_api_settings()

    # Input para la búsqueda
    initial_query = loaded_search.query if loaded_search else ""
    query = st.text_input("🔍 Introduce un término de búsqueda:", value=initial_query)
    
    # Cargar configuración de búsqueda guardada
    if loaded_search:
        st.session_state.settings.update(loaded_search.settings)
        query = loaded_search.query

    @st.cache_data(ttl=300)
    def fetch_search_results(query: str, providers: Dict, settings: Dict) -> Dict[str, List]:
        results = {}
        for provider_name, provider in providers.items():
            try:
                results[provider_name] = provider.search(query)
            except Exception as e:
                st.warning(f"⚠️ Error en búsqueda de {provider_name}: {str(e)}")
                results[provider_name] = []
        return results

    @st.cache_data(ttl=300)
    def fetch_trends_data(pytrends, query: str) -> Optional[pd.DataFrame]:
        try:
            pytrends.build_payload([query])
            return pytrends.interest_over_time()
        except Exception:
            return None

    if query:
        if not st.session_state.settings['google_search_api_key'] or not st.session_state.settings['custom_search_engine_id']:
            st.error("⚠️ Por favor, configura las APIs de Google en el menú 'Configuración de APIs'")
            return
        
        try:
            # Initialize providers once
            providers = st.session_state.search_manager._initialize_providers(st.session_state.settings)
            
            # Initialize PyTrends once
            pytrends = app_state._initialize_pytrends(st.session_state.settings['country'])
            
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Trends: {str(e)}")
            return
                
        with st.spinner('🔄 Buscando información...'):
            try:
                # Create new search entry and get ID
                search_id = st.session_state.search_manager.add_search(
                    query=query,
                    settings=st.session_state.settings.copy(),
                    country=st.session_state.settings['country']
                ) if not loaded_search else loaded_search.get('id')

                # Initialize results storage
                search_data = {
                    'search_results': {},
                    'trends_data': None,
                    'geo_data': None,
                    'topics_data': None
                }

                # Fetch results in parallel using cached functions
                search_results = fetch_search_results(query, providers, st.session_state.settings)
                trends_data = fetch_trends_data(pytrends, query) if st.session_state.settings['show_trends'] else None

                search_data['search_results'] = search_results

                # Mostrar resultados y estadísticas con manejo de errores
                if not any(search_results.values()):
                    st.warning("⚠️ No se encontraron resultados de búsqueda.")
                    return

                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.header("🔍 Resultados de búsqueda")
                    for provider, results in search_results.items():
                        with st.expander(f"Resultados de {provider}", expanded=True):
                            for result in results:
                                st.markdown(f"• [{result['title']}]({result['link']})")

                with col2:
                    # Generar y mostrar nube de palabras
                    st.header("☁️ Nube de palabras")
                    with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                        create_wordcloud(
                            [result['title'] for provider_results in search_results.values() for result in provider_results],
                            tmp.name,
                            background_color='white',
                            colormap='viridis'
                        )
                        st.image(tmp.name)

                    # Updated visualization handling
                    if st.session_state.settings['show_trends']:
                        try:
                            if isinstance(trends_data, pd.DataFrame) and not trends_data.empty:
                                search_data['trends_data'] = trends_data.to_dict()
                                st.plotly_chart(create_trend_chart(trends_data, query))
                            else:
                                st.info("ℹ️ No hay datos de tendencias disponibles.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener tendencias: {str(e)}")
                    
                    if st.session_state.settings['show_geo']:
                        try:
                            geo_data = pytrends.interest_by_region()
                            if isinstance(geo_data, pd.DataFrame) and not geo_data.empty:
                                search_data['geo_data'] = geo_data.to_dict()
                                geo_chart = create_geo_chart(geo_data, query)
                                if geo_chart:
                                    st.plotly_chart(geo_chart)
                            else:
                                st.info("ℹ️ No hay datos geográficos disponibles.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener datos geográficos: {str(e)}")
                    
                    if st.session_state.settings['show_topics']:
                        try:
                            related_topics = pytrends.related_topics()
                            if related_topics and query in related_topics:
                                search_data['topics_data'] = related_topics[query]
                                topics_chart = create_related_topics_chart(related_topics[query], query)
                                if topics_chart:
                                    st.plotly_chart(topics_chart)
                            else:
                                st.info("ℹ️ No hay temas relacionados disponibles.")
                        except Exception as e:
                            st.warning(f"⚠️ Error al obtener temas relacionados: {str(e)}")

                # Update search results in history
                st.session_state.search_manager.update_search_results(search_id, search_data)

            except Exception as e:
                st.error(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()