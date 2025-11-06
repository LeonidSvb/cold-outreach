const { spawn } = require('child_process');
const path = require('path');

const pythonScript = path.join(__dirname, 'run_icebreaker.py');

console.log('Starting icebreaker generator...');
console.log(`Script: ${pythonScript}`);
console.log('Python: Using system PATH');
console.log('');

// Use 'python' from PATH - it should work from any shell
const python = spawn('python', [pythonScript], {
  stdio: 'inherit',
  cwd: __dirname,
  shell: true,
  // Ensure Python can find modules
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

python.on('close', (code) => {
  console.log(`\nGenerator exited with code ${code}`);
  process.exit(code);
});

python.on('error', (err) => {
  console.error('Error running generator:', err);
  process.exit(1);
});
