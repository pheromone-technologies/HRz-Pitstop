const fs = require('fs');
const code = fs.readFileSync('js/menu.js', 'utf8').split('\n').slice(0, 100).join('\n');
const strMatches = code.match(/(?:"([^"]+)")|(?:'([^']+)')/g);
const terms = new Set();
strMatches.forEach(s => {
    let clean = s.replace(/["']/g, '');
    if (clean.length > 2 && !clean.includes('images/') && !clean.includes('.webp')) {
        terms.add(clean);
    }
});
const products = JSON.parse(fs.readFileSync('data/products.json', 'utf8'));
let zeroCount = 0;
console.log('Menu Item | Matching Products\n-----------------------------------------');
terms.forEach(term => {
    let termLower = term.toLowerCase();
    let match = 0;
    for (let p of products) {
        if ((p.category && p.category.toLowerCase().includes(termLower)) ||
            (p.name && p.name.toLowerCase().includes(termLower)) ||
            (p.sku && p.sku.toLowerCase().includes(termLower))) {
            match++;
        }
    }
    if (match === 0) {
        zeroCount++;
        console.log(term.padEnd(30) + ' | 0');
    }
});
console.log('\nTotal menu items audited:', terms.size);
console.log('Menu items with 0 matches:', zeroCount);

