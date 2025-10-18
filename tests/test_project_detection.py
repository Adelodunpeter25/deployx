import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.project import detect_project, get_project_summary

class TestProjectDetection(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_detect_react_project(self):
        """Test detection of React project"""
        # Create package.json with React
        package_json = {
            "name": "test-app",
            "dependencies": {"react": "^18.0.0"},
            "scripts": {"build": "react-scripts build"}
        }
        
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'react')
        self.assertEqual(summary['framework'], 'react')
        self.assertEqual(summary['build_command'], 'npm run build')
        self.assertEqual(summary['output_dir'], 'build')
        self.assertIn('package.json', summary['detected_files'])
    
    def test_detect_vue_project(self):
        """Test detection of Vue project"""
        package_json = {
            "name": "vue-app",
            "dependencies": {"vue": "^3.0.0"},
            "scripts": {"build": "vue-cli-service build"}
        }
        
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'vue')
        self.assertEqual(summary['framework'], 'vue')
        self.assertEqual(summary['output_dir'], 'dist')
    
    def test_detect_nextjs_project(self):
        """Test detection of Next.js project"""
        package_json = {
            "name": "nextjs-app",
            "dependencies": {"next": "^13.0.0", "react": "^18.0.0"},
            "scripts": {"build": "next build"}
        }
        
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'nextjs')
        self.assertEqual(summary['framework'], 'nextjs')
        self.assertEqual(summary['output_dir'], 'out')
    
    def test_detect_vite_react_project(self):
        """Test detection of Vite + React project"""
        package_json = {
            "name": "vite-react-app",
            "dependencies": {"react": "^18.0.0"},
            "devDependencies": {"vite": "^4.0.0"}
        }
        
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        # Create vite config
        (self.project_path / "vite.config.js").write_text("export default {}")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'react')
        self.assertEqual(summary['framework'], 'react-vite')
        self.assertEqual(summary['output_dir'], 'dist')
        self.assertIn('vite.config.js', summary['detected_files'])
    
    def test_detect_python_django_project(self):
        """Test detection of Django project"""
        # Create requirements.txt with Django
        (self.project_path / "requirements.txt").write_text("Django==4.2.0\npsycopg2==2.9.0")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'django')
        self.assertEqual(summary['framework'], 'django')
        self.assertEqual(summary['package_manager'], 'pip')
        self.assertIn('requirements.txt', summary['detected_files'])
    
    def test_detect_python_flask_project(self):
        """Test detection of Flask project"""
        (self.project_path / "requirements.txt").write_text("Flask==2.3.0\nGunicorn==20.1.0")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'flask')
        self.assertEqual(summary['framework'], 'flask')
    
    def test_detect_python_uv_project(self):
        """Test detection of Python project with uv"""
        # Create pyproject.toml
        (self.project_path / "pyproject.toml").write_text("""
[project]
name = "test-app"
dependencies = ["fastapi==0.100.0"]
""")
        
        # Create uv.lock
        (self.project_path / "uv.lock").write_text("# uv lock file")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'fastapi')
        self.assertEqual(summary['package_manager'], 'uv')
        self.assertIn('pyproject.toml', summary['detected_files'])
    
    def test_detect_static_html_project(self):
        """Test detection of static HTML project"""
        (self.project_path / "index.html").write_text("<html><body>Hello</body></html>")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'static')
        self.assertEqual(summary['output_dir'], '.')
        self.assertIn('index.html', summary['detected_files'])
    
    def test_detect_static_public_folder(self):
        """Test detection of static project with public folder"""
        public_dir = self.project_path / "public"
        public_dir.mkdir()
        (public_dir / "index.html").write_text("<html><body>Hello</body></html>")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'static')
        self.assertEqual(summary['output_dir'], 'public')
    
    def test_detect_unknown_project(self):
        """Test detection of unknown project type"""
        # Create empty directory
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        self.assertEqual(summary['type'], 'unknown')
        self.assertIsNone(summary['framework'])
    
    def test_package_manager_detection(self):
        """Test package manager detection"""
        # Test yarn
        package_json = {"name": "test", "dependencies": {"react": "^18.0.0"}}
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        (self.project_path / "yarn.lock").write_text("# yarn lock")
        
        info = detect_project(str(self.project_path))
        self.assertEqual(info.package_manager, 'yarn')
        
        # Test pnpm
        (self.project_path / "yarn.lock").unlink()
        (self.project_path / "pnpm-lock.yaml").write_text("# pnpm lock")
        
        info = detect_project(str(self.project_path))
        self.assertEqual(info.package_manager, 'pnpm')
    
    def test_invalid_package_json(self):
        """Test handling of invalid package.json"""
        (self.project_path / "package.json").write_text("invalid json {")
        
        info = detect_project(str(self.project_path))
        summary = get_project_summary(info)
        
        # Should fallback gracefully
        self.assertEqual(summary['type'], 'nodejs')

if __name__ == '__main__':
    unittest.main()