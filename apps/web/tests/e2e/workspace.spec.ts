import {test,expect,Page} from '@playwright/test';

async function login(page:Page){
  await page.goto('/');
  await page.getByLabel('Reviewer token').fill('demo-reviewer-token');
  await page.getByRole('button',{name:/Enter workspace/}).click();
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
}
async function analyze(page:Page){
  await page.getByRole('button',{name:/Job inbox/}).click();
  await page.getByRole('button').filter({has:page.getByRole('heading',{name:'Build churn prediction pipeline',exact:true})}).click();
  await expect(page.getByRole('button',{name:/Approve/}).first()).toBeVisible();
}

test('onboarding validates reviewer access and selects a persona',async({page})=>{
  await login(page);
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.getByLabel('Freelancer specialty').selectOption('web');
  await expect(page.getByLabel('Freelancer specialty')).toHaveValue('web');
});
test('approve a grounded proposal',async({page})=>{
  await login(page);await analyze(page);
  await page.getByRole('button',{name:/Approve/}).first().click();
  await expect(page.getByText('submitted',{exact:true}).first()).toBeVisible();
});
test('reject a proposal with a reason',async({page})=>{
  await login(page);await analyze(page);
  await page.getByPlaceholder(/reason/i).fill('Schedule is full this week');
  await page.getByRole('button',{name:/Reject/}).first().click();
  await expect(page.getByText('rejected',{exact:true}).first()).toBeVisible();
});
test('edit a draft before approval',async({page})=>{
  await login(page);await analyze(page);
  const editor=page.getByRole('textbox',{name:/proposal/i});
  const text=await editor.inputValue();
  await editor.fill(text+' I would clarify the delivery schedule first.');
  await page.getByRole('button',{name:/Approve/}).first().click();
  await expect(page.getByText('submitted',{exact:true}).first()).toBeVisible();
});
test('marketplace outage displays a degraded-mode message',async({page})=>{
  await login(page);
  await page.route('**/runs/stream',route=>route.fulfill({status:503,body:'Unavailable'}));
  await page.getByRole('button',{name:/Job inbox/}).click();
  await page.getByRole('button').filter({has:page.getByRole('heading',{name:'Build churn prediction pipeline',exact:true})}).click();
  await expect(page.getByRole('alert')).toContainText('Marketplace unavailable');
});
test('saved approval can be reopened after refresh',async({page})=>{
  await login(page);await analyze(page);
  await page.reload();
  await page.getByRole('button',{name:'Pipeline',exact:true}).click();
  await page.getByRole('button',{name:/Build churn prediction pipeline/}).first().click();
  await expect(page.getByRole('button',{name:/Approve/}).first()).toBeVisible();
});
