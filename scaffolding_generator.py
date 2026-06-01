"""
Scaffolding Generator — Creates student-ready scaffolding from a completed project.

Workflow:
  Completed workspace (dotnetapp/ + nunit/ + tests)
      ↓
  Copy to workspace/scaffolding/
      ↓
  Solution files  → method bodies stripped → TODO placeholders
  Test files      → copied verbatim (unchanged)
  Infrastructure  → copied verbatim (.csproj, .sln, .sh, .json, etc.)
"""

import os
import re
import shutil
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# File extensions that are always copied verbatim (never code-stripped)
VERBATIM_EXTS: set = {
    '.csproj', '.sln', '.sh', '.md', '.gitignore', '.gitattributes',
    '.json', '.yml', '.yaml', '.xml', '.config', '.props', '.targets',
    '.txt', '.env', '.dockerignore', '.editorconfig', '.ruleset',
}

# Code file extensions that may need method-body stripping
CODE_EXTS: set = {'.cs', '.py', '.ts', '.js', '.java'}

# Directories to never copy into scaffolding
SKIP_DIRS: set = {
    '.git', 'node_modules', 'bin', 'obj', '__pycache__',
    '.venv', 'venv', 'dist', 'build', 'scaffolding',
    'dotnettemplates', 'templates', 'template', 'angularscaffolding',
    '.idea', '.vscode', '.cursor', 'backup_api', 'extension-builder',
    '.neuralstack_logs',
}

# Top-level directory name signals that indicate a TEST directory
# → copied verbatim, never stripped
TEST_DIR_SIGNALS: set = {
    'nunit', 'test', 'tests', 'spec', 'specs',
    '__tests__', 'xunit', 'mstest', 'testproject',
}

