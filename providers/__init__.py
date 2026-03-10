# providers/__init__.py
# Central registry mapping provider names to their classes.
# The Streamlit selectbox is populated from PROVIDERS.keys().
# To add a new provider: create the module, then add it here.

from .zelt import ZeltProvider
from .capium import CapiumProvider

PROVIDERS = {
    "Capium": CapiumProvider,
    "Zelt": ZeltProvider,
}
