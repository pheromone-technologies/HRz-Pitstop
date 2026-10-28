const fs = require('fs');

global.window = { HRz: {} };
require('../js/utils.js');

const products = JSON.parse(fs.readFileSync('data/products.json', 'utf8'));
const results = window.HRz.Utils.smartSearch('Grips and Throttle', products);

console.log('Results count:', results.length);
results.forEach((p, idx) => {
  console.log((idx + 1) + '. [' + p.category + '] ' + p.name + ' - Rs.' + p.price + ' | Image: ' + p.image);
});
