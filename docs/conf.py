import os
import sys
sys.path.insert(0, os.path.abspath('..'))  # This assumes WrenchCL is in the parent directory of docs

# -- Project information -----------------------------------------------------
project = 'WrenchCL'
copyright = '2024, Willem van der Schans'
author = 'Willem van der Schans'
release = '0.0.1.dev0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
