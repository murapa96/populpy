"""
Analytics services for data visualization and trend analysis
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional

def create_trend_chart(trends_data: Dict[str, Any], query: str) -> go.Figure:
    """
    Create a line chart for search trends
    
    Args:
        trends_data: Dictionary with dates and values keys
        query: The search query
    
    Returns:
        Plotly figure object with the trend chart
    """
    if not trends_data or 'dates' not in trends_data or 'values' not in trends_data:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trends_data['dates'],
            y=trends_data['values'],
            mode='lines',
            name=query,
            line=dict(color='#1e88e5')
        )
    )
    
    fig.update_layout(
        title=f'Tendencias de búsqueda para "{query}"',
        xaxis_title='Fecha',
        yaxis_title='Interés relativo',
        hovermode='x',
        template='plotly_white'
    )
    
    return fig

def create_geo_chart(geo_data: pd.DataFrame, query: str) -> Optional[go.Figure]:
    """
    Create a geographical chart showing interest by region
    
    Args:
        geo_data: DataFrame with geographic data
        query: The search query
    
    Returns:
        Plotly figure object with the geographic chart, or None if data is invalid
    """
    if geo_data is None or geo_data.empty or query not in geo_data.columns:
        return None
    
    # Remove rows with zero values to focus on regions with data
    filtered_data = geo_data[geo_data[query] > 0]
    
    if filtered_data.empty:
        return None
    
    fig = px.choropleth(
        filtered_data,
        locations=filtered_data.index,
        locationmode='country names',
        color=query,
        title=f"Distribución geográfica del interés para '{query}'",
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
        ),
        template='plotly_white'
    )
    
    return fig

def create_related_topics_chart(topics_data: Dict[str, pd.DataFrame], query: str) -> Optional[go.Figure]:
    """
    Create a bar chart showing related topics
    
    Args:
        topics_data: Dictionary with top and rising DataFrames
        query: The search query
    
    Returns:
        Plotly figure object with the related topics chart, or None if data is invalid
    """
    if not topics_data or 'top' not in topics_data or topics_data['top'] is None:
        return None
    
    top_topics = topics_data['top']
    
    if top_topics.empty:
        return None
    
    # Select the top 10 topics
    top_10 = top_topics.head(10)
    
    try:
        fig = px.bar(
            top_10,
            x='topic_title',
            y='value',
            title=f"Temas relacionados más populares para '{query}'",
            color='value',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        fig.update_layout(
            xaxis_title="Tema",
            yaxis_title="Relevancia",
            xaxis={'categoryorder':'total descending'},
            template='plotly_white'
        )
        
        # Rotate x-axis labels if there are many
        if len(top_10) > 5:
            fig.update_layout(
                xaxis_tickangle=-45
            )
        
        return fig
    except Exception:
        return None
