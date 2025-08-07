import os
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Make sure this import points to the file with your Pydantic classes
from specification import RepositoryAnalysis

# --- CONFIG ---
SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.go', '.cpp', '.gradle', '.pom.xml', 'package.json')
MAX_FILE_CHARS = 10000  # Max characters to read from the beginning of a file


# --- READ FILES ---
def read_code_files(repo_path):
    """Reads the content of supported files in a directory."""
    file_contents = []
    print(f"🔍 Reading files from '{repo_path}'...")
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read(MAX_FILE_CHARS)
                        rel_path = os.path.relpath(full_path, repo_path)
                        file_contents.append((rel_path, content))
                except Exception as e:
                    print(f"⚠️ Could not read file {file}: {e}")
    print(f"Read {len(file_contents)} files.")
    return file_contents


# --- BUILD PROMPT INPUT ---
def build_repo_context(files):
    """Formats the file contents into a single string for the prompt."""
    context = []
    for filename, content in files:
        context.append(f"### File: {filename}\n```\n{content}\n```\n")
    return "\n".join(context)


# --- MAIN ---
def main():
    parser = argparse.ArgumentParser(description="Analyze a code repository and generate a JSON specification.")
    parser.add_argument('--api-key', required=True, help='Google Gemini API Key')
    parser.add_argument('--repo-path', required=True, help='Path to the local code repository.')
    parser.add_argument('--prompt-file', required=True,
                        help='Path to the file containing the base prompt instructions.')
    parser.add_argument('--output-file', default='repository_analysis.json', help='Name of the output JSON file.')
    args = parser.parse_args()

    os.environ["GOOGLE_API_KEY"] = args.api_key

    # 1. Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.2,  # Lower temperature for more deterministic JSON output
    )

    # 2. Set up the Pydantic parser
    pydantic_parser = PydanticOutputParser(pydantic_object=RepositoryAnalysis)

    # 3. Create a PromptTemplate with formatting instructions
    with open(args.prompt_file, 'r', encoding='utf-8') as f:
        prompt_instructions = f.read().strip()

    prompt_template = PromptTemplate(
        template="{instructions}\n\n{format_instructions}\n\nHere is the codebase to analyze:\n{repo_context}",
        input_variables=["repo_context", "instructions"],
        partial_variables={"format_instructions": pydantic_parser.get_format_instructions()},
    )

    # 4. Create the full processing chain using LCEL
    # The chain pipes the formatted prompt to the LLM, and the LLM's output to the parser
    chain = prompt_template | llm | pydantic_parser

    # Read files and build the context string
    repo_files = read_code_files(args.repo_path)
    repo_context = build_repo_context(repo_files)

    print("▶️ Invoking the analysis chain... (This may take a moment)")

    try:
        # 5. Invoke the chain. The final result is a parsed Pydantic object.
        analysis_result = chain.invoke({
            "repo_context": repo_context,
            "instructions": prompt_instructions
        })

        # 6. Save the Pydantic object as a well-formatted JSON file
        with open(args.output_file, 'w', encoding='utf-8') as f:
            # .model_dump_json() serializes the Pydantic object to a JSON string
            f.write(analysis_result.model_dump_json(indent=2))

        print("\n--- Analysis Complete ---")
        print(f"✅ Specification successfully parsed and saved to '{args.output_file}'")
        print(f"Detected Language: {analysis_result.language.value.name}")
        print(f"Detected Framework: {analysis_result.framework.value.name}")

    except Exception as e:
        print("\n--- An Error Occurred ---")
        print(f"❌ Could not complete the analysis. Error: {e}")


if __name__ == "__main__":
    main()