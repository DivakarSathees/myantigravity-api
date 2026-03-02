import os
import re
import json
import time
from typing import Dict, List, Optional


# =============================================================================
# FILE ANALYSIS CACHE
# =============================================================================
# Stores per-file analysis results with modification timestamps.
# On subsequent runs, only re-analyzes files that have changed.
# Tracks manual edits automatically via os.path.getmtime().

CACHE_FILENAME = ".file_analysis_cache.json"


class FileAnalysisCache:
    """
    Persistent cache for file analysis results.
    
    Stores analysis (classes, methods, test counts) per file alongside
    the file's last-modified timestamp. On the next run, skips files
    whose timestamp hasn't changed, dramatically speeding up description
    generation for large projects.
    
    Cache file: <workspace>/.file_analysis_cache.json
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.cache_path = os.path.join(workspace_path, CACHE_FILENAME)
        self.data: Dict = {}
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'new_files': 0,
            'deleted_files': 0,
            'unchanged_files': 0,
            'changed_files': 0,
        }
        self._load()
    
    def _load(self):
        """Load cache from disk if it exists."""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = {}
        else:
            self.data = {}
    
    def save(self):
        """Persist cache to disk."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save analysis cache: {e}")
    
    def get_relative_key(self, file_path: str) -> str:
        """Convert absolute path to workspace-relative key."""
        return os.path.relpath(file_path, self.workspace_path)
    
    def is_fresh(self, file_path: str) -> bool:
        """
        Check if cached analysis for a file is still valid.
        Compares the file's current mtime with the cached mtime.
        Returns False if file is new, modified, or not cached.
        """
        key = self.get_relative_key(file_path)
        if key not in self.data:
            return False
        
        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.data[key].get('last_modified', 0)
            return current_mtime == cached_mtime
        except OSError:
            return False
    
    def get(self, file_path: str) -> Optional[Dict]:
        """
        Get cached analysis for a file if it's still fresh.
        Returns None if cache miss (file new, modified, or not cached).
        """
        if self.is_fresh(file_path):
            self.stats['cache_hits'] += 1
            self.stats['unchanged_files'] += 1
            key = self.get_relative_key(file_path)
            return self.data[key].get('analysis')
        
        self.stats['cache_misses'] += 1
        key = self.get_relative_key(file_path)
        if key in self.data:
            self.stats['changed_files'] += 1
        else:
            self.stats['new_files'] += 1
        return None
    
    def put(self, file_path: str, analysis: Dict):
        """Store analysis result for a file with its current mtime."""
        key = self.get_relative_key(file_path)
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = time.time()
        
        self.data[key] = {
            'last_modified': mtime,
            'analysis': analysis,
            'analyzed_at': time.time()
        }
    
    def cleanup_deleted_files(self):
        """Remove cache entries for files that no longer exist."""
        keys_to_remove = []
        for key in self.data:
            full_path = os.path.join(self.workspace_path, key)
            if not os.path.exists(full_path):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.data[key]
            self.stats['deleted_files'] += 1
    
    def get_summary(self) -> str:
        """Return a human-readable summary of cache performance."""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        if total == 0:
            return "No files processed"
        
        hit_rate = (self.stats['cache_hits'] / total * 100) if total > 0 else 0
        parts = [f"Cache: {self.stats['cache_hits']}/{total} hits ({hit_rate:.0f}%)"]
        
        if self.stats['unchanged_files']:
            parts.append(f"{self.stats['unchanged_files']} unchanged (skipped)")
        if self.stats['changed_files']:
            parts.append(f"{self.stats['changed_files']} changed (re-analyzed)")
        if self.stats['new_files']:
            parts.append(f"{self.stats['new_files']} new (analyzed)")
        if self.stats['deleted_files']:
            parts.append(f"{self.stats['deleted_files']} deleted (cleaned)")
        
        return " | ".join(parts)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_project_description(
    workspace_path: str,
    reference_description_path: Optional[str] = None,
    output_filename: str = "PROJECT_DESCRIPTION.md"
) -> Dict:
    """
    Generates a comprehensive scenario-based project description by analyzing
    solution code and test cases, using a reference description for format.
    
    Uses a file analysis cache to avoid re-reading unchanged files.
    
    Args:
        workspace_path: Path to the workspace root
        reference_description_path: Optional path to reference description file (e.g., DemoDescription.md)
        output_filename: Name of the output description file
    
    Returns:
        dict with:
        - success: bool
        - output_path: str (path to generated description)
        - solution_files: list of analyzed solution files
        - test_files: list of analyzed test files
        - classes_documented: int
        - methods_documented: int
        - tests_documented: int
        - cache_summary: str (cache hit/miss statistics)
        - errors: list of any errors encountered
    """
    result = {
        'success': False,
        'output_path': '',
        'solution_files': [],
        'test_files': [],
        'classes_documented': 0,
        'methods_documented': 0,
        'tests_documented': 0,
        'cache_summary': '',
        'errors': []
    }
    
    try:
        # Initialize cache
        cache = FileAnalysisCache(workspace_path)
        cache.cleanup_deleted_files()
        
        # Step 1: Identify project structure
        project_info = identify_project_structure(workspace_path)
        
        # Step 2: Read reference description for format (if provided)
        reference_format = None
        if reference_description_path and os.path.exists(reference_description_path):
            reference_format = analyze_reference_format(reference_description_path)
        
        # Step 3: Analyze solution files (with cache)
        solution_analysis = analyze_solution_files(
            workspace_path,
            project_info['solution_dirs'],
            cache
        )
        result['solution_files'] = solution_analysis['files']
        result['classes_documented'] = solution_analysis['class_count']
        result['methods_documented'] = solution_analysis['method_count']
        
        # Step 4: Analyze test files (with cache)
        test_analysis = analyze_test_files(
            workspace_path,
            project_info['test_dirs'],
            cache
        )
        result['test_files'] = test_analysis['files']
        result['tests_documented'] = test_analysis['test_count']
        
        # Step 5: Generate description content
        description_content = build_description_content(
            project_info,
            solution_analysis,
            test_analysis,
            reference_format
        )
        
        # Step 6: Write to file
        output_path = os.path.join(workspace_path, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description_content)
        
        # Step 7: Save cache for next run
        cache.save()
        
        result['success'] = True
        result['output_path'] = output_path
        result['cache_summary'] = cache.get_summary()
        
    except Exception as e:
        result['errors'].append(str(e))
    
    return result


