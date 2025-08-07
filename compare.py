import argparse
import os
import subprocess
import sys
import json
import glob

def generate_html_report(reports_path, rules):
    """
    Generates a single HTML summary report from a directory of JSON reports.
    """
    print("\n--- Generating HTML Summary Report ---")

    # Find all JSON report files
    report_files = glob.glob(os.path.join(reports_path, '*-report.json'))

    if not report_files:
        print("Warning: No JSON report files found to generate an HTML summary.", file=sys.stderr)
        return

    # Load report data
    reports = []
    for report_file in report_files:
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                reports.append(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read or parse report file '{report_file}'. Skipping. Error: {e}", file=sys.stderr)
            continue

    # Sort reports by repoName to ensure consistent column order
    reports.sort(key=lambda x: x.get('repoName', ''))

    # Start HTML generation
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800">
    <div class="container mx-auto p-8">
        <h1 class="text-3xl font-bold mb-8 text-center">Compliance Report</h1>
        <div class="overflow-x-auto">
            <table class="min-w-full bg-white border border-gray-200 shadow-md rounded-lg">
                <thead class="bg-gray-200">
                    <tr>
                        <th class="py-3 px-4 border-b border-gray-300 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">Rule</th>
"""
    # Add repo names to header
    for report in reports:
        repo_name = report.get("repoName", "Unnamed Repo")
        html += f'<th class="py-3 px-4 border-b border-gray-300 text-center text-sm font-semibold text-gray-600 uppercase tracking-wider">{repo_name}</th>'

    html += """
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
"""
    # Add rules and results to table
    for rule in rules:
        html += f'<tr><td class="py-4 px-4 border-b border-gray-300 text-sm">{rule.get("title", "Untitled Rule")}</td>'
        for report in reports:
            result_symbol = "❓"  # Default: Not found
            for check in report.get('checks', []):
                if check.get('id') == rule.get('id'):
                    result = check.get('result', '').lower()
                    if result == 'pass':
                        result_symbol = "✅"
                    elif result == 'fail':
                        result_symbol = "❌"
                    break
            html += f'<td class="py-4 px-4 border-b border-gray-300 text-center text-2xl">{result_symbol}</td>'
        html += '</tr>'

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    # Save the HTML file
    html_report_path = os.path.join(reports_path, 'index.html')
    try:
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Successfully generated HTML report: {html_report_path}")
    except IOError as e:
        print(f"Error: Could not write HTML report file. {e}", file=sys.stderr)

def run_evaluation(args):
    """
    Scans Git repositories, generates individual JSON reports, and then creates a summary HTML report.
    """
    # --- 1. Setup and Pre-checks ---
    reports_dir = args.reports_path
    try:
        os.makedirs(reports_dir, exist_ok=True)
        print(f"Reports will be saved in the '{reports_dir}/' directory.")
    except OSError as e:
        print(f"Error: Could not create reports directory '{reports_dir}'. {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.rules_path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        print(f"Successfully loaded rules from '{args.rules_path}'.")
    except FileNotFoundError:
        print(f"Error: Rules file not found at '{args.rules_path}'", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Could not read or parse rules file '{args.rules_path}'. It must be a valid JSON file. {e}", file=sys.stderr)
        sys.exit(1)

    rules_content_for_prompt = json.dumps(rules, indent=2)
    base_prompt = f'''
Evaluate this source code base folder based on the rules provided below.
Do not focus on the business logic.

Your output MUST be a single JSON object. Do not include any other text, explanations, or markdown fences.
The JSON object must have the following structure:
- "repoName": A string with the name of the repository.
- "overview": A brief, one-sentence summary of the repository's compliance.
- "checks": An array of check objects, one for each rule.

Each object in the the "checks" array must have this structure:
- "id": The "id" of the rule being checked (e.g., "rule-1").
- "result": A string, either "pass" or "fail".
- "reason": A brief explanation for the result.

--- RULES ---
{rules_content_for_prompt}
'''

    # --- 2. Iterate and Process Repositories ---
    if not os.path.isdir(args.repository_base_path):
        print(f"Error: The specified repository base path is not a valid directory: {args.repository_base_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\nScanning for repositories in '{args.repository_base_path}'...")

    repo_list = [d for d in os.listdir(args.repository_base_path) if os.path.isdir(os.path.join(args.repository_base_path, d))]

    for repo_name in repo_list:
        repo_path = os.path.join(args.repository_base_path, repo_name)
        git_dir = os.path.join(repo_path, ".git")

        if os.path.isdir(git_dir):
            print(f"\n--- Found Git repository: {repo_name} ---")
            try:
                # --- 3. Execute Gemini Command ---
                print(f"Evaluating '{repo_name}'...")
                # Inject the specific repo name into the prompt
                prompt_with_repo_name = f'{{"repoName": "{repo_name}"}}\n{base_prompt}'
                command = ["gemini", prompt_with_repo_name]

                result = subprocess.run(
                    command,
                    input=base_prompt,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repo_path
                )

                # --- 4. Clean and Save the Report ---
                report_filename = f"{repo_name}-report.json"
                report_path = os.path.join(reports_dir, report_filename)

                cleaned_output = result.stdout.strip()
                if cleaned_output.startswith("```json"):
                    cleaned_output = cleaned_output[len("```json"):
].lstrip()
                if cleaned_output.endswith("```"):
                    cleaned_output = cleaned_output[:-len("```")].rstrip()

                # Validate that the output is valid JSON before saving
                try:
                    json.loads(cleaned_output)
                except json.JSONDecodeError as e:
                    print(f"Error: Gemini output for '{repo_name}' was not valid JSON. Skipping. Error: {e}", file=sys.stderr)
                    print(f"Raw output:\n{result.stdout}", file=sys.stderr)
                    continue

                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_output)

                print(f"Successfully generated JSON report for '{repo_name}'.")

            except FileNotFoundError:
                print("Error: 'gemini' command not found. Make sure it is installed and in your PATH.", file=sys.stderr)
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Error while evaluating repository '{repo_name}':", file=sys.stderr)
                print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
                print(f"Stderr:\n{e.stderr}", file=sys.stderr)
            except Exception as e:
                print(f"An unexpected error occurred while processing '{repo_name}': {e}", file=sys.stderr)
        else:
            print(f"Skipping '{repo_name}' (not a Git repository).")

    # --- 5. Generate the final HTML report ---
    generate_html_report(reports_dir, rules)

    print("\n--- Evaluation and reporting complete. ---")

def main():
    """
    Main entry point to drive the script.
    """
    parser = argparse.ArgumentParser(
        description="Run a compliance check on repositories and generate a summary HTML report."
    )
    parser.add_argument("repository_base_path", help="Absolute path to the directory of Git repositories.")
    parser.add_argument("rules_path", help="Path to the JSON file with evaluation rules.")
    parser.add_argument("--reports_path", default="reports", help="Directory to save all reports (JSON and HTML). Default: 'reports'.")

    args = parser.parse_args()
    run_evaluation(args)

if __name__ == "__main__":
    main()
