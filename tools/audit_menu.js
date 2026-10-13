const fs = require('fs');

// We need to read menu.js, extract the Menu.menuData object.
const menuCode = fs.readFileSync('js/menu.js', 'utf8');
const menuDataMatch = menuCode.match(/static menuData = (\{[\s\S]*?\n  \};\n\n  static init)/);
if (!menuDataMatch) {
    console.error("Could not parse menuData");
    process.exit(1);
}
let jsonStr = menuDataMatch[1].replace(/\n  \};\n\n  static init/, '\n  }');
// It's JS object, not strict JSON. Let's evaluate it.
const menuData = eval('(' + jsonStr + ')');

const products = JSON.parse(fs.readFileSync('data/products.json', 'utf8'));

const auditTerms = new Set();

// From accessories
Object.values(menuData.accessories).forEach(arr => {
    arr.forEach(item => auditTerms.add(item));
});
// From ridingGears
menuData.ridingGears.sidebar.forEach(item => auditTerms.add(item));
menuData.ridingGears.cards.forEach(card => {
    auditTerms.add(card.search || card.name || card.category);
});
// From luggageTouring
menuData.luggageTouring.sidebar.forEach(item => auditTerms.add(item));
menuData.luggageTouring.cards.forEach(card => {
    auditTerms.add(card.search || card.name || card.category);
});
// From helmetsAccessories
menuData.helmetsAccessories.sidebar.forEach(item => auditTerms.add(item));
menuData.helmetsAccessories.cards.forEach(card => {
    auditTerms.add(card.search || card.name || card.category);
});

const report = [];

auditTerms.forEach(term => {
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
    if (r.matchCount === 0) zeroCount++;
    console.log(`${r.term.padEnd(30)} | ${r.matchCount}`);
});

console.log(`\nTotal menu items audited: ${report.length}`);
console.log(`Menu items with 0 matches: ${zeroCount}`);
