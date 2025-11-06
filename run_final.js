const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Use relative path from System32
const pythonCmd = 'python3';
const scriptPath = path.join(__dirname, 'icebreaker_simple.py');
const logDir = path.join(__dirname, 'data', 'processed');

console.log('Running Python script via spawn...\n');
console.log(`Command: ${pythonCmd}`);
console.log(`Script: ${scriptPath}\n`);

// Ensure log dir exists
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

let output = '';
let errOutput = '';

const python = spawn(pythonCmd, [scriptPath], {
  cwd: __dirname,
  shell: true  // Use shell to access PATH properly on Windows
});

python.stdout.on('data', (data) => {
  const str = data.toString();
  process.stdout.write(str);
  output += str;
});

python.stderr.on('data', (data) => {
  const str = data.toString();
  process.stderr.write(str);
  errOutput += str;
});

python.on('close', (code) => {
  console.log(`\nProcess exited with code ${code}\n`);

  // Try to read and display the log file
  const logFile = path.join(logDir, 'icebreaker_generator.log');
  if (fs.existsSync(logFile)) {
    console.log('='.repeat(60));
    console.log('LOG FILE CONTENTS:');
    console.log('='.repeat(60) + '\n');
    try {
      const logContent = fs.readFileSync(logFile, 'utf-8');
      console.log(logContent);
    } catch (e) {
      console.error(`Could not read log file: ${e.message}`);
    }
  } else {
    console.log('No log file found yet');
  }

  process.exit(code);
});

python.on('error', (err) => {
  console.error(`Failed to start process: ${err.message}`);
  process.exit(1);
});
