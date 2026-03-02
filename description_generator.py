"""
Project Description Generator — LLM-based.

Reads all solution and test files, sends them to an LLM, and gets back
a structured academic problem statement. No static extraction (regex/parsing).
"""

import os
from typing import Dict, List, Optional

# For LLM
try:
    from langchain_openai import AzureChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    _LLM_AVAILABLE = True
except ImportError:
    _LLM_AVAILABLE = False


SKIP_DIRS = {
    '.git', 'node_modules', 'bin', 'obj', '__pycache__', 'venv', '.venv',
    'dist', 'build', 'dotnettemplates', 'templates', 'template',
    'angularscaffolding', 'scaffolding'
}
CODE_EXTS = ('.cs', '.py', '.js', '.ts', '.java')
MAX_CHARS_PER_FILE = 8000
MAX_TOTAL_CHARS = 120_000


# ─────────────────────────────────────────────────────────────────────────────
# FILE DISCOVERY & READING
# ─────────────────────────────────────────────────────────────────────────────

def _walk_code_files(root_dir: str) -> List[str]:
    results = []
    if not os.path.isdir(root_dir):
        return results
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(CODE_EXTS):
                results.append(os.path.join(dirpath, f))
    return results


def _read_file(path: str, max_chars: int = MAX_CHARS_PER_FILE) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [truncated, file too long]\n"
        return content
    except Exception:
        return ""


def _find_solution_and_test_dirs(workspace: str):
    sol_patterns = {'src', 'dotnetapp', 'lib', 'app', 'controllers', 'services', 'models'}
    test_patterns = {'test', 'tests', 'nunit', '__tests__', 'spec'}
    sol, tst = [], []

    for item in os.listdir(workspace):
        if item in SKIP_DIRS:
            continue
        full = os.path.join(workspace, item)
        if not os.path.isdir(full):
            continue
        low = item.lower()
        if low in test_patterns or 'test' in low or 'nunit' in low or 'spec' in low:
            tst.append(item)
        elif low in sol_patterns or low in ('data', 'exceptions'):
            sol.append(item)
        else:
            has_sub_sol = has_sub_test = False
            try:
                for sub in os.listdir(full):
                    sl = sub.lower()
                    if sl in sol_patterns or sl in ('data', 'exceptions'):
                        has_sub_sol = True
                    if sl in test_patterns or 'test' in sl or 'nunit' in sl:
                        has_sub_test = True
            except OSError:
                pass
            if has_sub_sol:
                sol.append(item)
            if has_sub_test:
                tst.append(item)

    if not sol:
        sol = ['.']
    return sol, tst


# ─────────────────────────────────────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────────────────────────────────────

def _get_description_llm():
    if not _LLM_AVAILABLE:
        raise RuntimeError("langchain_openai not installed. Install with: pip install langchain-openai")
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://iamneo-qb.openai.azure.com/"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "BseWgixIxbzsRMTI9XcdwIS39aVLQT791lDu1gi3rBBFngSSOH7vJQQJ99BIACYeBjFXJ3w3AAABACOGv3VO"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        temperature=0.2,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Project Description Generator. Your task is to produce an academic, exam-style problem statement that a student can use to implement the solution and pass all tests.

PROCESS:
1. Read and understand ALL solution files (business logic, classes, methods, properties, relationships).
2. Read and understand ALL test files (expected behavior, console messages, status codes, validations, exception handling).
3. Infer the project type (ADO.NET Console, WebAPI, or generic).
4. Produce a single structured markdown description in ONE pass.

CRITICAL OUTPUT RULES — THE DESCRIPTION MUST:
- NOT include any code syntax, code blocks, or backticks.
- NOT include test case names or test file names.
- NOT mention unit testing, assertions, or NUnit/xUnit/Jest/pytest.
- NOT include config file details (csproj, package.json, etc.).
- NOT leak internal implementation details.
- NOT create a "Testcases" section or reference demo.md/templates.

THE DESCRIPTION MUST:
- Be sufficient for a student to implement and pass all tests.
- Be academic and exam-oriented.
- Clearly define models (classes and properties).
- Clearly define methods/endpoints (purpose, parameters, return type).
- Clearly describe expected console messages or API responses.
- Clearly describe validations and exception handling.
- Follow the correct template structure based on project type.

