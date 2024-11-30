import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict

def create_trend_chart(trends_data: pd.DataFrame, query: str) -> go.Figure:
    fig = px.line(trends_data, x=trends_data.index, y=query)
    fig.update_layout(
        title="Tendencia temporal",
        xaxis_title="Fecha",
        yaxis_title="Interés relativo"
    )
    return fig

def create_geo_chart(pytrends, query: str) -> go.Figure:
    pytrends.build_payload([query])
    geo_data = pytrends.interest_by_region()
    fig = px.choropleth(
        geo_data,
        locations=geo_data.index,
        locationmode='country names',
        color=query,
        title="Distribución geográfica del interés"
    )
    return fig

def create_related_topics_chart(pytrends, query: str) -> go.Figure:
    pytrends.build_payload([query])
    related_topics = pytrends.related_topics()[query]['top']
    if related_topics is not None and not related_topics.empty:
        fig = px.bar(
            related_topics.head(10),
            x='topic_title',
            y='value',
            title="Temas relacionados más populares"
        )
        fig.update_layout(xaxis_title="Tema", yaxis_title="Relevancia")
        return fig
    return None
