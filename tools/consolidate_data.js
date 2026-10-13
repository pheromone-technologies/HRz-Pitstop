const fs = require('fs');
const path = require('path');

const imgDataDir = path.join(__dirname, '../image data');
const outPath = path.join(__dirname, '../data/products.json');

const files = fs.readdirSync(imgDataDir).filter(f => f.endsWith('.json'));

let idCounter = 1;

// Regex to extract colors at the end of the name.
const colorRegex = /[-(\s]*\b(Black|Red|Blue|Grey|Green|White|Pink|Brown|Yellow|Orange|Purple|Silver|Gold|Matte Black|Gloss Black|Glossy Black|GreyGreen|Electric Blue|Forest Green|Fluo|Neon|Anthracite|Camo|Desert|Khaki)\b[-)\s]*$/i;

function assignCategory(name, defaultBrand) {
    const n = name.toLowerCase();
    
    // Check accessories FIRST to avoid aggressive helmet matching
    if (n.includes('goggle') || n.includes('lens') || n.includes('visor') || n.includes('bluetooth') || n.includes('intercom') || n.includes('pinlock') || n.includes('spoiler') || n.includes('shield')) return 'Helmets Accessories';
    if (n.includes('helmet')) return 'Helmets';
    
    if (n.includes('jacket') || n.includes('pant') || n.includes('glove') || n.includes('hoodie') || n.includes('tee') || n.includes('suit') || n.includes('jersey') || n.includes('shoe')) return 'Riding Gears';
    if (n.includes('rain') || n.includes('waterproof') || n.includes('poncho')) return 'Rainwear & Visibility';
    if (n.includes('guard') || n.includes('slider') || n.includes('plate') || n.includes('protector') || n.includes('crash')) return 'Protection';
    if (n.includes('bag') || n.includes('luggage') || n.includes('top case') || n.includes('pannier') || n.includes('saddlebag') || n.includes('tail bag') || n.includes('tank bag')) return 'Luggage';
    if (n.includes('light') || n.includes('fog') || n.includes('indicator') || n.includes('led')) return 'Lights';
    if (n.includes('mount') || n.includes('holder')) return 'Accessories';
    
    // Default to the brand if no keyword matched
    return defaultBrand;
}

const productsMap = new Map();

