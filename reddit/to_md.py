import json

def json_to_markdown():
    # Read the JSON file
    with open('comment_summaries.json', 'r') as file:
        data = json.load(file)
    
    # Create markdown content
    markdown_content = "# Abstractions\n\n"
    
    for entry in data:
        # Add theme as header
        markdown_content += f"## {entry['theme']}\n\n"
        
        # Add post summary
        markdown_content += f"{entry['post_summary']}\n\n"
        
        # Add comment summary
        markdown_content += f"{entry['comment_summary']}\n\n"
        
        # Add separator between entries
        markdown_content += "---\n\n"
    
    # Write to markdown file
    with open('abstract.md', 'w') as file:
        file.write(markdown_content)

if __name__ == "__main__":
    json_to_markdown()