import sys
from unittest.mock import MagicMock

try:
    import strands
except ImportError:
    strands = MagicMock()
    strands.tool = lambda f: f
    
    class FakeAgent:
        def __init__(self, *args, **kwargs):
            pass
            
    strands.Agent = FakeAgent
    sys.modules["strands"] = strands
    
    models = MagicMock()
    gemini = MagicMock()
    models.gemini = gemini
    sys.modules["strands.models"] = models
    sys.modules["strands.models.gemini"] = gemini
