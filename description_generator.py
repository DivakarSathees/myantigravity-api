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
    """
    Find solution and test directory paths relative to workspace.
    When a top-level folder (e.g. dotnetwebapi) contains both solution (dotnetapp)
    and test (nunit) subfolders, we return those subfolder paths so solution and
    test files are read separately. Otherwise the same tree would be scanned twice
    and test files would be omitted (treated as duplicates).
    """
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
        # Top-level dir is clearly solution-only or test-only
        if low in test_patterns or 'test' in low or 'nunit' in low or 'spec' in low:
            tst.append(item)
        elif low in sol_patterns or low in ('data', 'exceptions'):
            sol.append(item)
        else:
            # Parent folder (e.g. dotnetwebapi): look inside for solution/test subfolders
            sol_subs = []
            tst_subs = []
            try:
                for sub in os.listdir(full):
                    sl = sub.lower()
                    if sl in sol_patterns or sl in ('data', 'exceptions'):
                        sol_subs.append(os.path.join(item, sub))
                    if sl in test_patterns or 'test' in sl or 'nunit' in sl or 'spec' in sl:
                        tst_subs.append(os.path.join(item, sub))
            except OSError:
                pass
            if sol_subs:
                sol.extend(sol_subs)
            elif not tst_subs and not sol:
                # No solution/test subfolders found; treat parent as solution root
                sol.append(item)
            if tst_subs:
                tst.extend(tst_subs)

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
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        # temperature=0.2,
    )
      

# ─────────────────────────────────────────────────────────────────────────────
# STACK-SPECIFIC DESCRIPTION TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
# Each template defines the EXACT structure and section order the LLM must follow.
# Use **bold** for headings/key terms; bullet points for properties/options; no code blocks.

