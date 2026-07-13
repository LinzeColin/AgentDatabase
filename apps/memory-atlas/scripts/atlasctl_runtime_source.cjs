"use strict";

const fs = require("node:fs");
const path = require("node:path");


function readAtlasctlRuntimeSource(repoRoot) {
  const facade = path.join(repoRoot, "scripts/atlasctl.py");
  const packageRoot = path.join(repoRoot, "scripts/memory_atlas_cli");
  const modulePaths = fs
    .readdirSync(packageRoot, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".py"))
    .map((entry) => path.join(packageRoot, entry.name))
    .sort();

  return [facade, ...modulePaths]
    .map((sourcePath) => fs.readFileSync(sourcePath, "utf8"))
    .join("\n");
}


module.exports = { readAtlasctlRuntimeSource };
