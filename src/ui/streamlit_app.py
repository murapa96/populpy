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
    create_wordcloud
)
from src.models import SearchManager
import os
from dotenv import load_dotenv
import tempfile

def init_session_state():
    if 'settings' not in st.session_state:
        st.session_state.settings = {
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
    if 'search_manager' not in st.session_state:
        st.session_state.search_manager = SearchManager()

def show_settings():
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # APIs
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

        # Opciones de búsqueda
        st.subheader("Opciones de búsqueda")
        st.session_state.settings['country'] = st.selectbox(
            "País",
            options=['ES', 'US', 'MX', 'AR', 'CO', 'PE', 'CL'],
            index=0
        )
        st.session_state.settings['timeframe'] = st.select_slider(
            "Periodo de tiempo",
            options=['today 1-m', 'today 3-m', 'today 12-m', 'today 5-y'],
            value='today 5-y'
        )
        st.session_state.settings['max_results'] = st.slider(
            "Número máximo de resultados",
            min_value=1,
            max_value=10,
            value=5
        )

        # Proveedores de búsqueda
        st.subheader("Proveedores de búsqueda")
        st.session_state.settings['search_providers'] = st.multiselect(
            "Selecciona los proveedores",
            options=['Google', 'DuckDuckGo', 'Bing'],
            default=['Google']
        )
        
        if 'Bing' in st.session_state.settings['search_providers']:
            st.text_input(
                "API Key de Bing",
                value=st.session_state.settings['bing_api_key'],
                type="password",
                key="bing_api_key"
            )

        # Opciones visuales
        st.subheader("Visualización")
        st.session_state.settings['theme'] = st.radio(
            "Tema",
            options=['light', 'dark'],
            horizontal=True
        )

        # Visualizaciones
        st.subheader("Visualizaciones")
        st.session_state.settings['show_trends'] = st.checkbox("Mostrar tendencias temporales", value=True)
        st.session_state.settings['show_geo'] = st.checkbox("Mostrar distribución geográfica", value=True)
        st.session_state.settings['show_topics'] = st.checkbox("Mostrar temas relacionados", value=True)

        # Botón para restaurar valores por defecto
        if st.button("Restaurar valores por defecto"):
            init_session_state()

def show_history():
    st.sidebar.header("📚 Historial de búsquedas")
    recent_searches = st.session_state.search_manager.get_recent_searches()
    
    for search in recent_searches:
        with st.sidebar.expander(f"🔍 {search.query}", expanded=False):
            st.write(f"🌍 País: {search.country}")
            st.write(f"⏰ Fecha: {search.timestamp.strftime('%Y-%m-%d %H:%M')}")
            if st.button("🔄 Cargar", key=f"load_{search.id}"):
                return search
            if st.button("🗑️ Eliminar", key=f"delete_{search.id}"):
                st.session_state.search_manager.delete_search(search.id)
                st.experimental_rerun()
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
    
    # Mostrar configuración en sidebar
    show_settings()
    
    # Mostrar historial en sidebar
    loaded_search = show_history()

    # Contenido principal
    st.title("📊 PopulPy - Análisis de Tendencias de Google")
    
    # Input para la búsqueda
    query = st.text_input("🔍 Introduce un término de búsqueda:")
    
    if loaded_search:
        query = loaded_search.query
        st.session_state.settings = loaded_search.settings

    if query:
        if not st.session_state.settings['google_search_api_key'] or not st.session_state.settings['custom_search_engine_id']:
            st.error("⚠️ Por favor, configura las APIs de Google en el menú lateral")
            return
            
        pytrends = TrendReq(hl=st.session_state.settings['country'])
        
        with st.spinner('🔄 Buscando información...'):
            try:
                # Configurar proveedores de búsqueda
                search_results = {}
                if 'Google' in st.session_state.settings['search_providers']:
                    google_provider = GoogleSearchProvider(
                        st.session_state.settings['google_search_api_key'],
                        st.session_state.settings['custom_search_engine_id']
                    )
                    search_results['Google'] = google_provider.search(query)
                
                if 'DuckDuckGo' in st.session_state.settings['search_providers']:
                    ddg_provider = DuckDuckGoProvider()
                    search_results['DuckDuckGo'] = ddg_provider.search(query)
                
                if 'Bing' in st.session_state.settings['search_providers']:
                    bing_provider = BingSearchProvider(st.session_state.settings['bing_api_key'])
                    search_results['Bing'] = bing_provider.search(query)

                # Mostrar resultados y estadísticas
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.header("🔍 Resultados de búsqueda")
                    for provider, results in search_results.items():
                        with st.expander(f"{provider} Results", expanded=True):
                            for result in results:
                                st.write(f"• [{result['title']}]({result['link']})")

                with col2:
                    # Generar y mostrar nube de palabras
                    st.header("☁️ Nube de palabras")
                    with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                        bg_color = 'white' if st.session_state.settings['theme'] == 'light' else 'black'
                        text_color = 'black' if st.session_state.settings['theme'] == 'light' else 'white'
                        create_wordcloud(
                            list(search_results.keys()),
                            tmp.name,
                            background_color=bg_color,
                            colormap='viridis'
                        )
                        st.image(tmp.name)

                    # Nuevas visualizaciones
                    if st.session_state.settings['show_trends']:
                        trends_data = get_google_search_trends(query, pytrends)
                        st.plotly_chart(create_trend_chart(trends_data, query))
                    
                    if st.session_state.settings['show_geo']:
                        st.plotly_chart(create_geo_chart(pytrends, query))
                    
                    if st.session_state.settings['show_topics']:
                        topics_chart = create_related_topics_chart(pytrends, query)
                        if topics_chart:
                            st.plotly_chart(topics_chart)
                        
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
