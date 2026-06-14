// fuzzy.js - Dependency-free string similarity module
// Implements Sorensen-Dice coefficient to replicate Python's difflib Gestalt behavior
// Handles edge cases like "IndividualsOrHUFDomain" -> "IndividualsOrHinduUndividedFamilyDomain"

export function diceCoefficient(string1, string2) {
    if (!string1 || !string2) return 0;
    if (string1 === string2) return 1;
    if (string1.length < 2 || string2.length < 2) return 0;
    
    let bigrams1 = new Map();
    for (let i = 0; i < string1.length - 1; i++) {
        const bigram = string1.substring(i, i + 2);
        bigrams1.set(bigram, (bigrams1.get(bigram) || 0) + 1);
    }
    
    let intersectionSize = 0;
    for (let i = 0; i < string2.length - 1; i++) {
        const bigram = string2.substring(i, i + 2);
        const count = bigrams1.get(bigram) || 0;
        if (count > 0) {
            bigrams1.set(bigram, count - 1);
            intersectionSize++;
        }
    }
    
    return (2.0 * intersectionSize) / (string1.length - 1 + string2.length - 1);
}

// Helper to run against an array of valid domains
export function findBestMatch(target, validDomains) {
    let stripped = target.replace('DetailsOfSharesHeldBy', '');
    let bestMatch = target;
    let bestScore = 0;
    
    validDomains.forEach(valid => {
        let score = diceCoefficient(stripped, valid);
        if (score > bestScore) {
            bestScore = score;
            bestMatch = valid;
        }
    });
    
    return {
        original: target,
        stripped: stripped,
        bestMatch: bestMatch,
        score: bestScore.toFixed(2)
    };
}
