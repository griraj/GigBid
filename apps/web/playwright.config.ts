import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const localPythons=process.platform==='win32'
  ? [path.join(root,'.venv','Scripts','python.exe'),path.join(root,'.venv-current','Scripts','python.exe')]
  : [path.join(root,'.venv','bin','python'),path.join(root,'.venv-current','bin','python')];
const python=process.env.GIGBID_PYTHON||localPythons.find(existsSync)||'python';
export default defineConfig({
  testDir:'./tests/e2e',
  timeout:120_000,
  expect:{timeout:90_000},
  workers:1,
  reporter:[['list'],['html',{open:'never',outputFolder:'../../docs/test-reports/playwright'}],['json',{outputFile:'../../evals/results/playwright.json'}]],
  outputDir:'../../tmp/playwright-results',
  use:{baseURL:'http://127.0.0.1:5176',trace:'retain-on-failure',screenshot:'only-on-failure'},
  webServer:[
    {command:`"${python}" -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8010`,cwd:root,
      url:'http://127.0.0.1:8010/health',timeout:120_000,reuseExistingServer:false,
      env:{GIGBID_DATA_DIR:path.join(root,'tmp','e2e-state'),GIGBID_ENV:'development',
        GIGBID_CORS_ORIGINS:'http://127.0.0.1:5176',
        GIGBID_API_TOKEN:'demo-reviewer-token',GIGBID_MODE:'local',GIGBID_TOOL_BACKEND:'mcp'}},
    {command:'npm run dev -- --port 5176 --strictPort',cwd:path.join(root,'apps/web'),url:'http://127.0.0.1:5176',
      timeout:60_000,reuseExistingServer:false,env:{VITE_API_URL:'http://localhost:8010'}},
  ],
});
