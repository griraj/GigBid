import base from './playwright.config';
import {defineConfig} from '@playwright/test';

export default defineConfig({...base,testDir:'./tests/demo',timeout:260_000,
  reporter:[['list']],outputDir:'../../output/demo/raw',
  use:{...base.use,viewport:{width:1440,height:1000},video:{mode:'on',size:{width:1440,height:1000}}},
});
