/**
 * Chat Export Utilities
 * 
 * Converts chat messages to downloadable document formats
 */

/**
 * Convert chat messages to formatted text document
 * @param {Array} messages - Array of message objects with role, content, timestamp
 * @param {Object} options - Export options
 * @returns {string} Formatted text content
 */
export function formatChatToText(messages, options = {}) {
  const { 
    title = "Chat Conversation",
    userName = "You",
    aiName = "AI Assistant",
    includeTimestamp = true,
    includeSeparator = true
  } = options;

  let content = "";
  
  // Header
  content += `${"=".repeat(50)}\n`;
  content += `${title}\n`;
  content += `Exported on: ${new Date().toLocaleString()}\n`;
  content += `${"=".repeat(50)}\n\n`;

  // Messages
  messages.forEach((msg, index) => {
    const role = msg.role === "user" ? userName : aiName;
    const timestamp = includeTimestamp 
      ? ` (${new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })})`
      : "";
    
    content += `${role}${timestamp}:\n`;
    content += `${msg.content}\n`;
    
    if (includeSeparator && index < messages.length - 1) {
      content += `\n${"-".repeat(40)}\n\n`;
    } else {
      content += "\n";
    }
  });

  // Footer
  content += `\n${"=".repeat(50)}\n`;
  content += `End of conversation\n`;
  content += `${"=".repeat(50)}\n`;

  return content;
}

/**
 * Convert chat messages to HTML document
 * @param {Array} messages - Array of message objects
 * @param {Object} options - Export options
 * @returns {string} HTML content
 */
export function formatChatToHTML(messages, options = {}) {
  const { 
    title = "Chat Conversation",
    userName = "You",
    aiName = "AI Assistant"
  } = options;

  let html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      background: #f5f5f5;
      color: #333;
    }
    .header {
      text-align: center;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 2px solid #e0e0e0;
    }
    .header h1 {
      margin: 0 0 10px;
      color: #1a1a1a;
    }
    .header p {
      color: #666;
      margin: 0;
    }
    .message {
      margin-bottom: 24px;
      padding: 20px;
      border-radius: 12px;
      background: white;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .message.user {
      border-left: 4px solid #1a1a1a;
    }
    .message.assistant {
      border-left: 4px solid #f97316;
    }
    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .role {
      font-weight: 600;
      font-size: 14px;
    }
    .role.user { color: #1a1a1a; }
    .role.assistant { color: #f97316; }
    .timestamp {
      font-size: 12px;
      color: #999;
    }
    .content {
      line-height: 1.6;
      white-space: pre-wrap;
    }
    .content strong { font-weight: 600; }
    .content ul, .content ol {
      margin: 10px 0;
      padding-left: 24px;
    }
    .content li { margin: 4px 0; }
    .footer {
      text-align: center;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 2px solid #e0e0e0;
      color: #666;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>${title}</h1>
    <p>Exported on ${new Date().toLocaleString()}</p>
  </div>
`;

  messages.forEach(msg => {
    const role = msg.role === "user" ? userName : aiName;
    const roleClass = msg.role;
    const timestamp = new Date(msg.timestamp).toLocaleTimeString([], { 
      hour: "2-digit", 
      minute: "2-digit" 
    });
    
    // Convert markdown-like content to HTML
    let content = msg.content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.*)$/gm, '<li>$1</li>')
      .replace(/^(\d+)\. (.*)$/gm, '<li>$2</li>');

    html += `
  <div class="message ${roleClass}">
    <div class="message-header">
      <span class="role ${roleClass}">${role}</span>
      <span class="timestamp">${timestamp}</span>
    </div>
    <div class="content">${content}</div>
  </div>
`;
  });

  html += `
  <div class="footer">
    <p>End of conversation</p>
  </div>
</body>
</html>`;

  return html;
}

/**
 * Download content as a file
 * @param {string} content - File content
 * @param {string} filename - File name with extension
 * @param {string} mimeType - MIME type of the file
 */
export function downloadAsFile(content, filename, mimeType = "text/plain") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Export chat as text document
 * @param {Array} messages - Chat messages
 * @param {Object} options - Export options
 */
export function exportChatAsText(messages, options = {}) {
  const { filename = "chat-conversation.txt" } = options;
  const content = formatChatToText(messages, options);
  downloadAsFile(content, filename, "text/plain");
}

/**
 * Export chat as HTML document
 * @param {Array} messages - Chat messages
 * @param {Object} options - Export options
 */
export function exportChatAsHTML(messages, options = {}) {
  const { filename = "chat-conversation.html" } = options;
  const content = formatChatToHTML(messages, options);
  downloadAsFile(content, filename, "text/html");
}

/**
 * Export chat as Word-compatible document (.doc)
 * Uses HTML with Word-specific headers for better compatibility
 * @param {Array} messages - Chat messages
 * @param {Object} options - Export options
 */
export function exportChatAsDoc(messages, options = {}) {
  const { 
    filename = "chat-conversation.doc",
    title = "Chat Conversation",
    userName = "You asked",
    aiName = "AI said"
  } = options;

  // Word-compatible HTML with MSO headers
  let doc = `
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <!--[if gte mso 9]>
  <xml>
    <w:WordDocument>
      <w:View>Print</w:View>
      <w:Zoom>100</w:Zoom>
    </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    @page { margin: 1in; }
    body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; line-height: 1.5; }
    h1 { font-size: 18pt; color: #1a1a1a; margin-bottom: 5pt; }
    .date { color: #666; font-size: 10pt; margin-bottom: 20pt; }
    .message { margin-bottom: 20pt; }
    .role { font-weight: bold; font-size: 11pt; margin-bottom: 5pt; }
    .role.user { color: #1a1a1a; }
    .role.ai { color: #ea580c; }
    .content { margin-left: 0; }
    .timestamp { color: #999; font-size: 9pt; margin-top: 5pt; }
    .separator { border-bottom: 1px solid #ddd; margin: 15pt 0; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <p class="date">Exported on ${new Date().toLocaleString()}</p>
  <div class="separator"></div>
`;

  messages.forEach((msg, index) => {
    const role = msg.role === "user" ? userName : aiName;
    const roleClass = msg.role === "user" ? "user" : "ai";
    const timestamp = new Date(msg.timestamp).toLocaleTimeString([], { 
      hour: "2-digit", 
      minute: "2-digit" 
    });
    
    // Convert markdown to simple HTML
    let content = msg.content
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/\*(.*?)\*/g, '<i>$1</i>')
      .replace(/\n/g, '<br>');

    doc += `
  <div class="message">
    <p class="role ${roleClass}">${role}:</p>
    <div class="content">${content}</div>
    <p class="timestamp">${timestamp}</p>
  </div>
`;
    
    if (index < messages.length - 1) {
      doc += `  <div class="separator"></div>\n`;
    }
  });

  doc += `
  <div class="separator"></div>
  <p style="text-align: center; color: #666; font-size: 10pt;">End of conversation</p>
</body>
</html>`;

  downloadAsFile(doc, filename, "application/msword");
}
