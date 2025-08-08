"""Plotly chart utilities for Streamlit.

Provides `create_chart(message, plotly_json_fig)` for compatibility or a
more direct `make_scatter(x, y, title)` helper. No Chainlit dependency.
"""

import plotly
import plotly.graph_objects as go
from utils.common import logger

def create_chart(message: str, plotly_json_fig: str):
    """Parse a Plotly figure from JSON and return it.

    Returns dict: {"success": bool, "figure": plotly.graph_objs.Figure|None, "error": str|None}
    """
    try:
        logger.info(f"🎨 Creating Plotly chart with message: {message}")
        fig = plotly.io.from_json(plotly_json_fig)
        return {"success": True, "figure": fig}
    except Exception as e:
        logger.error(f"❌ Error creating Plotly chart: {str(e)}")
        return {"success": False, "figure": None, "error": str(e)}


def make_scatter(x, y, title: str = "Scatter"):
    """Helper to create a simple scatter chart."""
    try:
        fig = go.Figure(data=go.Scatter(x=x, y=y, mode="markers"))
        fig.update_layout(title=title)
        return {"success": True, "figure": fig}
    except Exception as e:
        logger.error(f"❌ Error creating scatter chart: {str(e)}")
        return {"success": False, "figure": None, "error": str(e)}
