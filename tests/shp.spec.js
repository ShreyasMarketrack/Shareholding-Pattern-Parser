import { test, expect } from '@playwright/test';

test('Shareholding Viewer displays nested taxonomy groups accurately', async ({ page }) => {
  // Go to the locally running app
  await page.goto('http://localhost:5173/');

  // Wait for data to load
  await page.waitForSelector('.shp-table');

  // Verify the general information panel
  const companyName = await page.textContent('.info-item:has-text("Company Name") .info-value');
  expect(companyName).toBeTruthy();
  console.log(`Loaded company: ${companyName}`);

  // Get total validation string
  const totalShareholding = await page.textContent('.total-row td:last-child');
  console.log(`Total Shareholding: ${totalShareholding}`);
  
  // Total shareholding should ideally be around 100% (or strictly <= 100% since rollups fix overflow)
  const totalVal = parseFloat(totalShareholding);
  expect(totalVal).toBeLessThanOrEqual(100.01);
  expect(totalVal).toBeGreaterThan(0);

  // Click on "Promoters" to expand it
  await page.click('text=Promoters');
  
  // Now "Indian" and "Foreign" should be visible
  await expect(page.locator('text=Indian').first()).toBeVisible();
  await expect(page.locator('text=Foreign').first()).toBeVisible();

  // Click on "Indian" to expand it
  await page.click('text=Indian');

  // Since we default to Hide Zero Values = true, Individuals/HUF is hidden (it's 0%).
  // Let's toggle off "Hide Zero Values" to see it
  const hideZeroSlider = page.locator('label.switch-label .slider');
  await hideZeroSlider.click();

  // Now "Individuals/Hindu undivided Family" should be visible
  await expect(page.locator('text=Individuals/Hindu undivided Family').first()).toBeVisible();

  // Click on it
  await page.click('text=Individuals/Hindu undivided Family');

  // Now we should see the deep rows
  let deepRowsCount = await page.locator('.entity-row.depth-3').count();
  console.log(`Found ${deepRowsCount} specific entities under Individuals/HUF with Hide Zero OFF`);
  expect(deepRowsCount).toBeGreaterThan(0);
  
  // Turn Hide Zero Values back on
  await hideZeroSlider.click();
  
  // Let's check "Any Other (specify)" which has the 32.9% Adani Trust
  await page.click('text=Any Other (specify)');
  const otherRowsCount = await page.locator('.entity-row').filter({ hasText: 'Adani Family Trust' }).count();
  console.log(`Found Adani Family Trust: ${otherRowsCount}`);
  expect(otherRowsCount).toBeGreaterThan(0);

  // Switch to Processed JSON
  await page.click('button:has-text("Processed JSON")');
  await page.waitForTimeout(500); // wait for data fetch
  
  const companyNameProcessed = await page.textContent('.info-item:has-text("Company Name") .info-value');
  expect(companyNameProcessed).toBeTruthy();
  console.log(`Loaded processed company: ${companyNameProcessed}`);
  
  const totalShareholdingProcessed = await page.textContent('.total-row td:last-child');
  const totalValProc = parseFloat(totalShareholdingProcessed);
  expect(totalValProc).toBeLessThanOrEqual(100.01);
  expect(totalValProc).toBeGreaterThan(0);

  console.log("Playwright test completed successfully!");
});
