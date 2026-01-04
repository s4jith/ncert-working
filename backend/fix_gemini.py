filepath = 'app/services/gemini_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert API key configuration before line 70 (index 69)
# Line 69 is "        try:"
# Line 70 is "            result = genai.embed_content("
insert_at = 69  # After "try:", before "result = genai.embed_content("
indent = '            '  # 12 spaces to match the indentation

new_lines = (
    lines[:insert_at] +
    [indent + '# Configure API key before embedding generation\n',
     indent + 'from app.services.gemini_key_manager import gemini_key_manager\n',
     indent + 'api_key = gemini_key_manager.get_available_key()\n',
     indent + 'genai.configure(api_key=api_key)\n',
     indent + '\n'] +
    lines[insert_at:]
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed gemini_service.py!')
