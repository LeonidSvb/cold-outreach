const { execSync } = require('child_process');

// Try to find Python in multiple ways
console.log('Searching for Python executable...\n');

const commands = [
  'python --version',
  'python3 --version',
  'where python',
  'where python3'
];

for (const cmd of commands) {
  try {
    console.log(`Trying: ${cmd}`);
    const result = execSync(cmd, { encoding: 'utf-8' });
    console.log(`SUCCESS: ${result}\n`);
  } catch (e) {
    console.log(`FAILED: ${e.message}\n`);
  }
}

// Try registry lookup on Windows
try {
  console.log('Checking Windows registry for Python...\n');
  const regCmd = 'reg query HKEY_LOCAL_MACHINE\\SOFTWARE\\Python /s /v InstallPath';
  const result = execSync(regCmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] });
  console.log('Registry results:\n', result);
} catch (e) {
  console.log('No registry entries found');
}
