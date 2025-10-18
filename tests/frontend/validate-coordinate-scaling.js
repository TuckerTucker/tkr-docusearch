/**
 * Coordinate Scaling Validation Script
 *
 * This script validates that the coordinate transformation from PDF (bottom-left origin)
 * to Screen/SVG (top-left origin) is correct.
 *
 * Run this in Node.js or browser console to verify the math.
 *
 * Expected behavior:
 * - PDF Y increases upward (bottom-left origin)
 * - Screen Y increases downward (top-left origin)
 * - Higher PDF Y values → Lower screen Y values
 * - Lower PDF Y values → Higher screen Y values
 */

// Simulated coordinate-scaler functions (for Node.js testing)
function scaleBboxToScreen(pdfBbox, pdfWidth, pdfHeight, imageWidth, imageHeight) {
  const { left, bottom, right, top } = pdfBbox;

  // Calculate scale factors
  const scaleX = imageWidth / pdfWidth;
  const scaleY = imageHeight / pdfHeight;

  // Convert to screen coordinates with Y-axis flip
  const screenLeft = left * scaleX;
  const screenTop = imageHeight - (top * scaleY);      // FLIP: PDF top → Screen top
  const screenRight = right * scaleX;
  const screenBottom = imageHeight - (bottom * scaleY);  // FLIP: PDF bottom → Screen bottom

  // Calculate width and height
  const width = screenRight - screenLeft;
  const height = screenBottom - screenTop;

  return {
    x: screenLeft,
    y: screenTop,
    width: width,
    height: height
  };
}

// Test cases based on sample-api-responses.json
const testCases = [
  {
    name: 'Heading at top of page',
    description: 'High PDF Y values (650-720) should become low screen Y values',
    pdfBbox: { left: 72.0, bottom: 650.0, right: 540.0, top: 720.0 },
    pdfDims: { width: 612, height: 792 },
    imageDims: { width: 1020, height: 1320 }, // 150 DPI (612 * 2.0833 = 1020)
    expected: {
      // PDF top=720 is near page top (792)
      // Screen top should be near 0 (top of image)
      yNear: 'top',
      yRange: [0, 300]  // Should be in upper portion
    }
  },
  {
    name: 'Picture at bottom of page',
    description: 'Low PDF Y values (100-300) should become high screen Y values',
    pdfBbox: { left: 150.0, bottom: 100.0, right: 462.0, top: 300.0 },
    pdfDims: { width: 612, height: 792 },
    imageDims: { width: 1020, height: 1320 },
    expected: {
      // PDF top=300 is at 300/792 = 38% from bottom
      // Screen should be at ~62% from top = ~820px
      yNear: 'bottom',
      yRange: [700, 1100]
    }
  },
  {
    name: 'Table in middle',
    description: 'Middle PDF Y values should map to middle screen Y values',
    pdfBbox: { left: 100.0, bottom: 350.0, right: 512.0, top: 600.0 },
    pdfDims: { width: 612, height: 792 },
    imageDims: { width: 1020, height: 1320 },
    expected: {
      // PDF top=600 is at 600/792 = 76% from bottom
      // Screen should be at ~24% from top = ~320px
      yNear: 'middle',
      yRange: [200, 500]
    }
  },
  {
    name: 'Precise DPI calculation',
    description: 'Verify exact scale factors for 150 DPI',
    pdfBbox: { left: 72.0, bottom: 72.0, right: 144.0, top: 144.0 },
    pdfDims: { width: 612, height: 792 },
    imageDims: { width: 1275, height: 1650 }, // Exact 150 DPI (612 * 150/72 = 1275)
    expected: {
      // At 150 DPI, scale factor = 150/72 = 2.0833...
      scaleX: 2.0833,
      scaleY: 2.0833,
      widthExact: 150, // (144-72) * 2.0833 = 150
      heightExact: 150
    }
  }
];

