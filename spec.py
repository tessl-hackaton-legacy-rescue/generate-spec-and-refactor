import argparse
import os
import subprocess
import sys
import json

def main():
    """
    Main function to drive the rule generation process.
    """
    parser = argparse.ArgumentParser(
        description="Analyze a Git repository and generate a rules.json file using Gemini."
    )
    parser.add_argument(
        "directory",
        help="The absolute path to the Git repository to be evaluated.",
    )
    args = parser.parse_args()

    repo_path = args.directory

    # --- 1. Validate the Target Directory ---
    if not os.path.isdir(repo_path):
        print(f"Error: The specified path is not a valid directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"Error: The directory '{repo_path}' is not a Git repository.", file=sys.stderr)
        sys.exit(1)

    # --- 2. Define the Prompt ---
    prompt = """
Evaluate the project and generate a rules.json file.
Output in a JSON collection of objects following the format: id, category, title.

Categories can be:
- language
- framework
- build_tool
- code_style
- test_coverage
- cicd
- third_party (e.g., events, telemetry, logging, etc.)

Your output MUST be a single JSON array. Do not include any other text, explanations, or markdown fences.
"""

    # --- 3. Execute Gemini Command ---
    print(f"Analyzing repository at '{repo_path}' to generate rules.json...")
    try:
        command = ["gemini"]
        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path  # Execute the command in the repo's directory
        )

        # --- 4. Clean and Save the Output ---
        cleaned_output = result.stdout.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[len("```json"):
].lstrip()
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-len("```")].rstrip()

        # Validate that the output is valid JSON before saving
        try:
            rules_data = json.loads(cleaned_output)
            # Pretty-print the JSON for better readability
            formatted_json = json.dumps(rules_data, indent=2)
        except json.JSONDecodeError as e:
            print(f"Error: Gemini output was not valid JSON. Cannot create rules.json. Error: {e}", file=sys.stderr)
            print(f"Raw output:\n{result.stdout}", file=sys.stderr)
            sys.exit(1)

        output_filename = "rules.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(formatted_json)

        print(f"\nSuccessfully generated '{output_filename}'.")

    except FileNotFoundError:
        print("Error: 'gemini' command not found. Make sure it is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("Error while generating rules:", file=sys.stderr)
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
