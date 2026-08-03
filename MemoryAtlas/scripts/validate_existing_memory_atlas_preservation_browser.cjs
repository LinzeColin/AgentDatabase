#!/usr/bin/env node
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
(async()=>{
  const base=process.env.MEMORY_ATLAS_BASE_URL || "http://127.0.0.1:4173";
  const out=process.env.MEMORY_ATLAS_EVIDENCE_DIR || path.resolve(process.cwd(),".taskpack-runs/memory-atlas-recovery/browser");
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const rows=[];
  try{
    await page.goto(base,{waitUntil:"networkidle",timeout:60000});
    await page.locator(".app-shell").waitFor({state:"visible",timeout:30000});
    const defaultHome=await page.locator('[data-view="home"]').isVisible();
    const outerV31=await page.locator('.ma31-root,.ma31-legacy-boundary').count();
    const navCount=await page.locator('[data-nav-view]').count();
    rows.push({id:"BROWSER-default-home",pass:defaultHome,evidence:{defaultHome}});
    rows.push({id:"BROWSER-no-v31-wrapper",pass:outerV31===0,evidence:{outerV31}});
    rows.push({id:"BROWSER-ten-nav",pass:navCount===10,evidence:{navCount}});
    const keys=["home","galaxy","notion","roi","obsidian","timeline","contribution","wordcloud","search","summary"];
    for(const key of keys){
      await page.locator(`[data-nav-view="${key}"]`).click();
      await page.locator(`[data-view="${key}"]`).waitFor({state:"visible",timeout:20000});
      const visible=await page.locator(`[data-view="${key}"]`).isVisible();
      rows.push({id:`BROWSER-route-${key}`,pass:visible,evidence:{visible}});
    }
    rows.push({id:"BROWSER-controls",pass:await page.locator("section.controls").isVisible(),evidence:"filters"});
    const commandPaletteCount=await page.locator('.command-palette[data-s12-p1-command-palette]').count();
    rows.push({id:"BROWSER-command-contract",pass:commandPaletteCount===1,evidence:{commandPaletteCount}});
    await page.screenshot({path:path.join(out,"restored-existing-memory-atlas.png"),fullPage:true});
  }catch(err){ rows.push({id:"BROWSER-execution",pass:false,evidence:String(err&&err.stack||err)}); }
  await browser.close();
  const failed=rows.filter(x=>!x.pass);
  const report={schema_version:"memory_atlas.preservation_browser.v1",base,pass:failed.length===0,rows,failed};
  fs.writeFileSync(path.join(out,"browser-preservation.json"),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
  if(failed.length) process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
