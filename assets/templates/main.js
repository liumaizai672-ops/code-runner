const data = require('fs').readFileSync(0, 'utf8').trim();

if (data) {
  const tokens = data.split(/\s+/);
  console.log(tokens[0]);
}
