from app import app
import pytest

def test_app_layout():
    """Test if app layout exists and has correct structure"""
    assert app.layout is not None
    assert len(app.layout.children) == 2  # sidebar and content

def test_sidebar_components():
    """Test if sidebar contains all required components"""
    sidebar = app.layout.children[0]
    components = [comp for comp in sidebar.children if hasattr(comp, 'id')]
    assert any(comp.id == 'date-picker' for comp in components)
    assert any(comp.id == 'group-dropdown' for comp in components)
    assert any(comp.id == 'status-checklist' for comp in components)

def test_content_components():
    """Test if main content contains all required components"""
    content = app.layout.children[1]
    assert 'Dashboard de Demandas' in str(content.children)
