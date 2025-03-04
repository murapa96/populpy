#!/usr/bin/env python3
"""
PopulPy - Entry point for Streamlit application

This file serves as the main entry point to run the Streamlit application.
It ensures that Python can correctly import modules from the project.
"""
import os
import sys
import subprocess

def main():
    """
    Run the Streamlit application with the correct Python path configuration
    """
    # Get absolute path to the project root directory
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # Get path to the actual Streamlit app
    streamlit_app_path = os.path.join(project_root, "src", "ui", "streamlit_app.py")
    
    # Set PYTHONPATH environment variable to include the project root
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    
    # Run the Streamlit app with proper environment
    subprocess.run(["streamlit", "run", streamlit_app_path], env=env)

if __name__ == "__main__":
    main()
