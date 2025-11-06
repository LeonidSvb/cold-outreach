const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const scriptPath = path.join(__dirname, 'icebreaker_simple.py');
const logDir = path.join(__dirname, 'data', 'processed');
const command = `cd "${__dirname}" && python "${scriptPath}"`;

console.log('Executing Python script...');
console.log(`Script: ${scriptPath}`);
console.log(`Command: ${command}\n`);

// Ensure log dir exists
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

exec(command, { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
  if (stdout) console.log(stdout);
  if (stderr) console.error(stderr);

  if (error) {
    console.error(`\nError: ${error.message}`);
    process.exit(error.code);
  } else {
    console.log('\nScript completed successfully');

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
  }
});