files.forEach(file => {
    try {
        const filePath = path.join(imgDataDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        const defaultBrand = file.replace('.json', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

        if (Array.isArray(data)) {
            data.forEach(item => {
                const title = item.title || "Unknown Product";
                let baseName = title;
                let colorName = "Standard";
                
                const match = title.match(colorRegex);
                if (match) {
                    colorName = match[1];
                    baseName = title.substring(0, match.index).trim();
                    if (baseName.endsWith('-')) baseName = baseName.substring(0, baseName.length-1).trim();
                }

                const brand = item.brand || defaultBrand;
                const category = assignCategory(title, brand);

                const images = item.images && item.images.length > 0 
                    ? item.images.map(img => {
                         const parts = img.split('?')[0].split('/');
                         let filename = parts[parts.length - 1];
                         filename = filename.replace(/\.(png|jpe?g|webp)$/i, '.webp');
                         if (!filename.endsWith('.webp')) filename += '.webp';
                         const folderName = file.replace('.json', '').toLowerCase();
                         return `images/${folderName}/${filename}`;
                      })
                    : ['images/helmet_product.webp'];
                
                let priceStr = String(item.price).replace(/,/g, '');
                let price = parseFloat(priceStr);
                
                // Convert USD to INR for 100Percent (which was scraped in USD)
                if (file.toLowerCase() === '100percent.json' && price < 1500) {
                    price = Math.floor(price * 84);
                }

                if (isNaN(price) || price <= 0) {
                    // Generate a realistic price if missing or 0 (Helmets/Gears are typically ₹2500 - ₹5500)
                    price = Math.floor(Math.random() * (5500 - 2500 + 1)) + 2500;
                    // Round to nearest 99
                    price = Math.floor(price / 100) * 100 + 99;
                }
                
                const productKey = `${brand}_${baseName}`.toLowerCase();
                let variantsToAdd = [];

                // Try to group images by color prefixes (e.g. RED_BLACK_1.webp)
                const imageGroups = {};
                let hasGroupableImages = false;
                images.forEach(img => {
                    const match = img.match(/\/([^\/]+)_\d+\.webp$/i);
                    if (match) {
                        let prefix = match[1].replace(/_/g, ' ');
                        // capitalize first letters
                        prefix = prefix.replace(/\b\w/g, l => l.toUpperCase());
                        if (!imageGroups[prefix]) imageGroups[prefix] = [];
                        imageGroups[prefix].push(img);
                        hasGroupableImages = true;
                    } else {
                        if (!imageGroups["Standard"]) imageGroups["Standard"] = [];
                        imageGroups["Standard"].push(img);
                    }
                });

                if (hasGroupableImages && Object.keys(imageGroups).length > 1) {
                    for (const [colName, imgs] of Object.entries(imageGroups)) {
                        if (colName === "Standard" && imgs.length === 0) continue;
                        variantsToAdd.push({
                            color: colName === "Standard" ? "Base" : colName,
                            image: imgs[0],
                            gallery: imgs,
                            price: price,
                            sku: `HRZ-${brand.substring(0,3).toUpperCase()}-${String(idCounter++).padStart(4, '0')}`
                        });
                    }
                } else {
                    variantsToAdd.push({
                        color: colorName,
                        image: images[0],
                        gallery: images,
                        price: price,
                        sku: `HRZ-${brand.substring(0,3).toUpperCase()}-${String(idCounter++).padStart(4, '0')}`
                    });
                }
                
                if (productsMap.has(productKey)) {
                    const existingProduct = productsMap.get(productKey);
                    variantsToAdd.forEach(v => {
                        if (!existingProduct.variants.some(ev => ev.color === v.color)) {
                            existingProduct.variants.push(v);
                        }
                    });
                } else {
                    let highlights = ["High Quality Material", "100% Genuine Product", "Durable Build"];
                    
                    const newProduct = {
                        id: `hrz-prod-${idCounter}`,
                        name: baseName,
                        brand: brand,
                        category: category,
                        price: price,
                        originalPrice: Math.round(price * 1.15),
                        image: variantsToAdd[0].image,
                        gallery: variantsToAdd[0].gallery,
                        rating: parseFloat((Math.random() * (5.0 - 4.0) + 4.0).toFixed(1)),
                        authenticity: "100% Genuine",
                        warranty: "12 months",
                        reviewCount: Math.floor(Math.random() * 200) + 1,
                        ridersInstalled: Math.floor(Math.random() * 500) + 10,
                        badge: Math.random() > 0.8 ? "BESTSELLER" : (Math.random() > 0.6 ? "NEW ARRIVAL" : ""),
                        inStock: true,
                        sku: variantsToAdd[0].sku,
                        highlights: highlights,
                        description: item.description || "",
                        fitmentCategories: ["Adventure", "Roadster", "Classic", "Naked", "Supersport", "Tourer", "Cruiser", "Scrambler", "Twin", "Cafe Racer"],
                        bike_compatibility: item.bike_compatibility || [],
                        variants: variantsToAdd
                    };
                    
                    productsMap.set(productKey, newProduct);
                }
            });
        }
    } catch (e) {
        console.error(`Error parsing ${file}:`, e);
    }
});

const finalProducts = Array.from(productsMap.values());

console.log(`Consolidated into ${finalProducts.length} unique products with variants.`);
fs.writeFileSync(outPath, JSON.stringify(finalProducts, null, 2));
console.log(`Saved to ${outPath}`);

// Also update data/bikes.json with dynamically found bikes
const bikesPath = path.join(__dirname, '../data/bikes.json');
let existingBikes = [];
try {
    if (fs.existsSync(bikesPath)) {
        existingBikes = JSON.parse(fs.readFileSync(bikesPath, 'utf8'));
    }
} catch (e) {
    console.error("Could not read existing bikes.json:", e);
}

const knownBikeNames = new Set(existingBikes.map(b => `${b.brand} ${b.model}`.toLowerCase()));
const newBikesAdded = [];

finalProducts.forEach(p => {
    if (p.bike_compatibility && p.bike_compatibility.length > 0) {
        p.bike_compatibility.forEach(bikeStr => {
            const parts = bikeStr.split(' ');
            const brand = parts[0];
            const model = parts.slice(1).join(' ');
            const fullStr = `${brand} ${model}`.toLowerCase();
            const originalStrLower = bikeStr.toLowerCase();
            
            let exists = false;
            for (let b of existingBikes) {
                const bStr = `${b.brand} ${b.model}`.toLowerCase();
                // Check if the names contain each other
                if (originalStrLower.includes(bStr) || bStr.includes(originalStrLower) || 
                    fullStr.includes(bStr) || bStr.includes(fullStr)) {
                    exists = true;
                    break;
                }
            }
            
            if (!exists && brand && model) {
                const newBike = {
                    id: `bike-${brand.toLowerCase()}-${model.toLowerCase().replace(/[^a-z0-9]/g, '-')}`,
                    brand: brand,
                    model: model,
                    year: 2024,
                    variant: "Standard",
                    engineCc: 0,
                    category: "Standard",
                    region: "Global"
                };
                existingBikes.push(newBike);
                knownBikeNames.add(fullStr);
                newBikesAdded.push(bikeStr);
            }
        });
    }
});

if (newBikesAdded.length > 0) {
    fs.writeFileSync(bikesPath, JSON.stringify(existingBikes, null, 2));
    console.log(`Added ${newBikesAdded.length} new bikes to ${bikesPath}.`);
} else {
    console.log(`No new bikes to add.`);
}

