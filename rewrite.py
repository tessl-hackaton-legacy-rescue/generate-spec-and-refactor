import argparse
import os
import subprocess
import sys

def main():
    """
    Main function to drive the repository rewriting process.
    """
    parser = argparse.ArgumentParser(
        description="Rewrite a Git repository based on a set of rules using Gemini."
    )
    parser.add_argument(
        "repository_path",
        help="The absolute path to the Git repository to be rewritten.",
    )
    parser.add_argument(
        "rules_path",
        help="The path to the file containing the rewrite rules.",
    )
    args = parser.parse_args()

    repo_path = args.repository_path
    rules_path = args.rules_path

    # --- 1. Validate Paths ---
    if not os.path.isdir(repo_path):
        print(f"Error: The specified repository path is not a valid directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"Error: The directory '{repo_path}' is not a Git repository.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_content = f.read()
        print(f"Successfully loaded rules from '{rules_path}'.")
    except FileNotFoundError:
        print(f"Error: Rules file not found at '{rules_path}'", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error: Could not read rules file '{rules_path}'. {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Construct the Prompt ---
    base_prompt = "Rewrite the source code in current directory according to provided rules"
    full_prompt = f"{base_prompt}\n\n--- RULES ---\n{rules_content}"

    # --- 3. Execute Gemini Command ---
    print(f"\nExecuting Gemini in '{repo_path}' to rewrite the repository.")
    print("The output from the Gemini CLI will be displayed below:")
    print("-" * 40)

    try:
        command = ["gemini", "-p", "-y"]
        # We run the command without capturing output so that the Gemini CLI
        # can interact with the user and modify files directly.
        # The prompt is passed to the command's standard input.
        process = subprocess.run(
            command,
            input=full_prompt,
            text=True,
            cwd=repo_path,  # Execute the command in the repo's directory
            check=True,      # This will raise an exception if the command returns a non-zero exit code
        )
        print("-" * 40)
        print("Gemini command finished successfully.")

    except FileNotFoundError:
        print("Error: 'gemini' command not found. Make sure it is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("-" * 40, file=sys.stderr)
        print(f"Error: Gemini command failed with exit code {e.returncode}.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