// Run validation
console.log('='.repeat(80));
console.log('COORDINATE SCALING VALIDATION');
console.log('='.repeat(80));
console.log();

let passCount = 0;
let failCount = 0;

testCases.forEach((test, idx) => {
  console.log(`Test ${idx + 1}: ${test.name}`);
  console.log(`  ${test.description}`);
  console.log();

  const result = scaleBboxToScreen(
    test.pdfBbox,
    test.pdfDims.width,
    test.pdfDims.height,
    test.imageDims.width,
    test.imageDims.height
  );

  console.log('  PDF bbox:');
  console.log(`    left: ${test.pdfBbox.left}, bottom: ${test.pdfBbox.bottom}, right: ${test.pdfBbox.right}, top: ${test.pdfBbox.top}`);
  console.log();

  console.log('  Screen bbox:');
  console.log(`    x: ${result.x.toFixed(2)}, y: ${result.y.toFixed(2)}, width: ${result.width.toFixed(2)}, height: ${result.height.toFixed(2)}`);
  console.log();

  // Validate
  let testPassed = true;
  const issues = [];

  if (test.expected.yRange) {
    const [minY, maxY] = test.expected.yRange;
    if (result.y < minY || result.y > maxY) {
      testPassed = false;
      issues.push(`Y coordinate ${result.y.toFixed(2)} is outside expected range [${minY}, ${maxY}]`);
    }
  }

  if (test.expected.scaleX) {
    const scaleX = test.imageDims.width / test.pdfDims.width;
    const tolerance = 0.01;
    if (Math.abs(scaleX - test.expected.scaleX) > tolerance) {
      testPassed = false;
      issues.push(`Scale X ${scaleX.toFixed(4)} doesn't match expected ${test.expected.scaleX}`);
    }
  }

  if (test.expected.widthExact) {
    const tolerance = 1; // 1px tolerance
    if (Math.abs(result.width - test.expected.widthExact) > tolerance) {
      testPassed = false;
      issues.push(`Width ${result.width.toFixed(2)} doesn't match expected ${test.expected.widthExact}`);
    }
  }

  if (test.expected.heightExact) {
    const tolerance = 1;
    if (Math.abs(result.height - test.expected.heightExact) > tolerance) {
      testPassed = false;
      issues.push(`Height ${result.height.toFixed(2)} doesn't match expected ${test.expected.heightExact}`);
    }
  }

  // Check Y-flip correctness
  const pdfYCenter = (test.pdfBbox.bottom + test.pdfBbox.top) / 2;
  const screenYCenter = result.y + (result.height / 2);
  const pdfTopHalf = pdfYCenter > (test.pdfDims.height / 2);
  const screenTopHalf = screenYCenter < (test.imageDims.height / 2);

  // If in PDF top half, should be in screen top half (and vice versa)
  if (pdfTopHalf !== screenTopHalf) {
    testPassed = false;
    issues.push(`Y-flip error: PDF center is in ${pdfTopHalf ? 'top' : 'bottom'} half, but screen center is in ${screenTopHalf ? 'top' : 'bottom'} half`);
  }

  if (testPassed) {
    console.log('  ✅ PASSED');
    passCount++;
  } else {
    console.log('  ❌ FAILED');
    issues.forEach(issue => console.log(`     - ${issue}`));
    failCount++;
  }

  console.log();
  console.log('-'.repeat(80));
  console.log();
});

// Summary
console.log('='.repeat(80));
console.log('SUMMARY');
console.log('='.repeat(80));
console.log(`Total tests: ${testCases.length}`);
console.log(`Passed: ${passCount}`);
console.log(`Failed: ${failCount}`);
console.log();

if (failCount === 0) {
  console.log('✅ All coordinate scaling validations passed!');
  console.log('   Y-axis flip is working correctly.');
} else {
  console.log('❌ Some validations failed. Check the output above.');
}

console.log('='.repeat(80));

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { scaleBboxToScreen, testCases };
}