TEMPLATE — ADO.NET CONSOLE (Program.cs + SqlDataAdapter/DataSet/DataTable):
1. Title (Problem Statement: <Domain>)
2. Objective
3. Folder Structure (if needed)
4. Table Details
5. Classes and Properties
6. Database Details
7. Methods (purpose, parameters, return type, console messages)
8. Main Menu
9. Commands to Run
10. Notes

TEMPLATE — WEB API (Controllers + DbContext + Models):
1. Title
2. Problem Statement
3. Models (class properties, relationships, JsonIgnore where applicable)
4. DbContext description (DbSet properties, relationships)
5. Controllers and methods (purpose, HTTP method, route, status codes)
6. Endpoints list
7. Status Codes and Error Handling
8. Exceptions (if any)
9. Commands to Run
10. Notes

TEMPLATE — GENERIC:
1. Problem Statement
2. Objective
3. Classes and Properties
4. Methods
5. Expected Behavior (console/API responses)
6. Notes

FORMAT:
- Use **bold** for headings and key terms.
- Use bullet points for properties and options.
- Describe behavior in plain language, never with code.
- No code fences, no inline code, no syntax."""


def _build_user_prompt(solution_files: Dict[str, str], test_files: Dict[str, str]) -> str:
    parts = [
        "Analyze the following solution and test files, then produce the project description.\n\n"
        "=== SOLUTION FILES ===\n\n"
    ]
    total = 0
    for path, content in solution_files.items():
        rel = os.path.basename(path)
        block = f"--- {rel} ---\n{content}\n\n"
        if total + len(block) > MAX_TOTAL_CHARS:
            break
        parts.append(block)
        total += len(block)

    parts.append("\n=== TEST FILES ===\n\n")
    for path, content in test_files.items():
        rel = os.path.basename(path)
        block = f"--- {rel} ---\n{content}\n\n"
        if total + len(block) > MAX_TOTAL_CHARS:
            break
        parts.append(block)
        total += len(block)

    parts.append(
        "\n--- END OF FILES ---\n\n"
        "Produce ONLY the final project description in markdown. "
        "Do not include any explanation, reasoning, or analysis. "
        "Output the description directly."
    )
    return "".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate_project_description(
    workspace_path: str,
    reference_description_path: Optional[str] = None,
    output_filename: str = "PROJECT_DESCRIPTION.md",
    llm=None,
) -> Dict:
    """
    Generate a project description using an LLM.
    Reads all solution and test files, sends to LLM, writes the response to file.

    Args:
        workspace_path: Root of the project.
        reference_description_path: Ignored (kept for compatibility).
        output_filename: Output file name.
        llm: Optional LangChain LLM instance. If None, creates AzureChatOpenAI from env.
    """
    result = {
        'success': False,
        'output_path': '',
        'solution_files': [],
        'classes_documented': 0,
        'methods_documented': 0,
        'cache_summary': '',
        'errors': []
    }

    try:
        # 1. Discover dirs
        solution_dirs, test_dirs = _find_solution_and_test_dirs(workspace_path)

        # 2. Read solution files
        solution_files: Dict[str, str] = {}
        for d in solution_dirs:
            for fp in _walk_code_files(os.path.join(workspace_path, d)):
                solution_files[fp] = _read_file(fp)
        result['solution_files'] = [os.path.relpath(p, workspace_path) for p in solution_files]

        # 3. Read test files
        test_files: Dict[str, str] = {}
        for d in test_dirs:
            for fp in _walk_code_files(os.path.join(workspace_path, d)):
                if fp not in solution_files:
                    test_files[fp] = _read_file(fp)

        if not solution_files:
            result['errors'].append("No solution files found")
            return result

        # 4. Build prompt and call LLM
        user_prompt = _build_user_prompt(solution_files, test_files)
        if llm is None:
            llm = _get_description_llm()

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        description = response.content if hasattr(response, 'content') else str(response)

        # 5. Basic cleanup — remove code fences if LLM included them
        if "```" in description:
            import re
            description = re.sub(r'```[\s\S]*?```', '', description)
            description = re.sub(r'\n{3,}', '\n\n', description).strip()

        # 6. Write
        out_path = os.path.join(workspace_path, output_filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(description)

        result['success'] = True
        result['output_path'] = out_path
        result['classes_documented'] = description.count('**') // 2  # rough section/term count
        result['methods_documented'] = 0  # LLM output, no structured count

    except Exception as e:
        result['errors'].append(str(e))
        import traceback
        traceback.print_exc()

    return result