# Top-level directory name signals that indicate a SOLUTION directory
# → code files are stripped
SOLUTION_DIR_SIGNALS: set = {
    'dotnetapp', 'src', 'app', 'lib', 'controllers',
    'services', 'models', 'webapi', 'api',
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — BRACE COUNTING
# ─────────────────────────────────────────────────────────────────────────────

def _count_code_braces(line: str) -> Tuple[int, int]:
    """Count { and } that are NOT inside string literals or line comments."""
    opens = closes = 0
    in_str = False
    i = 0
    s = line
    while i < len(s):
        ch = s[i]
        if in_str:
            if ch == '\\':
                i += 2
                continue
            if ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '/' and i + 1 < len(s) and s[i + 1] == '/':
                break  # rest is a line comment
            elif ch == '{':
                opens += 1
            elif ch == '}':
                closes += 1
        i += 1
    return opens, closes


# ─────────────────────────────────────────────────────────────────────────────
# C# STRIPPING
# ─────────────────────────────────────────────────────────────────────────────

# Keywords that open non-method blocks (class, namespace, control flow)
_CSHARP_TYPE_DECLS = frozenset({
    'class', 'interface', 'struct', 'enum', 'record', 'namespace'
})
_CSHARP_CONTROL = frozenset({
    'if', 'else', 'for', 'foreach', 'while', 'do', 'switch',
    'try', 'catch', 'finally', 'using', 'lock', 'fixed',
    'checked', 'unchecked', 'return', 'throw', 'case', 'default',
})
_CSHARP_MODS = frozenset({
    'public', 'private', 'protected', 'internal', 'static',
    'virtual', 'override', 'abstract', 'async', 'sealed', 'new',
    'partial', 'readonly', 'extern', 'unsafe',
})

_AUTO_PROP_RE = re.compile(r'\{\s*(?:get|set|init)\s*;', re.IGNORECASE)
_VOID_RE = re.compile(r'\bvoid\b', re.IGNORECASE)
_TASK_SIMPLE_RE = re.compile(r'\bTask\b(?!\s*<)', re.IGNORECASE)


def _is_csharp_method_sig(line: str) -> bool:
    """
    Return True if this line looks like a C# method or constructor signature.

    Distinguishes methods from:  class/interface/struct/enum/namespace declarations,
    control-flow statements (if/for/while/…), auto-properties { get; set; },
    field declarations (end with ;), attribute lines ([…]), lambda expressions (=>).
    """
    s = line.strip()
    if not s:
        return False
    # Skip comment lines, attributes, preprocessor
    if s.startswith('//') or s.startswith('*') or s.startswith('[') or s.startswith('#'):
        return False
    # Must contain parentheses (parameters)
    if '(' not in s or ')' not in s:
        return False
    # Auto-property shorthand
    if _AUTO_PROP_RE.search(s):
        return False
    # Field / property declaration ending with ;
    if s.rstrip().endswith(';'):
        return False
    # Lambda expression
    if '=>' in s:
        return False
    # First non-modifier word determines the context
    words = s.split()
    first_non_mod = next((w.strip('(*<') for w in words if w.lower() not in _CSHARP_MODS), '')
    if first_non_mod.lower() in _CSHARP_TYPE_DECLS:
        return False
    # Control flow: first real word is a keyword
    first_word = words[0].lower().rstrip('(') if words else ''
    if first_word in _CSHARP_CONTROL:
        return False
    return True


def _csharp_todo_lines(method_sig: str, indent: str) -> List[str]:
    """Return the TODO placeholder lines appropriate for the method's return type."""
    if _VOID_RE.search(method_sig) or 'Main' in method_sig:
        return [f'{indent}// TODO: Implement this method']
    if _TASK_SIMPLE_RE.search(method_sig):
        return [
            f'{indent}// TODO: Implement this method',
            f'{indent}return Task.CompletedTask;',
        ]
    return [
        f'{indent}// TODO: Implement this method',
        f'{indent}throw new NotImplementedException();',
    ]


def _strip_csharp(content: str) -> str:
    """
    Strip method and constructor bodies from C# source code.

    State machine (line-by-line):
    • When NOT in a method body:
        - Detect a method signature + opening { (same line or next line).
        - Keep the signature line unchanged.
        - Switch to "in_body" mode.
    • When IN a method body:
        - Track brace depth; insert TODO once on the first content line.
        - Skip all subsequent body lines.
        - When depth drops back to entry level, emit the closing } and exit.
    """
    lines = content.split('\n')
    out: List[str] = []

    depth = 0          # current brace depth (not counting strings/comments)
    in_body = False    # are we inside a stripped method body?
    body_depth = None  # brace depth immediately AFTER the opening { of current method
    todo_done = False
    current_sig = ''
    pending_sig = None  # sig text when { will appear on the NEXT line

    for line in lines:
        opens, closes = _count_code_braces(line)
        stripped = line.strip()

        if in_body:
            depth += opens - closes

            if depth < body_depth:
                # Exited the method body — this line is the closing }
                in_body = False
                body_depth = None
                todo_done = False
                current_sig = ''
                out.append(line)
            elif not todo_done:
                # First real line inside the body → emit TODO
                cur_indent = len(line) - len(line.lstrip()) if line.strip() else 8
                for todo_line in _csharp_todo_lines(current_sig, ' ' * cur_indent):
                    out.append(todo_line)
                todo_done = True
                # The original content line is intentionally dropped
            # All subsequent body lines are skipped (already inserted TODO once)

        else:
            # ── Handle pending signature (brace expected on this line) ──
            if pending_sig is not None:
                if stripped == '{':
                    # Opening brace on its own line → enter body
                    depth += 1
                    body_depth = depth
                    in_body = True
                    todo_done = False
                    current_sig = pending_sig
                    pending_sig = None
                    out.append(line)
                    continue
                elif stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
                    # Some other line followed the sig candidate → it wasn't a sig
                    pending_sig = None

            # ── Look for method openings ──
            if '{' in line and not _AUTO_PROP_RE.search(line):
                if _is_csharp_method_sig(line):
                    # Method/constructor with { on the SAME line
                    depth += opens - closes
                    body_depth = depth
                    in_body = True
                    todo_done = False
                    current_sig = stripped
                    pending_sig = None
                    out.append(line)  # keep the signature line
                else:
                    # class / namespace / if / for / property-with-body / etc.
                    depth += opens - closes
                    out.append(line)
            elif _is_csharp_method_sig(line) and '{' not in line:
                # Method signature with { on the NEXT line
                pending_sig = stripped
                depth += opens - closes
                out.append(line)
            else:
                depth += opens - closes
                out.append(line)

    return '\n'.join(out)


# ─────────────────────────────────────────────────────────────────────────────
# PYTHON STRIPPING
# ─────────────────────────────────────────────────────────────────────────────

def _strip_python(content: str) -> str:
    """
    Strip Python function/method bodies, replacing with:
        # TODO: Implement this method
        pass
    Keeps: imports, class declarations, decorators, docstrings (first line only), fields.
    """
    lines = content.split('\n')
    out: List[str] = []

    DEF_RE = re.compile(r'^(\s*)def\s+\w+\s*\(')
    in_body = False
    body_indent = ''
    sig_indent = ''
    todo_done = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_body:
            cur_indent = len(line) - len(line.lstrip()) if line.strip() else len(body_indent)
            if stripped and cur_indent <= len(sig_indent):
                # Back to or above function level → exit body
                in_body = False
                body_indent = ''
                todo_done = False
                # Do NOT skip this line — it's the first line after the function
                out.append(line)
            elif not todo_done and stripped:
                # First real line in body → emit TODO
                out.append(f'{body_indent}# TODO: Implement this method')
                out.append(f'{body_indent}pass')
                todo_done = True
                # Skip the original line
            # Else: skip body lines (already inserted TODO)
        else:
            m = DEF_RE.match(line)
            if m:
                sig_indent = m.group(1)
                body_indent = sig_indent + '    '
                in_body = True
                todo_done = False
            out.append(line)

        i += 1

    return '\n'.join(out)


# ─────────────────────────────────────────────────────────────────────────────
# DIRECTORY CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def _is_under_test_dir(rel_path: str) -> bool:
    """Return True if rel_path (relative to workspace root) is inside a test directory."""
    parts = rel_path.replace('\\', '/').split('/')
    return any(
        p.lower() in TEST_DIR_SIGNALS
        or 'test' in p.lower()
        or 'nunit' in p.lower()
        or 'spec' in p.lower()
        for p in parts
    )


def _classify_top_level_dirs(workspace_path: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Walk workspace root and classify top-level directories into:
      sol_dirs  — solution directories (code to be stripped)
      test_dirs — test directories (copied verbatim)
      skip_dirs — infrastructure / ignored directories

    Returns (sol_dirs, test_dirs) as lists of *directory names* (not full paths).
    """
    sol_dirs: List[str] = []
    test_dirs: List[str] = []

    try:
        entries = os.listdir(workspace_path)
    except OSError:
        return sol_dirs, test_dirs, []

    for name in entries:
        if name in SKIP_DIRS:
            continue
        full = os.path.join(workspace_path, name)
        if not os.path.isdir(full):
            continue
        low = name.lower()
        if low in TEST_DIR_SIGNALS or 'test' in low or 'nunit' in low or 'spec' in low:
            test_dirs.append(name)
        elif low in SOLUTION_DIR_SIGNALS:
            sol_dirs.append(name)
        else:
            # Unknown directory — classify by scanning for sub-dirs
            sub_names = []
            try:
                sub_names = os.listdir(full)
            except OSError:
                pass
            is_sol = any(
                s.lower() in SOLUTION_DIR_SIGNALS or s.lower() in {'program.cs', 'models'}
                for s in sub_names
            )
            is_test = any(
                s.lower() in TEST_DIR_SIGNALS or 'test' in s.lower()
                for s in sub_names
            )
            if is_test and not is_sol:
                test_dirs.append(name)
            elif is_sol:
                sol_dirs.append(name)
            else:
                sol_dirs.append(name)  # default: treat as solution

    return sol_dirs, test_dirs


# ─────────────────────────────────────────────────────────────────────────────
# STRIP DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

def _strip_code_file(content: str, ext: str) -> str:
    """Strip solution code from a file based on its extension."""
    if ext == '.cs':
        return _strip_csharp(content)
    if ext == '.py':
        return _strip_python(content)
    # TypeScript / JavaScript / Java: return as-is for now
    # (extend here when needed)
    return content


# ─────────────────────────────────────────────────────────────────────────────
# MAIN API
# ─────────────────────────────────────────────────────────────────────────────

def create_scaffolding(
    workspace_path: str,
    output_base: str,
    project_name: str = '',
    scaffold_tests: bool = False,
) -> Dict:
    """
    Create a student-ready scaffolding from the completed project in workspace_path.

    Args:
        workspace_path : Root of the completed project workspace.
        output_base    : Base directory where the scaffolding folder will be created.
                         Typically the same as workspace_path (so output goes to
                         workspace_path/scaffolding/).
        project_name   : Subfolder name inside output_base/scaffolding/. When empty,
                         the scaffolding goes directly into output_base/scaffolding/.
        scaffold_tests : If True, also strip test files. Default False (tests verbatim).

    Returns:
        dict with keys:
          success         (bool)
          output_path     (str)
          scaffolded_files (list of str) — files that had code stripped
          copied_files    (list of str) — files copied verbatim
          errors          (list of str)
    """
    result: Dict = {
        'success': False,
        'output_path': '',
        'scaffolded_files': [],
        'copied_files': [],
        'errors': [],
    }

    # ── Resolve output path ──────────────────────────────────────────────────
    if project_name:
        output_path = os.path.join(output_base, 'scaffolding', project_name)
    else:
        output_path = os.path.join(output_base, 'scaffolding')

    result['output_path'] = output_path

    # Remove old scaffolding if it exists so we get a clean copy
    if os.path.exists(output_path):
        try:
            shutil.rmtree(output_path)
        except Exception as exc:
            result['errors'].append(f'Cannot remove old scaffolding: {exc}')
            return result

    os.makedirs(output_path, exist_ok=True)

    # ── Classify top-level directories ──────────────────────────────────────
    sol_dirs, test_dirs = _classify_top_level_dirs(workspace_path)[:2]

    # Build set of all dirs to process (sol + test)
    all_target_dirs = set(sol_dirs) | set(test_dirs)

    # If nothing was classified, fallback: treat everything (except SKIP_DIRS) as solution
    if not all_target_dirs:
        try:
            for name in os.listdir(workspace_path):
                if name not in SKIP_DIRS and os.path.isdir(os.path.join(workspace_path, name)):
                    sol_dirs.append(name)
                    all_target_dirs.add(name)
        except OSError as exc:
            result['errors'].append(f'Cannot list workspace: {exc}')
            return result

    # ── Copy files ───────────────────────────────────────────────────────────
    def _process_dir(src_dir: str, dst_dir: str, is_test_area: bool) -> None:
        os.makedirs(dst_dir, exist_ok=True)

        try:
            entries = list(os.scandir(src_dir))
        except OSError as exc:
            result['errors'].append(f'Cannot scan {src_dir}: {exc}')
            return

        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            src_path = entry.path
            dst_path = os.path.join(dst_dir, entry.name)

            if entry.is_dir():
                sub_is_test = is_test_area or _is_under_test_dir(
                    os.path.relpath(src_path, workspace_path)
                )
                _process_dir(src_path, dst_path, sub_is_test)
                continue

            # It's a file
            ext = os.path.splitext(entry.name)[1].lower()
            rel = os.path.relpath(src_path, workspace_path)

            should_verbatim = (
                is_test_area                      # inside test directory → verbatim
                or (not scaffold_tests and _is_under_test_dir(rel))
                or ext in VERBATIM_EXTS           # config/infra file → verbatim
                or ext not in CODE_EXTS           # non-code file → verbatim
            )

            try:
                if should_verbatim:
                    shutil.copy2(src_path, dst_path)
                    result['copied_files'].append(rel)
                else:
                    with open(src_path, 'r', encoding='utf-8', errors='replace') as f:
                        original = f.read()
                    scaffolded = _strip_code_file(original, ext)
                    with open(dst_path, 'w', encoding='utf-8') as f:
                        f.write(scaffolded)
                    result['scaffolded_files'].append(rel)
            except Exception as exc:
                result['errors'].append(f'Error processing {rel}: {exc}')

    # Process each target directory
    for dir_name in sorted(all_target_dirs):
        src = os.path.join(workspace_path, dir_name)
        dst = os.path.join(output_path, dir_name)
        is_test = dir_name in test_dirs
        _process_dir(src, dst, is_test)

    result['success'] = True
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def get_scaffolding_summary(result: Dict) -> str:
    """Convert a create_scaffolding result dict into a human-readable string."""
    if not result.get('success'):
        errors = '\n'.join(f'  • {e}' for e in result.get('errors', []))
        return f'❌ Scaffolding failed.\nErrors:\n{errors}'

    stripped = result['scaffolded_files']
    copied = result['copied_files']
    errors = result.get('errors', [])

    lines = [
        f'✅ Scaffolding created at: {result["output_path"]}',
        f'',
        f'📝 Files with solution stripped ({len(stripped)}):',
    ]
    for f in stripped:
        lines.append(f'  • {f}')
    lines.append(f'')
    lines.append(f'📋 Files copied verbatim ({len(copied)} — tests + infrastructure):')
    for f in copied[:20]:  # limit verbatim list to keep summary readable
        lines.append(f'  • {f}')
    if len(copied) > 20:
        lines.append(f'  … and {len(copied) - 20} more')
    if errors:
        lines.append(f'')
        lines.append(f'⚠️ Warnings/errors ({len(errors)}):')
        for e in errors:
            lines.append(f'  • {e}')

    lines.append('')
    lines.append(
        '💡 Next steps:\n'
        '  1. Review the scaffolding files in the scaffolding/ folder.\n'
        '  2. Generate a description aligned with the scaffolding:\n'
        '     generate_project_description(use_scaffolding=True)'
    )

    return '\n'.join(lines)
