import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [payloadPath, outputPath, previewDir] = process.argv.slice(2);
if (!payloadPath || !outputPath || !previewDir) {
  throw new Error("usage: build_project_cost_workbook.mjs PAYLOAD OUTPUT PREVIEW_DIR");
}

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));
if (!Array.isArray(payload.sheets) || payload.sheets.length !== 8) {
  throw new Error("project-cost workbook requires exactly eight sheets");
}

const workbook = Workbook.create();
const previewFiles = [];
for (let sheetIndex = 0; sheetIndex < payload.sheets.length; sheetIndex += 1) {
  const spec = payload.sheets[sheetIndex];
  if (!spec || typeof spec.name !== "string" || !Array.isArray(spec.headers) || spec.headers.length === 0) {
    throw new Error(`invalid sheet specification at index ${sheetIndex}`);
  }
  if (!Array.isArray(spec.rows) || !Array.isArray(spec.column_kinds) || spec.column_kinds.length !== spec.headers.length) {
    throw new Error(`invalid rows or column kinds for ${spec.name}`);
  }
  for (const row of spec.rows) {
    if (!Array.isArray(row) || row.length !== spec.headers.length) {
      throw new Error(`row width mismatch for ${spec.name}`);
    }
  }

  const sheet = workbook.worksheets.add(spec.name);
  sheet.showGridLines = false;
  const columnCount = spec.headers.length;
  const lastColumn = columnName(columnCount);
  sheet.mergeCells(`A1:${lastColumn}1`);
  sheet.getRange("A1").values = [[spec.title]];
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#16324F",
    font: { bold: true, color: "#FFFFFF", size: 15 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 30;

  const headerRange = sheet.getRangeByIndexes(1, 0, 1, columnCount);
  headerRange.values = [spec.headers];
  headerRange.format = {
    fill: "#DCEAF7",
    font: { bold: true, color: "#16324F" },
    borders: { preset: "outside", style: "thin", color: "#A7B8C7" },
    verticalAlignment: "center",
    wrapText: true,
  };
  headerRange.format.rowHeight = 28;

  if (spec.rows.length > 0) {
    const dataRange = sheet.getRangeByIndexes(2, 0, spec.rows.length, columnCount);
    dataRange.values = spec.rows;
    dataRange.format = {
      borders: {
        insideHorizontal: { style: "thin", color: "#E5EAF0" },
        bottom: { style: "thin", color: "#A7B8C7" },
      },
      verticalAlignment: "top",
      wrapText: true,
    };
    for (let colIndex = 0; colIndex < columnCount; colIndex += 1) {
      const kind = spec.column_kinds[colIndex];
      const columnRange = sheet.getRangeByIndexes(2, colIndex, spec.rows.length, 1);
      if (kind === "MINOR_INTEGER" || kind === "INTEGER") {
        columnRange.format.numberFormat = "#,##0;[Red](#,##0);-";
      } else if (kind === "DATE") {
        columnRange.format.numberFormat = "yyyy-mm-dd";
      } else {
        columnRange.format.numberFormat = "@";
      }
    }
    dataRange.format.autofitRows();
  }

  const widths = Array.isArray(spec.column_widths) ? spec.column_widths : [];
  for (let colIndex = 0; colIndex < columnCount; colIndex += 1) {
    const width = Number(widths[colIndex] ?? 18);
    sheet.getRangeByIndexes(0, colIndex, Math.max(3, spec.rows.length + 2), 1).format.columnWidth = Math.min(
      42,
      Math.max(10, width),
    );
  }
  sheet.freezePanes.freezeRows(2);

  const inspectEndRow = Math.min(spec.rows.length + 2, 24);
  await workbook.inspect({
    kind: "table",
    range: `${spec.name}!A1:${lastColumn}${Math.max(2, inspectEndRow)}`,
    include: "values,formulas",
    tableMaxRows: 24,
    tableMaxCols: 16,
    maxChars: 5000,
  });
}

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
  maxChars: 3000,
});
if (/"matchCount"\s*:\s*[1-9]/.test(formulaErrors.ndjson ?? "")) {
  throw new Error("formula error token detected in workbook");
}

await fs.mkdir(previewDir, { recursive: true });
for (let sheetIndex = 0; sheetIndex < payload.sheets.length; sheetIndex += 1) {
  const spec = payload.sheets[sheetIndex];
  const preview = await workbook.render({
    sheetName: spec.name,
    autoCrop: "all",
    scale: 1,
    format: "png",
  });
  const previewPath = path.join(previewDir, `${String(sheetIndex + 1).padStart(2, "0")}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  previewFiles.push(previewPath);
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
process.stdout.write(`${JSON.stringify({ output_path: outputPath, preview_files: previewFiles })}\n`);

function columnName(count) {
  let value = count;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}