DESCRIPTION_TEMPLATES = {
    "dotnet_webapi": """
You MUST produce the description in EXACTLY this structure and order. Follow this template strictly.

### **<ProjectTitle>**

**Problem Statement:**
**Develop a Web API project for <ProjectTitle>** using **ASP.NET Core**. <One or two sentences describing the domain and what the API manages: entities, CRUD operations, validations, exception handling.> The system should <key capabilities>. You will need to define models, controllers, and handle status codes correctly. Implement validation and exception handling for erroneous input, especially <relevant cases: missing data, invalid dates, etc.>.

Your task is to implement the API based on the following requirements.

**Models:**
<Numbered list, one per model file. For each:>
1. **<ModelName>.cs:**
   * **<PropertyName> (<type>):** <Short description. Mention primary key, required, format, JsonIgnore if applicable.>
   * **<PropertyName> (<type>):** ...
   * **<NavigationProperty> (<type>?):** <Description and relationship (one-to-many, many-to-one). Mention JsonIgnore if applied.>

Using **ApplicationDbContext** for <list entity names> system. **ApplicationDbContext** must be present inside the **Data** folder.
* **Namespace - dotnetapp.Data**

The **ApplicationDbContext** class acts as the primary interface between the application and the database, managing CRUD operations for <entities>. This context class defines the database schema through its DbSet properties and manages the **relationships** between entities using the Fluent API.

**DbSet Properties:**
1. **DbSet<<Entity>> <TableName>:** <What the table represents and relationship (e.g. one-to-many).>
2. **DbSet<<Entity>> <TableName>:** ...

**Implement the actual logic in the controller:**

**Controllers: Namespace: dotnetapp.Controllers**

**<ControllerName>**
* **<MethodName>(<params>):** <What it does. When it returns 204/200/201/400/404, validation rules, eager loading (Include) if used.>
* **<MethodName>(<params>):** ...

**<OtherControllerName>**
* ...

**Exceptions:**
* **<ExceptionName>** is a custom exception located in the **dotnetapp.Exceptions** folder.
* <When it is thrown and the message.>

**Endpoints:**
**<Resource1>:**
**GET /api/<Resource>:** <Brief description.>
**POST /api/<Resource>:** ...
**PUT /api/<Resource>/{id}:** ...

**<Resource2>:**
...

**Status Codes and Error Handling:**
**204 No Content:** <When returned.>
**200 OK:** ...
**201 Created:** ...
**400 Bad Request:** ...
**404 Not Found:** ...
**<CustomException>:** <When thrown and status code (e.g. 500).>

**Note:**
* Use swagger/index to view the API output screen in 8080 port.
* Don't delete any files in the project environment.
* When clicking on Run Testcase button make sure that your application is running on the port 8080.

**Commands to Run the Project:**
* **cd dotnetapp** — Select the dotnet project folder
* **dotnet restore** — Restore all required packages
* **dotnet run** — Run the application on port 8080
* **dotnet build** — Build and check for errors
* **dotnet clean** — If the same error persists, clean the project and build again

**For Entity Framework Core:**
To use Entity Framework:
Install EF:
* **dotnet new tool-manifest**
* **dotnet tool install --local dotnet-ef --version 6.0.6** — Then use dotnet dotnet-ef instead of dotnet-ef.
* **dotnet dotnet-ef** — To check if EF is installed.
* **dotnet dotnet-ef migrations add initialsetup** — Add migrations
* **dotnet dotnet-ef database update** — Update the database

**Note:**
Use the below sample connection string to connect to MsSql Server:
private string **connectionString** = "User ID=sa;password=examlyMssql@123; server=localhost;Database=appdb;trusted_connection=false;Persist Security Info=False;Encrypt=False"
""",

    "dotnet_console_ado": """
You MUST produce the description in EXACTLY this structure and order (ADO.NET Console — database with SqlConnection, SqlCommand, SqlDataAdapter).

**Problem Statement:** **<ProjectTitle>**

**Objective:**
You need to create the **<Entity>** table in the **appdb** database with the necessary columns. Then, develop a console-based C# application using ADO.NET to perform Create, Read, and Delete (and Update if applicable) operations on the <Entity> table in an SQL Server database. The application should enable users to <list key operations>. Implement using a combination of connected and disconnected architectures with **SqlConnection, SqlCommand,** and **SqlDataAdapter**. All classes, properties, and methods should be public.

**Folder Structure:**
<Describe or list folder structure if needed.>

**Table:**
<Table name and column definitions, or reference to database setup.>

### Classes and Properties

#### <Entity> Class (Models/<Entity>.cs)
The **<Entity>** class represents a <entity> entity with the following public properties:
* **<PropertyName> (<type>):** <Description. Mention auto-incremented/primary key if applicable.>
* **<PropertyName> (<type>):** ...
<Repeat for all properties.>

**Database Details:**
* Database Name: **appdb**
* Table Name: **<TableName>**
* Ensure that the database connection is properly established using the **ConnectionStringProvider** class in the file **Program.cs.**
* Use the below connection string to connect to MsSql Server:
* public static string **ConnectionString** { get; } = "User ID=sa;password=examlyMssql@123; server=localhost;Database=appdb;trusted_connection=false;Persist Security Info=False;Encrypt=False";

**To Work with SQLServer:**
(Open a New Terminal) type the below commands
**sqlcmd -U sa**
password: **examlyMssql@123**
1> create database appdb
2>go
1>use appdb
2>go
1> create table TableName(columnName datatype,...)
2> go
1> insert into TableName values(...)
2> go

**Methods:**
Define the following methods inside the **Program** class, located in the **Program.cs** file.

For EACH method provide:
#### N. **<MethodName>(<parameters>)**
* <One line purpose.>
* **Parameters**: <Description.>
* **Architecture**: <e.g. Uses disconnected architecture with SqlDataAdapter, DataSet, and DataRow.>
* **Access Modifier**: public
* **Declaration Modifier**: static (if applicable)
* **Return Type**: void (or as applicable)
* **Console Messages**:
* <When successful: exact message format, e.g. "Item added successfully with ID: {Id}" and line with all fields.>
* <When not found / error: exact message, e.g. "No item found with ID {id}.">

### Main Menu:
The main menu serves as the user interface. List options exactly, e.g.:
**<Domain> Management Menu - Enter your choice (1-5):**
1. Add <Entity>
2. Display All <Entities>
3. Display <Entities> Below Minimum Stock (or similar)
4. Delete <Entity>
5. Exit - Terminates the application with the message "Exiting the application...".
**Invalid choice** - Displays "Invalid choice."

**Commands to Run the Project:**
* **cd dotnetapp** — Select the dotnet project folder
* **dotnet restore** — Restore all required packages
* **dotnet run** — To run the application (port 8080 if applicable)
* **dotnet build** — Build and check for errors
* **dotnet clean** — If the same error persists, clean and build again
* **dotnet add package package_name --version 6.0** — Install any required package (support .Net 6.0)

**Note:**
1. **Do not change the class names.**
2. **Do not change the skeleton** (Structure of the project given).

**Refer to the Sample Output:**
**Add <Entity>:**
**Display All <Entities>:**
**Display <Entities> Below Minimum Stock:** (or similar)
**Delete <Entity>:**
**Exit:**
**Invalid choice:**
""",

    "dotnet_console_collection": """
You MUST produce the description in EXACTLY this structure and order (Console application using in-memory collection — List<Entity>, no database).

**<ProjectTitle>**

You need to develop the **<ProjectTitle>**, a console-based application in C# that <one line purpose>. Use a **List** to store and manage the collection of <entities>. Implement a menu-driven interface with options to **add, display, update, and delete** <entity> information. Ensure error handling with try-catch blocks to manage invalid data inputs, particularly using **FormatException**.

**Folder Structure:**
<Describe or list folder structure.>

### Classes and Methods

#### 1. <Entity> Class (Models/<Entity>.cs)
**Purpose:** Represents an individual <entity> in the system.
**Properties:**
* **<PropertyName> (<type>):** <Description. Mention constraints e.g. must be positive, cannot be negative.>
* **<PropertyName> (<type>):** ...
**Access Modifier:** public

#### 2. Program Class (Program.cs)
**Purpose:** Acts as the entry point for the application, containing the business logic to manage <entity> records.

**Properties:**
**<collectionName> (List<<Entity>>):** A **static** collection of <Entity> objects used to manage and store <entity> records.
**Access Modifier:** private

**Methods:**

**Main(string[] args):**
Handles the application's flow through a menu-driven interface with the following options:
1. **Add <Entity> Record:** <Brief description.>
2. **Display <Entities>:** <Brief description.>
3. **Update <Entity> Record:** <Brief description.>
4. **Delete <Entity> Record:** <Brief description.>
5. **Exit:** Terminates the application.
Displays the message "Invalid choice." if the input is outside the range 1–5.

**Add<Entity>Record(<Entity> entity):**
Adds a new <entity> to the list if validations pass.
* **Access Modifier:** public
* **Declaration Modifier:** static
* **Return Type:** void
* Success Message: "<Entity> record added successfully."
* Error Message: <Exact validation message from solution.>

**Display<Entities>():**
Displays all <entity> records in the list.
* **Access Modifier:** public
* **Declaration Modifier:** static
* **Return Type:** void
* Success Message: Prints each <entity>'s details in the format: "Name: {Name}, Department: {Department}, ..." (adapt to actual properties).
* Error Message: "No <entities> in the records." (if the list is empty).

**Update<Entity>Record(string oldName, <Entity> updatedEntity):** (or equivalent signature)
Updates the details of an existing <entity> based on the provided key (e.g. name).
* **Access Modifier:** public
* **Declaration Modifier:** static
* **Return Type:** void
* Success Message: "<Entity> record updated successfully."
* Error Message: "No matching <entity> record found."

**Delete<Entity>Record(string entityName):** (or equivalent signature)
Removes an <entity> record from the list based on the provided key.
* **Access Modifier:** public
* **Declaration Modifier:** static
* **Return Type:** void
* Success Message: "<Entity> record deleted successfully."
* Error Message: "No matching <entity> record found."

**Menu Options:**
1. **Add <Entity> Record:** <One line.>
2. **Display <Entities>:** <One line.>
3. **Update <Entity> Record:** <One line.>
4. **Delete <Entity> Record:** <One line.>
5. **Exit:** Exits the application with the message "Exiting the application...".
### Any invalid input results in the message: "Invalid choice."

**Sample Output:**
Add:
Display:
Update:
Delete:
Exit:

**Commands to Run the Project:**
* **cd dotnetapp** — Select the dotnet project folder
* **dotnet run** — To run the application
* **dotnet build** — To build and check for errors
* **dotnet clean** — If any error persists, clean the project and build again.
""",

    "dotnet_console": """
You MUST produce the description in this structure (ADO.NET Console — use dotnet_console_ado template structure).
1. **Problem Statement** / **Objective**
2. **Folder Structure** (if needed)
3. **Table** / **Classes and Properties**
4. **Database Details**
5. **Methods** (full spec: parameters, return type, console messages)
6. **Main Menu**
7. **Commands to Run**
8. **Notes** / **Sample Output**
""",

    "dotnet_mvc": """
You MUST produce the description in this structure (.NET MVC).

1. **Title** — Problem Statement
2. **Problem Statement** — ASP.NET Core MVC app description
3. **Models** — Classes and properties
4. **Controllers** — Actions, views, routes
5. **Views** — Pages and behavior
6. **Endpoints / Routes**
7. **Status Codes and Error Handling**
8. **Commands to Run**
9. **Notes**
""",

    "generic": """
You MUST produce the description in this structure (generic).

1. **Problem Statement**
2. **Objective**
3. **Classes and Properties**
4. **Methods / Endpoints**
5. **Expected Behavior** (console or API responses)
6. **Commands to Run** (if applicable)
7. **Notes**
""",
}


