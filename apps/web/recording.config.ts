import base from './playwright.config';
import {defineConfig} from '@playwright/test';

export default defineConfig({...base,testDir:'./tests/demo',timeout:360_000,
  reporter:[['list']],outputDir:'../../tmp/demo-recording',
  use:{...base.use,video:'off',actionTimeout:20_000},
});
