const fs = require('fs');
const path = require('path');

function readText(filePath, maxChars) {
  try {
    const text = fs.readFileSync(filePath, 'utf8').trim();
    return text.length > maxChars ? text.slice(0, maxChars) : text;
  } catch {
    return '';
  }
}

function getTargetPath(args) {
  if (!args || typeof args !== 'object') return '';
  return String(
    args.Path || args.path || args.TargetFile || args.file_path || args.AbsolutePath || ''
  );
}

function isProtectedFile(filePath) {
  const norm = filePath.replace(/\\/g, '/').toLowerCase();
  return (
    norm === 'agents.md' ||
    norm === '.agents/hooks.json' ||
    norm === '.agents/guard.js' ||
    norm.endsWith('/agents.md') ||
    norm.endsWith('/.agents/hooks.json') ||
    norm.endsWith('/.agents/guard.js')
  );
}

function checkPreToolUse(input) {
  const tool = (input.toolCall && input.toolCall.name) || '';
  const args = (input.toolCall && input.toolCall.args) || {};

  if (tool === 'run_command') {
    const cmd = String(args.CommandLine || args.command || '');
    if (/\bgit\s+push\b.*(\s-f\b|--force\b)/i.test(cmd)) {
      return { decision: 'deny', reason: 'Blocked: force-push is not allowed.' };
    }
    if (/\bgit\s+push\b.*(?:\s|:)(main|master)(?:\s|$)/i.test(cmd)) {
      return { decision: 'deny', reason: 'Blocked: push to a feature branch, never main/master.' };
    }
    if (/(>|rm|del|mv|ren|remove-item|set-content|out-file).*(agents\.md|hooks\.json|guard\.js)/i.test(cmd)) {
      return { decision: 'deny', reason: 'Blocked: only the repo owner may edit AGENTS.md or hooks.' };
    }
    return { decision: 'ask' };
  }

  if (isProtectedFile(getTargetPath(args))) {
    return { decision: 'deny', reason: 'Blocked: only the repo owner may edit AGENTS.md or hooks.' };
  }
  return { decision: 'ask' };
}

function handleSessionStart(root) {
  const agents = readText(path.join(root, 'AGENTS.md'), 6000);
  const memory = readText(path.join(root, 'MEMORY.md'), 4000);
  const parts = [];
  if (agents) parts.push('Follow AGENTS.md strictly:\n' + agents);
  if (memory) parts.push('Current MEMORY.md:\n' + memory);
  if (!parts.length) return {};
  return {
    injectSteps: [{ systemMessage: { systemMessage: parts.join('\n\n') } }]
  };
}

function handlePreInvocation(input, root) {
  const num = Number(input.invocationNum || 0);
  const shortReminder =
    'Reminder: strictly follow AGENTS.md (ELI5, 1 step, no code comments, minimal code, 1 feature/folder, never edit AGENTS.md or main).';
  if (num < 10) {
    return {
      injectSteps: [{ systemMessage: { systemMessage: shortReminder } }]
    };
  }
  if (num === 10 || num % 5 === 0) {
    const agents = readText(path.join(root, 'AGENTS.md'), 6000);
    const msg =
      'Long chat reminder (turn ' + num + '): Save MEMORY.md + DECISIONS.md now, then tell the user to open a New Chat and type "continue".\n\n' +
      agents;
    return {
      injectSteps: [
        {
          systemMessage: {
            systemMessage: msg,
            metadata: {
              user_markdown: 'This chat is getting long. After this step, please click **New Chat** and type `continue` so I stay sharp!'
            }
          }
        }
      ]
    };
  }
  return {
    injectSteps: [
      {
        systemMessage: {
          systemMessage: shortReminder + ' Chat is long (turn ' + num + '): save MEMORY.md + DECISIONS.md and ask user to open New Chat.'
        }
      }
    ]
  };
}

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { raw += chunk; });
process.stdin.on('end', () => {
  try {
    const input = raw ? JSON.parse(raw) : {};
    const root = input.cwd || (input.workspacePaths && input.workspacePaths[0]) || path.resolve(__dirname, '..');
    const event = input.hookEventName || '';
    let out = {};
    if (event === 'PreToolUse') out = checkPreToolUse(input);
    else if (event === 'SessionStart') out = handleSessionStart(root);
    else if (event === 'PreInvocation') out = handlePreInvocation(input, root);
    process.stdout.write(JSON.stringify(out));
  } catch {
    process.stdout.write(JSON.stringify({}));
  }
});