def _detect_project_stack(workspace_path: str, solution_files: Dict[str, str]) -> str:
    """
    Detect project type from workspace structure and file content.
    Returns one of: dotnet_webapi, dotnet_console, dotnet_console_ado,
    dotnet_console_collection, dotnet_mvc, generic.

    NOTE: This is heuristic-based and intentionally conservative:
    - Only classify as .NET Web API / MVC / ADO.NET console when we see
      clear signals (AspNetCore, DbContext, SqlConnection, SqlDataAdapter, etc.).
    - For other stacks or ambiguous C# projects, fall back to "generic" so the
      description uses the safe generic template instead of a wrong .NET-specific one.
    """
    # Quick language / file-type check
    paths = list(solution_files.keys())
    paths_lower = " ".join(paths).lower()
    content_snapshot = " ".join(solution_files.values())[:20000].lower()

    has_cs = any(p.lower().endswith(".cs") for p in paths)
    has_java = any(p.lower().endswith(".java") for p in paths)
    has_ts = any(p.lower().endswith(".ts") for p in paths)
    has_js = any(p.lower().endswith(".js") for p in paths)
    has_py = any(p.lower().endswith(".py") for p in paths)

    # Non-.NET stacks → generic
    if not has_cs:
        return "generic"

    # ── Detect ASP.NET Web API / MVC ─────────────────────────────────────
    # Web API signals
    has_aspnetcore = "microsoft.aspnetcore.mvc" in content_snapshot
    has_apicontroller = "[apicontroller]" in content_snapshot
    has_http_attrs = any(tag in content_snapshot for tag in ["[httpget", "[httppost", "[httpput", "[httpdelete"])
    has_api_route = 'route("api/' in content_snapshot or 'route(" api/' in content_snapshot
    in_controllers_folder = "controllers" in paths_lower

    # MVC (views) signals
    has_viewresult = "viewresult" in content_snapshot
    has_return_view = "return view(" in content_snapshot

    if in_controllers_folder or has_aspnetcore or has_http_attrs or has_apicontroller:
        if has_viewresult or has_return_view:
            return "dotnet_mvc"
        # Default ASP.NET controller style to Web API when not clearly MVC
        return "dotnet_webapi"

    # EF Core / DbContext strongly suggests Web API / backend service
    if "dbcontext" in content_snapshot or "applicationdbcontext" in content_snapshot:
        return "dotnet_webapi"

    # ── Detect Console apps (ADO.NET vs in-memory collection) ────────────
    has_program_cs = "program.cs" in paths_lower
    if has_program_cs:
        # ADO.NET / database console signals
        has_ado = any(
            marker in content_snapshot
            for marker in [
                "sqldataadapter",
                "dataset",
                "datatable",
                "sqlconnection",
                "sqlcommand",
                "system.data.sqlclient",
                "connectionstringprovider",
            ]
        )
        # Collection-based console: List<T>, Console.WriteLine, but no strong ADO markers
        has_collection = (
            "list<" in content_snapshot
            or "list <" in content_snapshot
        )

        if has_ado:
            return "dotnet_console_ado"
        if has_collection and not has_ado:
            return "dotnet_console_collection"
        # Console but unclear: treat as generic console template (lighter)
        return "dotnet_console"

    # Fallback for unknown C# projects → generic description
    return "generic"


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """You are a Project Description Generator. Your task is to produce an academic, exam-style problem statement that a student can use to implement the solution and pass all tests.

PROCESS:
1. Read and understand ALL solution files (business logic, classes, methods, properties, relationships).
2. Read and understand ALL test files (expected behavior, console messages, status codes, validations, exception handling).
3. Use the TEMPLATE provided for this project type — follow its section order and structure EXACTLY.
4. Produce a single structured markdown description in ONE pass.

EXHAUSTIVE DOCUMENTATION (MANDATORY — DO NOT OMIT ANYTHING):
- The description MUST document EVERY public method that appears in the solution code: correct method name, parameters (names and types), return type, and behavior. Tests expect these methods to exist; if the description omits a method, the student will not implement it and tests will fail.
- The description MUST document EVERY public property of every model/class in the solution (name, type, and brief description). Tests may assert on property names via reflection.
- The description MUST include every console message string, menu text, prompt text, and error/success message that appears in the solution or that the tests assert on (e.g. substring checks, expected output). Use the exact strings from the code or tests.
- Do NOT document only "sample" or "example" methods from the template. Extract and list EVERY method and property from the SOLUTION FILES and ensure every behavior/string the TEST FILES rely on is described. If the solution has 7 methods, the description must list all 7 with correct signatures and behavior.
- Cross-check: any method or property that the test code references (e.g. GetMethod, GetProperty, expected output strings) MUST appear in the description with the same name and contract.

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
- Clearly define models (classes and properties with types and descriptions).
- Clearly define controller methods (purpose, parameters, status codes, validations).
- Clearly describe expected API responses and exception handling.
- Follow the TEMPLATE structure for the detected project type — same headings, same order.

FORMAT:
- Use **bold** for headings and key terms.
- Use bullet points for properties and options.
- Describe behavior in plain language, never with code.
- No code fences, no inline code, no syntax.
"""

