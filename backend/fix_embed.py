import re

# Fix enhanced_rag_service.py
filepath = 'app/services/enhanced_rag_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'result = genai.embed_content(' in line and i > 0:
        # Check if this is inside generate_embedding
        prev_lines = ''.join(lines[max(0,i-10):i])
        if 'def generate_embedding' in prev_lines and 'gemini_key_manager' not in prev_lines:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + '# Configure API key before embedding generation\n')
            new_lines.append(indent + 'from app.services.gemini_key_manager import gemini_key_manager\n')
            new_lines.append(indent + 'api_key = gemini_key_manager.get_available_key()\n')
            new_lines.append(indent + 'genai.configure(api_key=api_key)\n')
            new_lines.append(indent + '\n')
    new_lines.append(line)
    i += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed enhanced_rag_service.py')

# Fix gemini_service.py
filepath = 'app/services/gemini_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'result = genai.embed_content(' in line and i > 0:
        prev_lines = ''.join(lines[max(0,i-10):i])
        if 'def generate_embedding' in prev_lines and 'gemini_key_manager' not in prev_lines:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + '# Configure API key before embedding generation\n')
            new_lines.append(indent + 'from app.services.gemini_key_manager import gemini_key_manager\n')
            new_lines.append(indent + 'api_key = gemini_key_manager.get_available_key()\n')
            new_lines.append(indent + 'genai.configure(api_key=api_key)\n')
            new_lines.append(indent + '\n')
    new_lines.append(line)
    i += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed gemini_service.py')
