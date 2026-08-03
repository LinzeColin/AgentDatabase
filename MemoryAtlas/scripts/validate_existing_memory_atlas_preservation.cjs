#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const cp = require("child_process");
const root = path.resolve(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const checks = [];
const add = (id, pass, evidence) => checks.push({ id, pass: Boolean(pass), evidence });
const app = read("src/App.tsx");
const types = read("src/types.ts");
const constants = read("src/shared/atlas/constants.tsx");
const routes = read("src/app/routeRegistry.tsx");
const shell = read("src/app/MemoryAtlasShell.tsx");
const expected = ["home","galaxy","notion","roi","obsidian","timeline","contribution","wordcloud","search","summary"];
add("PRES-001-direct-root", app.includes("<AppProviders>") && app.includes("<MemoryAtlasShell>") && app.includes("<FeatureRouter />"), "direct composition");
add("PRES-002-no-outer-v31", !/V31App|legacy\s*=|ma31-legacy-boundary|data-existing-memory-atlas-preserved/.test(app), "no outer wrapper");
add("PRES-003-default-home", /DEFAULT_MEMORY_ATLAS_VIEW\s*:\s*ViewKey\s*=\s*[\"']home[\"']/.test(constants), "home");
for (const key of expected) {
  add(`PRES-004-type-${key}`, new RegExp(`[\"']${key}[\"']`).test(types), key);
  add(`PRES-004-route-${key}`, new RegExp(`\\b${key}\\s*:`).test(routes), key);
  add(`PRES-005-view-${key}`, new RegExp(`key:\\s*[\"']${key}[\"']`).test(constants), key);
}
const critical = ["InteractionLens","NodeInspector","ContributionPeriodInspector","CommandPalettePanel","OwnerDailyEntry","OwnerDailyWorkspace","ProposalWorkspace","WritebackProposalPanel","MemoryAtlasHelpPanel"];
for (const token of critical) add(`PRES-006-${token}`, shell.includes(token), token);
add("PRES-006-controls", shell.includes('className="controls"') && shell.includes('className="search-box"'), "filters retained");
add("PRES-006-route-data", shell.includes('data-view={activeView}'), "browser route oracle");
add("PRES-007-no-wrapper-css-source", !shell.includes("ma31-legacy-boundary"), "shell is not nested legacy");
let changed=[];
try { changed=cp.execFileSync("git",["status","--porcelain=v1","--untracked-files=all"],{cwd:path.resolve(root,".."),encoding:"utf8"}).trim().split(/\r?\n/).filter(Boolean).map(x=>x.slice(3)); } catch {}
const dataChanges=changed.filter(p=>/MemoryAtlas\/(public|src\/data|src\/fixtures)\//.test(p) || /Private-Database|primary-objects/.test(p));
add("PRES-007-no-data-change", dataChanges.length===0, dataChanges);
const failed=checks.filter(x=>!x.pass);
console.log(JSON.stringify({schema_version:"memory_atlas.preservation_validation.v1",pass:failed.length===0,check_count:checks.length,failed,checks},null,2));
if(failed.length) process.exit(1);
