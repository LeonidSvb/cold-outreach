const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const pythonExe = 'C:\\Users\\79818\\AppData\\Local\\Microsoft\\WindowsApps\\python3.exe';
const scriptPath = path.join(__dirname, 'icebreaker_simple.py');
const logDir = path.join(__dirname, 'data', 'processed');

console.log('Using execFileSync to run Python directly...\n');
console.log(`Python: ${pythonExe}`);
console.log(`Script: ${scriptPath}\n`);

if (!fs.existsSync(pythonExe)) {
  console.error(`ERROR: Python not found at ${pythonExe}`);
  process.exit(1);
}

// Ensure log dir exists
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

try {
  console.log('Starting execution...\n');

  const output = execFileSync(pythonExe, [scriptPath], {
    cwd: __dirname,
    encoding: 'utf-8',
    maxBuffer: 10 * 1024 * 1024,
    stdio: ['pipe', 'pipe', 'pipe']
  });

  console.log('STDOUT:');
  console.log(output);

  // Try to read and display the log file
  const logFile = path.join(logDir, 'icebreaker_generator.log');
  if (fs.existsSync(logFile)) {
    console.log('\n' + '='.repeat(60));
    console.log('LOG FILE CONTENTS:');
    console.log('='.repeat(60) + '\n');
    try {
      const logContent = fs.readFileSync(logFile, 'utf-8');
      console.log(logContent);
    } catch (e) {
      console.error(`Could not read log file: ${e.message}`);
    }
  }

  process.exit(0);
} catch (error) {
  console.error('ERROR:', error.message);

  if (error.stderr) {
    console.error('\nSTDERR:', error.stderr);
  }

  if (error.stdout) {
    console.error('\nSTDOUT:', error.stdout);
  }

  // Try to read log file anyway
  const logFile = path.join(logDir, 'icebreaker_generator.log');
  if (fs.existsSync(logFile)) {
    console.log('\nLog file exists, attempting to read...\n');
    try {
      const logContent = fs.readFileSync(logFile, 'utf-8');
      console.log(logContent);
    } catch (e) {
      console.error(`Could not read log file: ${e.message}`);
    }
  }

  process.exit(error.status || 1);
}
