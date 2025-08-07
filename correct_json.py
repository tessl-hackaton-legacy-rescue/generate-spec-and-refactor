def clean_json_file(filepath: str) -> None:
    """
    Reads a file, removes JSON markdown fences ('```json' and '```'),
    and saves the cleaned content back to the same file.

    Args:
        filepath: The path to the file to be cleaned.
    """
    try:
        # Step 1: Read the entire file content
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        # Step 2: Remove leading/trailing whitespace and the markdown fences
        # The .strip() calls handle any newlines or spaces around the fences
        cleaned_content = content.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content.removeprefix('```json')
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content.removesuffix('```')
        
        # Final strip to ensure the JSON is clean
        cleaned_content = cleaned_content.strip()

        # Step 3: Write the cleaned content back to the file, overwriting it
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(cleaned_content)

        print(f"✅ File '{filepath}' has been cleaned successfully.")

    except FileNotFoundError:
        print(f"❌ Error: The file '{filepath}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# --- Example Usage ---
# Assume you have a file named 'data.json' with the following content:
#
# ```json
# {
#     "name": "Example Data",
#     "value": 42
# }
# ```
#
# You would call the function like this:
# clean_json_file('data.json')