# =============================================================================
# PROJECT STRUCTURE DETECTION
# =============================================================================

def identify_project_structure(workspace_path: str) -> Dict:
    """Identify solution and test directories in the workspace"""
    structure = {
        'project_type': 'unknown',
        'solution_dirs': [],
        'test_dirs': [],
        'config_files': []
    }
    
    # Common solution directory names
    solution_patterns = ['src', 'dotnetapp', 'lib', 'app', 'controllers', 'services', 'models']
    # Common test directory names
    test_patterns = ['test', 'tests', 'nunit', '__tests__', 'spec']
    
    for item in os.listdir(workspace_path):
        item_path = os.path.join(workspace_path, item)
        
        if os.path.isdir(item_path):
            item_lower = item.lower()
            if any(pattern in item_lower for pattern in solution_patterns):
                structure['solution_dirs'].append(item)
            elif any(pattern in item_lower for pattern in test_patterns):
                structure['test_dirs'].append(item)
        elif os.path.isfile(item_path):
            # Identify project type from config files
            if item.endswith('.csproj') or item.endswith('.sln'):
                structure['project_type'] = '.NET'
                structure['config_files'].append(item)
            elif item == 'package.json':
                structure['project_type'] = 'Node.js'
                structure['config_files'].append(item)
            elif item == 'requirements.txt' or item == 'setup.py':
                structure['project_type'] = 'Python'
                structure['config_files'].append(item)
            elif item == 'pom.xml' or item.endswith('.gradle'):
                structure['project_type'] = 'Java'
                structure['config_files'].append(item)
    
    return structure


# =============================================================================
# REFERENCE FORMAT ANALYSIS
# =============================================================================

