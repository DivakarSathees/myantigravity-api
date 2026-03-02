import os
import re
from typing import Dict, List, Optional
from pathlib import Path


def analyze_test_patterns(test_directory: str, max_files: int = 5) -> dict:
    """
    Analyzes test files in a directory to extract common patterns.
    
    Args:
        test_directory: Path to test directory
        max_files: Maximum number of test files to analyze
    
    Returns:
        dict with:
        - framework: Detected testing framework
        - naming_pattern: File naming convention
        - file_structure: Class/function organization
        - import_patterns: Common import statements
        - assertion_style: Assertion methods used
        - setup_teardown: Setup/teardown patterns
        - example_files: List of analyzed files
        - confidence: Confidence score (0-1)
    """
    if not os.path.exists(test_directory):
        return {
            'framework': 'unknown',
            'naming_pattern': 'unknown',
            'file_structure': 'unknown',
            'import_patterns': [],
            'assertion_style': 'unknown',
            'setup_teardown': 'unknown',
            'example_files': [],
            'confidence': 0.0
        }
    
    # Find test files
    test_files = []
    for root, dirs, files in os.walk(test_directory):
        for file in files:
            if is_test_file(file):
                test_files.append(os.path.join(root, file))
                if len(test_files) >= max_files:
                    break
        if len(test_files) >= max_files:
            break
    
    if not test_files:
        return {
            'framework': 'unknown',
            'naming_pattern': 'no test files found',
            'file_structure': 'unknown',
            'import_patterns': [],
            'assertion_style': 'unknown',
            'setup_teardown': 'unknown',
            'example_files': [],
            'confidence': 0.0
        }
    
    # Analyze files
    frameworks = []
    imports = []
    assertions = []
    setups = []
    structures = []
    
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect framework
            framework = detect_test_framework(content)
            if framework != 'unknown':
                frameworks.append(framework)
            
            # Extract imports
            file_imports = extract_imports(content)
            imports.extend(file_imports)
            
            # Detect assertions
            file_assertions = detect_assertions(content)
            assertions.extend(file_assertions)
            
            # Detect setup/teardown
            file_setup = detect_setup_teardown(content)
            if file_setup:
                setups.append(file_setup)
            
            # Analyze structure
            structure = analyze_file_structure(content, get_language_from_file(test_file))
            structures.append(structure)
            
        except Exception as e:
            print(f"Error analyzing {test_file}: {e}")
            continue
    
    # Aggregate results
    framework = most_common(frameworks) if frameworks else 'unknown'
    naming_pattern = extract_naming_pattern([os.path.basename(f) for f in test_files])
    import_patterns = most_common_items(imports, top_n=10)
    assertion_style = most_common(assertions) if assertions else 'unknown'
    setup_teardown = most_common(setups) if setups else 'none detected'
    file_structure = aggregate_structures(structures)
    
    # Calculate confidence
    confidence = calculate_confidence(frameworks, assertions, setups)
    
    return {
        'framework': framework,
        'naming_pattern': naming_pattern,
        'file_structure': file_structure,
        'import_patterns': import_patterns,
        'assertion_style': assertion_style,
        'setup_teardown': setup_teardown,
        'example_files': [os.path.basename(f) for f in test_files],
        'confidence': confidence
    }


def is_test_file(filename: str) -> bool:
    """Check if filename matches common test file patterns"""
    patterns = [
        r'^test_.*\.py$',
        r'.*_test\.py$',
        r'.*\.test\.(js|ts|jsx|tsx)$',
        r'.*\.spec\.(js|ts|jsx|tsx)$',
        r'.*Tests\.cs$',
        r'.*Test\.java$',
        r'.*Spec\.rb$'
    ]
    return any(re.match(pattern, filename, re.IGNORECASE) for pattern in patterns)


def get_language_from_file(filepath: str) -> str:
    """Determine programming language from file extension"""
    ext = Path(filepath).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.cs': 'csharp',
        '.java': 'java',
        '.rb': 'ruby'
    }
    return language_map.get(ext, 'unknown')


def detect_test_framework(file_content: str) -> str:
    """Detect testing framework from file content"""
    # Python frameworks
    if 'import pytest' in file_content or 'from pytest' in file_content:
        return 'pytest'
    if 'import unittest' in file_content or 'from unittest' in file_content:
        return 'unittest'
    
    # JavaScript/TypeScript frameworks
    if 'from \'@jest' in file_content or 'require(\'jest' in file_content or 'describe(' in file_content and 'it(' in file_content:
        return 'jest'
    if 'from \'mocha\'' in file_content or 'require(\'mocha\')' in file_content:
        return 'mocha'
    
    # .NET frameworks
    if 'using NUnit' in file_content or '[Test]' in file_content or '[TestFixture]' in file_content:
        return 'nunit'
    if 'using Xunit' in file_content or '[Fact]' in file_content or '[Theory]' in file_content:
        return 'xunit'
    if 'using Microsoft.VisualStudio.TestTools' in file_content or '[TestMethod]' in file_content:
        return 'mstest'
    
    # Java frameworks
    if 'import org.junit' in file_content or '@Test' in file_content:
        return 'junit'
    if 'import org.testng' in file_content:
        return 'testng'
    
    return 'unknown'


def extract_naming_pattern(filenames: List[str]) -> str:
    """Extract common naming pattern from filenames"""
    if not filenames:
        return 'unknown'
    
    # Check for common patterns
    if all(f.startswith('test_') for f in filenames):
        return 'test_*.py (pytest style)'
    if all(f.endswith('_test.py') for f in filenames):
        return '*_test.py'
    if all('.test.' in f for f in filenames):
        return '*.test.js/ts (Jest style)'
    if all('.spec.' in f for f in filenames):
        return '*.spec.js/ts'
    if all(f.endswith('Tests.cs') for f in filenames):
        return '*Tests.cs (NUnit/xUnit style)'
    if all(f.endswith('Test.java') for f in filenames):
        return '*Test.java (JUnit style)'
    
    # Mixed or custom pattern
    return f"mixed pattern (examples: {', '.join(filenames[:3])})"


