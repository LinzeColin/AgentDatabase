const fs = require("node:fs");
const path = require("node:path");

const databaseRoot = path.resolve(__dirname, "../../..");
const migrationPath = path.join(
  databaseRoot,
  "config/memory_atlas_legacy_command_migrations.json",
);

function loadLegacyCommandMigrations() {
  const payload = JSON.parse(fs.readFileSync(migrationPath, "utf8"));
  if (
    payload.schema_version !== "memory_atlas.legacy_command_migrations.v1_2_1_s04_p3_t3"
    || payload.compatibility_policy?.mode !== "lookup_only"
    || payload.compatibility_policy?.execution_supported !== false
    || payload.compatibility_policy?.shell_invocation_allowed !== false
    || payload.compatibility_policy?.removal_version !== "v1.2.2"
    || payload.compatibility_policy?.maximum_supported_releases !== 1
    || payload.compatibility_policy?.removal_required !== true
    || !Array.isArray(payload.migrations)
    || payload.migrations.length !== 178
  ) {
    return null;
  }
  const migrations = new Map(payload.migrations.map((row) => [row.legacy_alias, row]));
  return migrations.size === 178 ? migrations : null;
}

function legacyCommandMappingsCover(expectedMappings) {
  const migrations = loadLegacyCommandMigrations();
  if (!migrations) return false;
  return Object.entries(expectedMappings).every(([alias, replacementAlias]) => {
    const row = migrations.get(alias);
    return row
      && row.replacement_command === `npm run ${replacementAlias}`
      && row.compatibility_mode === "lookup_only"
      && row.execution_supported === false;
  });
}

module.exports = { legacyCommandMappingsCover };
