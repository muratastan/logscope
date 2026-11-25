from pathlib import Path
from scripts.check_structure import ROOT

def test_project_files():
    files=['.vscode/tasks.json','frontend/src/App.jsx','backend/fullstack.py','django_demo/templates/home.html','docker-compose.yml']
    assert all((ROOT/f).is_file() for f in files)

def test_readme_and_plan():
    assert (ROOT/'docs/HAFTA_HAFTA_YOL_HARITASI.md').exists()
    assert (ROOT/'.env.example').exists()
    assert '.env' in (ROOT/'.gitignore').read_text(encoding='utf-8')
