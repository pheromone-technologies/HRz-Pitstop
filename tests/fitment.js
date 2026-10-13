const activeBike = { brand: 'Royal Enfield', model: 'Himalayan', variant: 'Standard' };
const activeBikeStr = 'royal enfield himalayan standard';
const activeBikeStrShort = 'royal enfield himalayan';
const activeModelOnly = 'himalayan';
const testStrs = ['royal enfield', 'honda cb350', 'universal', 'himalayan 411', 'standard', ''];
testStrs.forEach(compatStr => {
  const lower = compatStr.toLowerCase();
  const res = activeBikeStr.includes(lower) || lower.includes(activeBikeStr) || activeBikeStrShort.includes(lower) || lower.includes(activeBikeStrShort) || lower === activeModelOnly || (lower.includes('royal enfield') && lower.includes('himalayan'));
  console.log(compatStr + ' => ' + res);
});