def extract_imports(file_content: str) -> List[str]:
    """Extract import/using statements from file"""
    imports = []
    
    # Python imports
    python_imports = re.findall(r'^(?:import|from)\s+([^\s]+)', file_content, re.MULTILINE)
    imports.extend(python_imports)
    
    # JavaScript/TypeScript imports
    js_imports = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', file_content)
    imports.extend(js_imports)
    
    # C# using statements
    cs_imports = re.findall(r'^using\s+([^;]+);', file_content, re.MULTILINE)
    imports.extend(cs_imports)
    
    # Java imports
    java_imports = re.findall(r'^import\s+([^;]+);', file_content, re.MULTILINE)
    imports.extend(java_imports)
    
    return imports


def detect_assertions(file_content: str) -> List[str]:
    """Detect assertion styles used in tests"""
    assertions = []
    
    # Python assertions
    if re.search(r'\bassert\s+', file_content):
        assertions.append('assert (pytest/python)')
    if 'self.assert' in file_content:
        assertions.append('self.assert* (unittest)')
    
    # JavaScript assertions
    if 'expect(' in file_content:
        assertions.append('expect() (Jest/Chai)')
    if 'assert.' in file_content and ('chai' in file_content.lower() or 'assert' in file_content):
        assertions.append('assert.* (Chai/Node)')
    
    # .NET assertions
    if 'Assert.AreEqual' in file_content or 'Assert.IsTrue' in file_content:
        assertions.append('Assert.* (NUnit/MSTest)')
    if 'Assert.Equal' in file_content or 'Assert.True' in file_content:
        assertions.append('Assert.* (xUnit)')
    
    # Java assertions
    if 'assertEquals' in file_content or 'assertTrue' in file_content:
        assertions.append('assert* (JUnit)')
    
    return assertions


def detect_setup_teardown(file_content: str) -> Optional[str]:
    """Detect setup/teardown patterns"""
    # Python
    if '@pytest.fixture' in file_content:
        return '@pytest.fixture'
    if 'def setUp' in file_content or 'def tearDown' in file_content:
        return 'setUp/tearDown (unittest)'
    
    # JavaScript
    if 'beforeEach' in file_content or 'afterEach' in file_content:
        return 'beforeEach/afterEach (Jest/Mocha)'
    if 'beforeAll' in file_content or 'afterAll' in file_content:
        return 'beforeAll/afterAll (Jest/Mocha)'
    
    # .NET
    if '[SetUp]' in file_content or '[TearDown]' in file_content:
        return '[SetUp]/[TearDown] (NUnit)'
    if '[TestInitialize]' in file_content or '[TestCleanup]' in file_content:
        return '[TestInitialize]/[TestCleanup] (MSTest)'
    
    # Java
    if '@Before' in file_content or '@After' in file_content:
        return '@Before/@After (JUnit)'
    if '@BeforeEach' in file_content or '@AfterEach' in file_content:
        return '@BeforeEach/@AfterEach (JUnit 5)'
    
    return None


def analyze_file_structure(file_content: str, language: str) -> str:
    """Analyze test file structure (classes, functions, etc.)"""
    if language == 'python':
        has_classes = bool(re.search(r'^class\s+Test', file_content, re.MULTILINE))
        has_functions = bool(re.search(r'^def\s+test_', file_content, re.MULTILINE))
        if has_classes and has_functions:
            return 'class-based with test methods'
        elif has_classes:
            return 'class-based organization'
        elif has_functions:
            return 'function-based tests'
    
    elif language in ['javascript', 'typescript']:
        has_describe = 'describe(' in file_content
        has_it = 'it(' in file_content
        if has_describe and has_it:
            return 'describe/it blocks (BDD style)'
        elif has_it:
            return 'it() test functions'
    
    elif language == 'csharp':
        has_test_fixture = '[TestFixture]' in file_content
        has_test_methods = '[Test]' in file_content or '[Fact]' in file_content
        if has_test_fixture and has_test_methods:
            return 'class with [TestFixture] and [Test] methods'
        elif has_test_methods:
            return 'class with test methods'
    
    elif language == 'java':
        has_test_annotation = '@Test' in file_content
        if has_test_annotation:
            return 'class with @Test methods'
    
    return 'standard test structure'


def most_common(items: List[str]) -> str:
    """Return most common item in list"""
    if not items:
        return 'unknown'
    return max(set(items), key=items.count)


def most_common_items(items: List[str], top_n: int = 10) -> List[str]:
    """Return top N most common items"""
    if not items:
        return []
    from collections import Counter
    counter = Counter(items)
    return [item for item, count in counter.most_common(top_n)]


def aggregate_structures(structures: List[str]) -> str:
    """Aggregate file structures into common pattern"""
    if not structures:
        return 'unknown'
    return most_common(structures)


def calculate_confidence(frameworks: List[str], assertions: List[str], setups: List[str]) -> float:
    """Calculate confidence score based on consistency of detected patterns"""
    score = 0.0
    
    # Framework consistency
    if frameworks:
        framework_consistency = frameworks.count(most_common(frameworks)) / len(frameworks)
        score += framework_consistency * 0.4
    
    # Assertion detection
    if assertions:
        score += 0.3
    
    # Setup/teardown detection
    if setups:
        score += 0.3
    
    return min(score, 1.0)