def analyze_reference_format(reference_path: str) -> Dict:
    """Analyze reference description to extract format patterns"""
    with open(reference_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    format_info = {
        'has_problem_statement': '**Problem Statement:**' in content,
        'has_models_section': '**Models:**' in content,
        'has_controllers_section': '**Controllers:**' in content or 'Controller' in content,
        'has_endpoints_section': '**Endpoints:**' in content,
        'has_commands_section': '**Commands' in content,
        'uses_bold_headers': '**' in content,
        'uses_bullet_points': '*   ' in content or '- ' in content,
        'sections': extract_sections(content)
    }
    
    return format_info


def extract_sections(content: str) -> List[str]:
    """Extract section headers from reference description"""
    sections = []
    lines = content.split('\n')
    for line in lines:
        if line.startswith('**') and line.endswith('**'):
            sections.append(line.strip('*').strip(':'))
    return sections


# =============================================================================
# SOLUTION FILE ANALYSIS (CACHED)
# =============================================================================

def analyze_solution_files(workspace_path: str, solution_dirs: List[str], cache: FileAnalysisCache) -> Dict:
    """Analyze solution files to extract classes and methods. Uses cache."""
    analysis = {
        'files': [],
        'classes': [],
        'class_count': 0,
        'method_count': 0
    }
    
    for dir_name in solution_dirs:
        dir_path = os.path.join(workspace_path, dir_name)
        if not os.path.exists(dir_path):
            continue
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith(('.cs', '.py', '.js', '.ts', '.java')):
                    file_path = os.path.join(root, file)
                    try:
                        # Check cache first
                        cached = cache.get(file_path)
                        if cached is not None:
                            # Cache hit — use stored analysis
                            file_analysis = cached
                        else:
                            # Cache miss — read and analyze file
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            file_analysis = analyze_code_file(content, file)
                            # Store in cache for next run
                            cache.put(file_path, file_analysis)
                        
                        analysis['files'].append(file)
                        analysis['classes'].extend(file_analysis['classes'])
                        analysis['class_count'] += len(file_analysis['classes'])
                        analysis['method_count'] += file_analysis['method_count']
                    except Exception as e:
                        print(f"Error analyzing {file}: {e}")
    
    return analysis


# =============================================================================
# CODE FILE ANALYSIS (per language)
# =============================================================================

def analyze_code_file(content: str, filename: str) -> Dict:
    """Analyze a single code file to extract classes and methods"""
    analysis = {
        'classes': [],
        'method_count': 0
    }
    
    # Detect language
    if filename.endswith('.cs'):
        analysis = analyze_csharp_file(content)
    elif filename.endswith('.py'):
        analysis = analyze_python_file(content)
    elif filename.endswith(('.js', '.ts')):
        analysis = analyze_javascript_file(content)
    elif filename.endswith('.java'):
        analysis = analyze_java_file(content)
    
    return analysis


def analyze_csharp_file(content: str) -> Dict:
    """Analyze C# file for classes and methods"""
    analysis = {'classes': [], 'method_count': 0}
    
    # Find classes
    class_pattern = r'public\s+class\s+(\w+)'
    classes = re.findall(class_pattern, content)
    
    # Find methods
    method_pattern = r'public\s+(?:async\s+)?(?:Task<)?(\w+)>?\s+(\w+)\s*\([^)]*\)'
    methods = re.findall(method_pattern, content)
    
    for class_name in classes:
        analysis['classes'].append({
            'name': class_name,
            'type': 'class',
            'methods': []
        })
    
    analysis['method_count'] = len(methods)
    
    return analysis


def analyze_python_file(content: str) -> Dict:
    """Analyze Python file for classes and methods"""
    analysis = {'classes': [], 'method_count': 0}
    
    # Find classes
    class_pattern = r'class\s+(\w+)'
    classes = re.findall(class_pattern, content)
    
    # Find functions/methods
    method_pattern = r'def\s+(\w+)\s*\('
    methods = re.findall(method_pattern, content)
    
    for class_name in classes:
        analysis['classes'].append({
            'name': class_name,
            'type': 'class',
            'methods': []
        })
    
    analysis['method_count'] = len(methods)
    
    return analysis


def analyze_javascript_file(content: str) -> Dict:
    """Analyze JavaScript/TypeScript file for classes and methods"""
    analysis = {'classes': [], 'method_count': 0}
    
    # Find classes
    class_pattern = r'class\s+(\w+)'
    classes = re.findall(class_pattern, content)
    
    # Find functions
    method_pattern = r'(?:function\s+(\w+)|(\w+)\s*:\s*function|(\w+)\s*\([^)]*\)\s*=>)'
    methods = re.findall(method_pattern, content)
    
    for class_name in classes:
        analysis['classes'].append({
            'name': class_name,
            'type': 'class',
            'methods': []
        })
    
    analysis['method_count'] = len([m for m in methods if any(m)])
    
    return analysis


def analyze_java_file(content: str) -> Dict:
    """Analyze Java file for classes and methods"""
    analysis = {'classes': [], 'method_count': 0}
    
    # Find classes
    class_pattern = r'public\s+class\s+(\w+)'
    classes = re.findall(class_pattern, content)
    
    # Find methods
    method_pattern = r'public\s+(?:static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
    methods = re.findall(method_pattern, content)
    
    for class_name in classes:
        analysis['classes'].append({
            'name': class_name,
            'type': 'class',
            'methods': []
        })
    
    analysis['method_count'] = len(methods)
    
    return analysis


# =============================================================================
# TEST FILE ANALYSIS (CACHED)
# =============================================================================

def analyze_test_files(workspace_path: str, test_dirs: List[str], cache: FileAnalysisCache) -> Dict:
    """Analyze test files to extract test cases. Uses cache."""
    analysis = {
        'files': [],
        'tests': [],
        'test_count': 0
    }
    
    for dir_name in test_dirs:
        dir_path = os.path.join(workspace_path, dir_name)
        if not os.path.exists(dir_path):
            continue
        
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if 'test' in file.lower() or 'spec' in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        # Check cache first
                        cached = cache.get(file_path)
                        if cached is not None:
                            # Cache hit
                            test_count = cached.get('test_count', 0)
                        else:
                            # Cache miss — read and count
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            test_count = count_test_methods(content, file)
                            # Store in cache
                            cache.put(file_path, {'test_count': test_count})
                        
                        analysis['files'].append(file)
                        analysis['test_count'] += test_count
                    except Exception as e:
                        print(f"Error analyzing test file {file}: {e}")
    
    return analysis


def count_test_methods(content: str, filename: str) -> int:
    """Count test methods in a test file"""
    count = 0
    
    if filename.endswith('.cs'):
        # C# test methods with [Test] or [Fact] attribute
        count = len(re.findall(r'\[(?:Test|Fact)\]', content))
    elif filename.endswith('.py'):
        # Python test functions
        count = len(re.findall(r'def\s+test_\w+', content))
    elif filename.endswith(('.js', '.ts')):
        # JavaScript/TypeScript it() or test() blocks
        count = len(re.findall(r'(?:it|test)\s*\(', content))
    elif filename.endswith('.java'):
        # Java test methods with @Test
        count = len(re.findall(r'@Test', content))
    
    return count


# =============================================================================
# DESCRIPTION CONTENT BUILDER
# =============================================================================

def build_description_content(
    project_info: Dict,
    solution_analysis: Dict,
    test_analysis: Dict,
    reference_format: Optional[Dict]
) -> str:
    """Build the description content based on analysis"""
    
    content = []
    
    # Title
    content.append("# Project Description\n\n")
    
    # Overview
    content.append("## Overview\n\n")
    content.append(f"This is a {project_info['project_type']} project with {solution_analysis['class_count']} classes ")
    content.append(f"and {solution_analysis['method_count']} methods, covered by {test_analysis['test_count']} test cases.\n\n")
    
    # Solution Architecture
    content.append("## Solution Architecture\n\n")
    if solution_analysis['files']:
        content.append("**Solution Files:**\n\n")
        for file in solution_analysis['files']:
            content.append(f"- `{file}`\n")
        content.append("\n")
    
    # Classes
    if solution_analysis['classes']:
        content.append("**Classes:**\n\n")
        for cls in solution_analysis['classes']:
            content.append(f"- **{cls['name']}**: {cls['type']}\n")
        content.append("\n")
    
    # Test Coverage
    content.append("## Test Coverage\n\n")
    if test_analysis['files']:
        content.append(f"**Total Test Cases:** {test_analysis['test_count']}\n\n")
        content.append("**Test Files:**\n\n")
        for file in test_analysis['files']:
            content.append(f"- `{file}`\n")
        content.append("\n")
    
    # Commands (based on project type)
    content.append("## Commands\n\n")
    commands = get_commands_for_project_type(project_info['project_type'])
    for cmd in commands:
        content.append(f"```bash\n{cmd}\n```\n\n")
    
    return ''.join(content)


def get_commands_for_project_type(project_type: str) -> List[str]:
    """Get relevant commands based on project type"""
    commands_map = {
        '.NET': ['dotnet restore', 'dotnet build', 'dotnet test', 'dotnet run'],
        'Node.js': ['npm install', 'npm start', 'npm test', 'npm run build'],
        'Python': ['pip install -r requirements.txt', 'python app.py', 'pytest'],
        'Java': ['mvn compile', 'mvn test', 'mvn package']
    }
    return commands_map.get(project_type, [])
