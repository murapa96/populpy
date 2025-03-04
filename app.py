#!/usr/bin/env python3
"""
Entry point for the PopulPy Streamlit application.
This file serves as the entry point that users should run with 'streamlit run app.py'
"""
import os
import sys
from dotenv import load_dotenv

# Make sure the current directory is in the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Import and run the main UI
from src.ui.streamlit_app import main

# This will be executed when Streamlit runs this file
if __name__ == "__main__":
    main()
