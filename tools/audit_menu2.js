const fs = require('fs');

const menuCode = fs.readFileSync('js/menu.js', 'utf8');

// The arrays in menu.js look like:
// "BIKE PROTECTION": ["Lock system", "Crash Guard", "Frame Slider", ...],
// "BIKE ESSENTIALS": ["Windshield", "Winglet", "Seat"],
// ...
// Also:
// cards: [{name: "Helmet", search: "Helmets"}, ...]

// Let's use a regex to extract all string literals from the menuData block
const blockMatch = menuCode.match(/static menuData = \{([\s\S]*?)\};\n\n  static/);
if (!blockMatch) {
    console.error("Could not find menuData block");
    process.exit(1);
}
const block = blockMatch[1];
const strMatches = block.match(/(?:"([^"]+)")|(?:'([^']+)')/g);
const terms = new Set();
strMatches.forEach(s => {
    let clean = s.replace(/["']/g, '');
    if (clean && clean.length > 2 && !clean.includes('images/') && !clean.includes('.webp') && !clean.includes('.webp')) {
        terms.add(clean);
    }
});

const products = JSON.parse(fs.readFileSync('data/products.json', 'utf8'));

const report = [];

terms.forEach(term => {
    const termLower = term.toLowerCase();
    let matchCount = 0;
    
    for (const p of products) {
        if ((p.category && p.category.toLowerCase().includes(termLower)) ||
            (p.name && p.name.toLowerCase().includes(termLower)) ||
            (p.sku && p.sku.toLowerCase().includes(termLower))) {
            matchCount++;
        }
    }
    report.push({ term, matchCount });
});

report.sort((a, b) => a.matchCount - b.matchCount);

console.log("Menu Item | Matching Products");
console.log("-----------------------------------------");
let zeroCount = 0;
report.forEach(r => {
    if (r.matchCount === 0) {
        zeroCount++;
        console.log(`${r.term.padEnd(30)} | ${r.matchCount}`);
    }
});

console.log(`\nTotal menu items audited: ${report.length}`);
console.log(`Menu items with 0 matches: ${zeroCount}`);