# Legacy single prompt (no template injection) — kept for fallback
SYSTEM_PROMPT = SYSTEM_PROMPT_BASE + """

TEMPLATE — ADO.NET CONSOLE: Title, Objective, Folder Structure, Table Details, Classes and Properties, Database Details, Methods, Main Menu, Commands to Run, Notes.
TEMPLATE — WEB API: Title, Problem Statement, Models, DbContext, Controllers and methods, Endpoints, Status Codes and Error Handling, Exceptions, Commands to Run, Notes.
TEMPLATE — GENERIC: Problem Statement, Objective, Classes and Properties, Methods, Expected Behavior, Notes.
"""


def _build_system_prompt(stack: str) -> str:
    """Build system prompt with the template for the detected stack."""
    template = DESCRIPTION_TEMPLATES.get(stack, DESCRIPTION_TEMPLATES["generic"])
    return (
        SYSTEM_PROMPT_BASE
        + "\n\n--- STRUCTURE TO FOLLOW (use this exact order and section names) ---\n"
        + template
        + "\n\n--- END TEMPLATE ---\n"
    )


def _build_user_prompt(solution_files: Dict[str, str], test_files: Dict[str, str]) -> str:
    parts = [
        "Analyze the following solution and test files, then produce the project description "
        "following the TEMPLATE structure you were given. Do not skip any section.\n\n"
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
        "Output the description directly.\n\n"
        "REMINDER: Document EVERY method and EVERY property from the solution files above, with correct names, "
        "parameters, return types, and behavior. Include every console/API message string that the tests expect. "
        "Omit nothing that appears in the solution or that the tests rely on."
    )
    return "".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def _paths_to_file_contents(workspace_path: str, paths: List[str]) -> Dict[str, str]:
    """Build path -> content dict from a list of paths (files or dirs) relative to workspace."""
    out: Dict[str, str] = {}
    for p in paths:
        p = p.strip()
        if not p:
            continue
        full = os.path.join(workspace_path, p) if not os.path.isabs(p) else p
        if not os.path.exists(full):
            continue
        if os.path.isfile(full):
            if full.endswith(CODE_EXTS):
                out[full] = _read_file(full)
        else:
            for fp in _walk_code_files(full):
                out[fp] = _read_file(fp)
    return out


