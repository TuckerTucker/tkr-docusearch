/**
 * Node.js test for URL Builder module
 * Tests URL generation logic without browser dependencies
 */

import { buildDetailsURL, hasChunkContext, extractChunkNumber, isValidSource } from '../../src/frontend/utils/url-builder.js';

// ANSI colors for terminal output
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const RESET = '\x1b[0m';
const BLUE = '\x1b[34m';

let passCount = 0;
let failCount = 0;

function test(name, fn) {
    try {
        fn();
        console.log(`${GREEN}✓${RESET} ${name}`);
        passCount++;
    } catch (error) {
        console.log(`${RED}✗${RESET} ${name}`);
        console.log(`  ${error.message}`);
        failCount++;
    }
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
}

console.log(`${BLUE}Running URL Builder Tests...${RESET}\n`);

// Test 1: buildDetailsURL with chunk_id
test('buildDetailsURL: with chunk_id', () => {
    const source = {
        doc_id: 'abc123',
        page: 5,
        chunk_id: 'abc123-chunk0045'
    };
    const url = buildDetailsURL(source);
    const expected = '/frontend/details.html?id=abc123&page=5&chunk=abc123-chunk0045';
    assert(url === expected, `Expected "${expected}", got "${url}"`);
});

// Test 2: buildDetailsURL without chunk_id
test('buildDetailsURL: without chunk_id', () => {
    const source = {
        doc_id: 'def456',
        page: 3,
        chunk_id: null
    };
    const url = buildDetailsURL(source);
    const expected = '/frontend/details.html?id=def456&page=3';
    assert(url === expected, `Expected "${expected}", got "${url}"`);
});

// Test 3: buildDetailsURL with missing chunk_id field
test('buildDetailsURL: missing chunk_id field', () => {
    const source = {
        doc_id: 'ghi789',
        page: 1
    };
    const url = buildDetailsURL(source);
    const expected = '/frontend/details.html?id=ghi789&page=1';
    assert(url === expected, `Expected "${expected}", got "${url}"`);
});

// Test 4: buildDetailsURL with invalid source
test('buildDetailsURL: invalid source (no doc_id)', () => {
    const source = {
        page: 5
    };
    const url = buildDetailsURL(source);
    const expected = '/frontend/details.html';
    assert(url === expected, `Expected "${expected}", got "${url}"`);
});

// Test 5: buildDetailsURL with null source
test('buildDetailsURL: null source', () => {
    const url = buildDetailsURL(null);
    const expected = '/frontend/details.html';
    assert(url === expected, `Expected "${expected}", got "${url}"`);
});

// Test 6: hasChunkContext with valid chunk_id
test('hasChunkContext: with chunk_id', () => {
    const source = { chunk_id: 'abc123-chunk0045' };
    assert(hasChunkContext(source) === true, 'Should return true');
});

// Test 7: hasChunkContext with null chunk_id
test('hasChunkContext: null chunk_id', () => {
    const source = { chunk_id: null };
    assert(hasChunkContext(source) === false, 'Should return false');
});

// Test 8: hasChunkContext with missing chunk_id
test('hasChunkContext: missing chunk_id', () => {
    const source = {};
    assert(hasChunkContext(source) === false, 'Should return false');
});

// Test 9: hasChunkContext with empty string chunk_id
test('hasChunkContext: empty string chunk_id', () => {
    const source = { chunk_id: '' };
    assert(hasChunkContext(source) === false, 'Should return false');
});

// Test 10: extractChunkNumber with valid chunk_id
test('extractChunkNumber: valid chunk_id (0045)', () => {
    const num = extractChunkNumber('abc123-chunk0045');
    assert(num === 45, `Expected 45, got ${num}`);
});

// Test 11: extractChunkNumber with zero chunk_id
test('extractChunkNumber: valid chunk_id (0000)', () => {
    const num = extractChunkNumber('abc123-chunk0000');
    assert(num === 0, `Expected 0, got ${num}`);
});

// Test 12: extractChunkNumber with invalid format
test('extractChunkNumber: invalid format', () => {
    const num = extractChunkNumber('invalid-format');
    assert(num === null, `Expected null, got ${num}`);
});

// Test 13: extractChunkNumber with null
test('extractChunkNumber: null input', () => {
    const num = extractChunkNumber(null);
    assert(num === null, `Expected null, got ${num}`);
});

// Test 14: isValidSource with valid source
test('isValidSource: valid source', () => {
    const source = {
        doc_id: 'abc123',
        page: 5,
        chunk_id: 'abc123-chunk0045'
    };
    assert(isValidSource(source) === true, 'Should return true');
});

// Test 15: isValidSource without doc_id
test('isValidSource: missing doc_id', () => {
    const source = { page: 5 };
    assert(isValidSource(source) === false, 'Should return false');
});

// Test 16: isValidSource with invalid page type
test('isValidSource: invalid page type', () => {
    const source = {
        doc_id: 'abc123',
        page: 'not-a-number'
    };
    assert(isValidSource(source) === false, 'Should return false');
});

// Test 17: Real-world text search result
test('Real-world: text search result', () => {
    const source = {
        id: 1,
        doc_id: 'test123',
        filename: 'document.pdf',
        extension: 'pdf',
        page: 5,
        chunk_id: 'test123-chunk0012',
        thumbnail_path: null,
        date_added: '2025-10-17T12:00:00Z'
    };
    const url = buildDetailsURL(source);
    assert(url.includes('chunk=test123-chunk0012'), 'Should include chunk parameter');
    assert(hasChunkContext(source) === true, 'Should have chunk context');
});

// Test 18: Real-world visual search result
test('Real-world: visual search result', () => {
    const source = {
        id: 2,
        doc_id: 'visual456',
        filename: 'presentation.pptx',
        extension: 'pptx',
        page: 3,
        chunk_id: null,
        thumbnail_path: '/api/thumbnail/visual456-page3.jpg',
        date_added: '2025-10-17T12:00:00Z'
    };
    const url = buildDetailsURL(source);
    assert(!url.includes('chunk='), 'Should not include chunk parameter');
    assert(hasChunkContext(source) === false, 'Should not have chunk context');
});

// Print summary
console.log(`\n${BLUE}Test Summary:${RESET}`);
console.log(`${GREEN}Passed: ${passCount}${RESET}`);
console.log(`${RED}Failed: ${failCount}${RESET}`);

if (failCount === 0) {
    console.log(`\n${GREEN}All tests passed!${RESET}`);
    process.exit(0);
} else {
    console.log(`\n${RED}Some tests failed!${RESET}`);
    process.exit(1);
}
