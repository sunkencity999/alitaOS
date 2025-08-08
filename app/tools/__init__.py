"""Tools package for Streamlit version of AlitaOS.

This package intentionally avoids side-effect imports to prevent circular
dependency issues and mismatches with legacy Chainlit handlers.
Import the specific functions directly from their modules, e.g.:

    from tools.stock import get_stock_price
    from tools.image import generate_image
    from tools.search import search_information
    from tools.chart import create_chart
    from tools.python_file import create_python_file, execute_python_code
"""

__all__ = []
