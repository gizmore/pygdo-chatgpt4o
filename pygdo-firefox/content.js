const CHAT_SELECTOR = '[data-message-author-role="user"]';
const INPUT_SELECTOR = 'textarea';
const FILE_TO_PYGDO = '/tmp/to_pygdo.txt'; // Path where user messages are written
const FILE_FROM_PYGDO = '/tmp/from_pygdo.txt'; // Path where PyGDO writes responses

// Function to capture user messages and write to file
function captureMessages() {
    const messages = document.querySelectorAll(CHAT_SELECTOR);
    if (messages.length === 0) return;

    let lastMessage = messages[messages.length - 1].innerText;
    fetch('http://py.giz.orh/chatgpt4o.fromchappy.txt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file: FILE_TO_PYGDO, content: lastMessage })
    });
}

// Function to read responses from file and insert into chat
async function insertResponse() {
    try {
        let response = await fetch('http://localhost:5000/read?file=' + FILE_FROM_PYGDO);
        let text = await response.text();
        if (!text.trim()) return;

        let inputField = document.querySelector(INPUT_SELECTOR);
        if (inputField) {
            inputField.value = text;
            inputField.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(() => {
                document.querySelector('button[type="submit"]').click();
            }, 500);
        }
    } catch (e) {
        console.error('Error reading response:', e);
    }
}

// Observer to track new messages
const observer = new MutationObserver(captureMessages);
observer.observe(document.body, { childList: true, subtree: true });

// Periodic check for new responses
setInterval(insertResponse, 3000);
