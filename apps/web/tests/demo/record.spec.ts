import {test,expect} from '@playwright/test';
import path from 'node:path';
import {mkdirSync,writeFileSync} from 'node:fs';

// Actual browser capture: backend responses are never intercepted or fabricated.
test('record narration-ready synthetic marketplace demonstration',async({browser,request})=>{
  const warm=await request.post('http://127.0.0.1:8010/runs',{
    headers:{Authorization:'Bearer demo-reviewer-token'},
    data:{job_id:'j100',persona:'ai'},timeout:120_000,
  });
  expect(warm.ok()).toBeTruthy();
  // Wake the free hosted service before the closing shot, outside the video.
  expect((await request.get('https://gigbid-ti71.onrender.com/writeup',{
    timeout:120_000,
  })).ok()).toBeTruthy();
  const directory=path.resolve('../../docs/demo');
  mkdirSync(directory,{recursive:true});
  const context=await browser.newContext({baseURL:'http://127.0.0.1:5176',
    viewport:{width:1600,height:900},deviceScaleFactor:1,
    recordVideo:{dir:path.resolve('../../tmp/demo-recording/raw'),size:{width:1600,height:900}},
  });
  await context.addInitScript(()=>{
    sessionStorage.setItem('gigbid_auth','1');
    sessionStorage.setItem('gigbid_token','demo-reviewer-token');
  });
  const page=await context.newPage();
  const started=Date.now();
  const cues:{seconds:number;scene:string}[]=[];
  const until=async(seconds:number)=>{
    const remaining=seconds*1000-(Date.now()-started);
    if(remaining>0)await page.waitForTimeout(remaining);
  };
  const mark=(scene:string)=>{
    const seconds=Number(((Date.now()-started)/1000).toFixed(2));
    cues.push({seconds,scene});console.log(`${seconds}s: ${scene}`);
  };
  const top=()=>page.evaluate(()=>window.scrollTo({top:0,behavior:'smooth'}));
  const job=async(title:string)=>{
    await top();
    await page.getByRole('button',{name:/^Job inbox/}).click();
    await page.getByRole('button').filter({has:page.getByRole('heading',{name:title,exact:true})}).click();
  };
  await page.goto('/');
  await expect(page.getByRole('navigation',{name:'Main navigation'})).toBeVisible();
  mark('Overview: synthetic marketplace; approval required');
  await until(15);
  mark('Analyze churn prediction opportunity');
  await job('Build churn prediction pipeline');
  await expect(page.getByRole('button',{name:'Approve & submit',exact:true})).toBeVisible();
  await until(29);
  await page.getByRole('heading',{name:'Decision center',exact:true}).hover();
  await until(35);
  await page.getByRole('heading',{name:/Requirement/}).scrollIntoViewIfNeeded();
  await until(42);
  await page.getByRole('heading',{name:/Proposal/}).scrollIntoViewIfNeeded();
  await until(50);
  mark('Review and edit the cited proposal');
  const editor=page.getByRole('textbox',{name:/proposal/i});
  await editor.scrollIntoViewIfNeeded();
  await editor.click();
  await editor.press('ControlOrMeta+End');
  await editor.pressSequentially(' I would confirm the delivery schedule before starting.',{delay:75});
  await until(65);
  await page.getByRole('button',{name:'Approve & submit',exact:true}).click();
  await expect(page.getByText('submitted',{exact:true}).first()).toBeVisible();
  mark('Approved proposal submitted to local simulator');
  await until(75);
  mark('Scam screening');
  await job('Unpaid sample work outside platform');
  await expect(page.getByText(/^skip$/i).first()).toBeVisible();
  await top();
  await until(90);
  mark('Prompt injection screening');
  await job('Urgent banking verification task');
  await expect(page.getByText(/^skip$/i).first()).toBeVisible();
  await top();
  await until(105);
  mark('Interview reply: draft, review, approve');
  await page.getByRole('button',{name:'Messages',exact:true}).click();
  await page.getByLabel('Incoming client message').fill('Can we schedule an interview next week?');
  await until(111);
  await page.getByRole('button',{name:'Draft response',exact:true}).click();
  const approve=page.getByRole('button',{name:'Approve response',exact:true});
  await expect(approve).toBeVisible();
  await approve.scrollIntoViewIfNeeded();
  await until(129);
  await approve.click();
  await expect(page.getByText('sent',{exact:true})).toBeVisible();
  await until(140);
  mark('Negotiation below the configured minimum rate');
  await page.getByLabel('Incoming client message').fill('Our hourly rate is $15 per hour. Can you accept that rate?');
  await page.getByRole('button',{name:'Draft response',exact:true}).click();
  await expect(page.getByText(/My minimum hourly rate/)).toBeVisible();
  await page.getByRole('button',{name:'Approve response',exact:true}).scrollIntoViewIfNeeded();
  await until(160);
  mark('Public source code and evaluation evidence');
  await page.goto('https://github.com/griraj/GigBid',{waitUntil:'domcontentloaded',timeout:30_000});
  await until(170);
  mark('Published technical write-up');
  await page.goto('https://gigbid-ti71.onrender.com/writeup',{waitUntil:'domcontentloaded',timeout:30_000});
  await until(180);
  const video=page.video();
  await context.close();
  if(!video)throw new Error('Video recording was not created');
  await video.saveAs(path.join(directory,'GigBid_Silent_Demo.webm'));
  writeFileSync(path.join(directory,'GigBid_Demo_Timeline.json'),JSON.stringify({
    source:'Actual local GigBid application with real backend and MCP calls; synthetic marketplace data',
    audio:'Silent; user narration will be added later',width:1600,height:900,
    nominalDurationSeconds:180,playbackSpeed:1,cues,
  },null,2)+'\n');
});