def generate_project_description(
    workspace_path: str,
    reference_description_path: Optional[str] = None,
    output_filename: str = "PROJECT_DESCRIPTION.md",
    llm=None,
    stack: Optional[str] = None,
    solution_paths: Optional[List[str]] = None,
    test_paths: Optional[List[str]] = None,
) -> Dict:
    """
    Generate a project description using an LLM.
    Reads solution and test files (from provided paths or auto-discovered), sends to LLM, writes the response to file.

    Args:
        workspace_path: Root of the project.
        reference_description_path: Ignored (kept for compatibility).
        output_filename: Output file name.
        llm: Optional LangChain LLM instance. If None, creates AzureChatOpenAI from env.
        stack: Optional explicit stack/template key. When None, auto-detected from code.
        solution_paths: Optional list of paths (relative to workspace_path or absolute). Each can be a file or
                       directory. If provided, only these paths are read for solution content; otherwise
                       solution dirs are auto-discovered.
        test_paths: Optional list of paths for test content. If provided, only these are read; otherwise
                    test dirs are auto-discovered.
    """
    result = {
        'success': False,
        'output_path': '',
        'solution_files': [],
        'stack': 'generic',
        'classes_documented': 0,
        'methods_documented': 0,
        'cache_summary': '',
        'errors': []
    }

    try:
        # 1. Get solution and test file contents (from provided paths or auto-discover)
        if solution_paths:
            solution_files = _paths_to_file_contents(workspace_path, solution_paths)
        else:
            solution_dirs, test_dirs = _find_solution_and_test_dirs(workspace_path)
            solution_files = {}
            for d in solution_dirs:
                for fp in _walk_code_files(os.path.join(workspace_path, d)):
                    solution_files[fp] = _read_file(fp)

        result['solution_files'] = [os.path.relpath(p, workspace_path) for p in solution_files]

        if test_paths:
            test_files = _paths_to_file_contents(workspace_path, test_paths)
            # Remove any that were already in solution (e.g. if agent passed overlapping dirs)
            for fp in list(test_files.keys()):
                if fp in solution_files:
                    del test_files[fp]
        else:
            test_dirs = _find_solution_and_test_dirs(workspace_path)[1]
            test_files = {}
            for d in test_dirs:
                for fp in _walk_code_files(os.path.join(workspace_path, d)):
                    if fp not in solution_files:
                        test_files[fp] = _read_file(fp)

        if not solution_files:
            result['errors'].append("No solution files found")
            return result

        # 4. Detect stack and build stack-specific prompt (allow explicit override)
        if stack:
            # Normalize and trust only known template keys
            normalized = stack.strip().lower()
            resolved_stack = normalized if normalized in DESCRIPTION_TEMPLATES else "generic"
        else:
            resolved_stack = _detect_project_stack(workspace_path, solution_files)
        result['stack'] = resolved_stack
        system_prompt = _build_system_prompt(resolved_stack)
        user_prompt = _build_user_prompt(solution_files, test_files)
        if llm is None:
            llm = _get_description_llm()

        messages = [
            SystemMessage(content=system_prompt),
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
