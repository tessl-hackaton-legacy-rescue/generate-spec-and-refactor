import os
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage

# --- CONFIG ---
SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.go', '.cpp', '.gradle')
MAX_FILE_CHARS = 10000


# --- READ FILES ---
def read_code_files(repo_path):
    file_contents = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()[:MAX_FILE_CHARS]
                        rel_path = os.path.relpath(full_path, repo_path)
                        file_contents.append((rel_path, content))
                except Exception as e:
                    print(f"Could not read {file}: {e}")
    return file_contents


# --- BUILD PROMPT INPUT ---
def build_repo_context(files):
    context = []
    for filename, content in files:
        context.append(f"\n### File: {filename}\n{content}\n")
    return "\n".join(context)


# --- MAIN ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', required=True, help='Gemini API Key')
    parser.add_argument('--repo-path', required=True)
    parser.add_argument('--prompt-file', required=True)
    parser.add_argument('--output-file', default='spec_from_langchain.txt')
    args = parser.parse_args()

    os.environ["GOOGLE_API_KEY"] = args.api_key

    # Init LangChain LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
    )

    # Read prompt and files
    with open(args.prompt_file, 'r', encoding='utf-8') as f:
        user_prompt = f.read().strip()

    repo_files = read_code_files(args.repo_path)
    context = build_repo_context(repo_files)

    # Compose final prompt
    full_prompt = f"""{user_prompt}

Below is the codebase:

{context}
"""

    # Run via LangChain
    response = llm.invoke([HumanMessage(content=full_prompt)])

    # Save result
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(response.content)

    print(f"✅ Specification saved to {args.output_file}")


if __name__ == "__main__":
    main()
