#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve, relative, extname } from "node:path";
import process from "node:process";
import ts from "typescript";

const SCHEMA_VERSION = "memory_atlas.semantic_readability.v1_2_1_s05_p3_t2";
const RULES = [
  "mojibake",
  "main_view_machine_field",
  "actionless_error",
  "english_empty_state",
];
const CONFIG_KEYS = new Set([
  "schema_version",
  "task_id",
  "remediation_task",
  "profile_bindings",
  "rules",
  "known_findings",
]);
const KNOWN_FINDING_KEYS = new Set(["fingerprint", "rule", "path", "anchor"]);
const USER_TEXT_ATTRIBUTES = new Set(["aria-label", "title", "placeholder", "alt"]);
const COPY_ROOT_PATTERN = /^(?:copy|uiCopy|zhCNCopy)$/;
const HIDDEN_DETAIL_TAGS = new Set(["details", "MachineFieldDetails", "EvidenceRefsDetails"]);
const COPY_NON_VISIBLE_KEYS = new Set(["term", "view"]);
const ACTION_PATTERN = /请|重试|重新|检查|返回|切换|(?<!无法)继续|打开|查看|修复|联系|确认|导入|生成|恢复|前往|进入/;
const CJK_PATTERN = /[\u3400-\u9fff]/;
const MOJIBAKE_MARKERS = ["\ufffd", "Ã", "Â", "â€", "ðŸ", "锟斤拷"];
const LATIN1_UTF8_TAIL = "\\u0080-\\u00bf\\u20ac\\u201a\\u0192\\u201e\\u2026\\u2020\\u2021\\u02c6\\u2030\\u0160\\u2039\\u0152\\u017d\\u2018\\u2019\\u201c\\u201d\\u2022\\u2013\\u2014\\u02dc\\u2122\\u0161\\u203a\\u0153\\u017e\\u0178";
const MOJIBAKE_PATTERNS = [new RegExp(`[äåæçèé][${LATIN1_UTF8_TAIL}]{2}`, "g")];
const MACHINE_LITERAL_PATTERNS = [
  /\b(?:[a-z][a-z0-9]*_){1,}[a-z0-9]+\b/g,
  /\bmemory_atlas\.[a-z0-9_.-]+\b/gi,
  /\b[0-9a-f]{40}(?:[0-9a-f]{24})?\b/gi,
  /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/gi,
];
const MACHINE_PROPERTY_NAMES = new Set([
  "schema_version",
  "review_schema_version",
  "closure_schema_version",
  "source_review_schema_version",
  "proposal_schema_version",
  "generated_at",
  "saved_at",
  "original_value",
  "proposed_value",
  "rollback_metadata",
  "requires_conflict_check",
  "requires_agent_or_human_apply",
  "source_scope",
  "target_type",
  "signal_type",
  "proposal_decision",
  "risk_level",
  "current_state",
  "action_half_life",
  "confidence",
  "status",
  "source_id",
  "ref_type",
  "evidence_level",
]);
const BARE_MACHINE_LABELS = new Set([
  "brightness",
  "color",
  "confidence",
  "mass",
  "source",
  "status",
  "trail",
  "urgency",
]);
const APPROVED_FORMATTER_PATTERN = /^(?:format|human|zhCN|display|label|toLocale)|(?:Title|Label|Copy|Summary|Narrator)$/;
const CONTROL_CALLS = new Set(["every", "filter", "find", "includes", "some", "startsWith", "endsWith", "sort"]);
const COMPARISON_TOKENS = new Set([
  ts.SyntaxKind.EqualsEqualsToken,
  ts.SyntaxKind.EqualsEqualsEqualsToken,
  ts.SyntaxKind.ExclamationEqualsToken,
  ts.SyntaxKind.ExclamationEqualsEqualsToken,
  ts.SyntaxKind.GreaterThanToken,
  ts.SyntaxKind.GreaterThanEqualsToken,
  ts.SyntaxKind.LessThanToken,
  ts.SyntaxKind.LessThanEqualsToken,
]);

function parseArgs(argv) {
  const values = { srcRoot: resolve("src"), config: resolve("../../config/memory_atlas_semantic_readability.json") };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--src-root" && value) {
      values.srcRoot = resolve(value);
      index += 1;
    } else if (flag === "--config" && value) {
      values.config = resolve(value);
      index += 1;
    } else {
      throw new Error(`unsupported or incomplete argument: ${flag}`);
    }
  }
  return values;
}

function sameKeys(value, expected) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value);
  return actual.length === expected.size && actual.every((key) => expected.has(key));
}

function loadConfig(path) {
  const payload = JSON.parse(readFileSync(path, "utf8"));
  if (!sameKeys(payload, CONFIG_KEYS)) throw new Error("semantic readability config keys do not match the schema");
  if (payload.schema_version !== SCHEMA_VERSION) throw new Error("semantic readability schema version is unsupported");
  if (payload.task_id !== "S05-P3-T2" || payload.remediation_task !== "S05-P3-T3") {
    throw new Error("semantic readability task boundary must be S05-P3-T2 -> S05-P3-T3");
  }
  if (JSON.stringify(payload.profile_bindings) !== JSON.stringify(["ui", "release"])) {
    throw new Error("semantic readability must bind exactly to ui and release");
  }
  if (JSON.stringify(payload.rules) !== JSON.stringify(RULES)) {
    throw new Error("semantic readability rules must cover the four frozen categories");
  }
  if (!Array.isArray(payload.known_findings)) throw new Error("known_findings must be an array");
  const fingerprints = new Set();
  for (const finding of payload.known_findings) {
    if (!sameKeys(finding, KNOWN_FINDING_KEYS)) throw new Error("known finding keys do not match the schema");
    if (!RULES.includes(finding.rule)) throw new Error(`unknown finding rule: ${finding.rule}`);
    if (!/^[0-9a-f]{16}$/.test(finding.fingerprint)) throw new Error("known finding fingerprint is invalid");
    if (typeof finding.path !== "string" || !finding.path || typeof finding.anchor !== "string" || !finding.anchor) {
      throw new Error("known finding path and anchor are required");
    }
    if (fingerprints.has(finding.fingerprint)) throw new Error(`duplicate known finding: ${finding.fingerprint}`);
    fingerprints.add(finding.fingerprint);
  }
  return payload;
}

function walkSourceFiles(root) {
  const files = [];
  const visit = (directory) => {
    for (const name of readdirSync(directory).sort()) {
      const path = resolve(directory, name);
      const rel = relative(root, path).split("\\").join("/");
      if (rel.split("/").includes("experiments")) continue;
      const stat = statSync(path);
      if (stat.isDirectory()) visit(path);
      else if ([".ts", ".tsx"].includes(extname(path)) && !name.endsWith(".d.ts")) files.push(path);
    }
  };
  visit(root);
  return files;
}

function normalizeAnchor(value) {
  return value.replace(/\s+/g, " ").trim().slice(0, 180);
}

function lineOf(sourceFile, position) {
  return sourceFile.getLineAndCharacterOfPosition(position).line + 1;
}

function addFinding(findings, sourceFile, path, rule, position, anchor, detail) {
  const normalized = normalizeAnchor(anchor);
  if (!normalized) return;
  findings.push({ rule, path, line: lineOf(sourceFile, position), anchor: normalized, detail });
}

function jsxTagName(node) {
  const tag = ts.isJsxElement(node) ? node.openingElement.tagName : node.tagName;
  return tag.getText();
}

function classNameText(node) {
  const opening = ts.isJsxElement(node) ? node.openingElement : node;
  const attribute = opening.attributes.properties.find(
    (item) => ts.isJsxAttribute(item) && item.name.getText() === "className",
  );
  if (!attribute || !ts.isJsxAttribute(attribute) || !attribute.initializer) return "";
  if (ts.isStringLiteral(attribute.initializer)) return attribute.initializer.text;
  return attribute.initializer.getText();
}

function isInsideHiddenDetails(node) {
  for (let current = node.parent; current; current = current.parent) {
    if (ts.isJsxElement(current) || ts.isJsxSelfClosingElement(current)) {
      const tag = jsxTagName(current);
      if (HIDDEN_DETAIL_TAGS.has(tag)) return true;
      if (/(?:machine|technical|debug|advanced)(?:-|_)?(?:field|detail)/i.test(classNameText(current))) return true;
    }
  }
  return false;
}

function propertyName(node) {
  if (ts.isPropertyAccessExpression(node)) return node.name.text;
  if (ts.isElementAccessExpression(node) && node.argumentExpression && ts.isStringLiteral(node.argumentExpression)) {
    return node.argumentExpression.text;
  }
  return "";
}

function isMachineProperty(name) {
  return MACHINE_PROPERTY_NAMES.has(name)
    || /_(?:id|ids|hash|refs)$/.test(name)
    || /^(?:id|hash)$/.test(name);
}

function isFormatted(node, boundary) {
  for (let current = node.parent; current; current = current.parent) {
    if (ts.isCallExpression(current)) {
      const callee = current.expression.getText().split(".").at(-1) || "";
      if (APPROVED_FORMATTER_PATTERN.test(callee)) return true;
    }
    if (current === boundary) break;
  }
  return false;
}

function isDescendantOf(node, ancestor) {
  return node.getStart() >= ancestor.getStart() && node.getEnd() <= ancestor.getEnd();
}

function isControlOnly(node, boundary) {
  for (let current = node.parent; current; current = current.parent) {
    if (ts.isConditionalExpression(current) && isDescendantOf(node, current.condition)) return true;
    if (ts.isBinaryExpression(current) && COMPARISON_TOKENS.has(current.operatorToken.kind)) return true;
    if (ts.isCallExpression(current)) {
      const callee = current.expression.getText().split(".").at(-1) || "";
      if (CONTROL_CALLS.has(callee)) return true;
    }
    if (current === boundary) break;
  }
  return false;
}

function containsNestedJsx(node) {
  let found = false;
  const visit = (current) => {
    if (found) return;
    if (current !== node && (ts.isJsxElement(current) || ts.isJsxSelfClosingElement(current) || ts.isJsxFragment(current))) {
      found = true;
      return;
    }
    ts.forEachChild(current, visit);
  };
  visit(node);
  return found;
}

function stringFragments(node, fragments, boundary) {
  if (!node || node !== boundary && (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) || ts.isJsxFragment(node))) return;
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) fragments.push({ text: node.text, node });
  else if (ts.isTemplateHead(node) || ts.isTemplateMiddle(node) || ts.isTemplateTail(node)) fragments.push({ text: node.text, node });
  ts.forEachChild(node, (child) => stringFragments(child, fragments, boundary));
}

function machineExpressions(node, expressions, boundary) {
  if (!node || node !== boundary && (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node) || ts.isJsxFragment(node))) return;
  if ((ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) && isMachineProperty(propertyName(node))) {
    if (!isFormatted(node, boundary)) expressions.push(node);
    return;
  }
  ts.forEachChild(node, (child) => machineExpressions(child, expressions, boundary));
}

function machineTokens(text) {
  const tokens = [];
  const normalized = text.trim().toLowerCase().replace(/[：:]+$/g, "");
  if (BARE_MACHINE_LABELS.has(normalized)) tokens.push(normalized);
  for (const pattern of MACHINE_LITERAL_PATTERNS) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) tokens.push(match[0]);
  }
  return [...new Set(tokens)];
}

function attributeMap(node) {
  const opening = ts.isJsxElement(node) ? node.openingElement : node;
  return new Map(
    opening.attributes.properties
      .filter(ts.isJsxAttribute)
      .map((attribute) => [attribute.name.getText(), attribute]),
  );
}

function staticAttributeValue(attribute, copyValues) {
  if (!attribute?.initializer) return "";
  if (ts.isStringLiteral(attribute.initializer)) return attribute.initializer.text;
  if (!ts.isJsxExpression(attribute.initializer) || !attribute.initializer.expression) return "";
  const expression = attribute.initializer.expression;
  if (ts.isStringLiteral(expression) || ts.isNoSubstitutionTemplateLiteral(expression)) return expression.text;
  if (ts.isPropertyAccessExpression(expression)) {
    let root = expression.expression;
    while (ts.isPropertyAccessExpression(root)) root = root.expression;
    if (ts.isIdentifier(root) && COPY_ROOT_PATTERN.test(root.text)) {
      return copyValues.get(expression.name.text) || "";
    }
  }
  return "";
}

function staticElementText(node, copyValues) {
  if (ts.isJsxSelfClosingElement(node)) return "";
  const values = [];
  const visit = (current) => {
    if (current !== node && isInsideHiddenDetails(current)) return;
    if (ts.isJsxText(current)) values.push(current.text);
    if (ts.isJsxExpression(current) && current.expression) {
      const expression = current.expression;
      if (ts.isStringLiteral(expression) || ts.isNoSubstitutionTemplateLiteral(expression)) values.push(expression.text);
      else if (ts.isPropertyAccessExpression(expression)) {
        const resolved = copyValues.get(expression.name.text);
        if (resolved) values.push(resolved);
      }
    }
    ts.forEachChild(current, visit);
  };
  visit(node);
  return normalizeAnchor(values.join(" "));
}

function collectCopyValues(sourceFile) {
  const values = new Map();
  const visit = (node) => {
    if (ts.isPropertyAssignment(node)) {
      const key = node.name && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name)) ? node.name.text : "";
      if (key && !COPY_NON_VISIBLE_KEYS.has(key)) {
        const value = node.initializer;
        if (ts.isStringLiteral(value) || ts.isNoSubstitutionTemplateLiteral(value)) values.set(key, value.text);
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
  return values;
}

function scanJsx(sourceFile, path, findings, copyValues) {
  const inspectVisibleText = (text, node) => {
    if (isInsideHiddenDetails(node)) return;
    for (const token of machineTokens(text)) {
      addFinding(findings, sourceFile, path, "main_view_machine_field", node.getStart(), token, `visible machine token: ${token}`);
    }
  };

  const inspectVisibleExpression = (expression) => {
    const fragments = [];
    stringFragments(expression, fragments, expression);
    for (const fragment of fragments) {
      if (!isFormatted(fragment.node, expression) && !isControlOnly(fragment.node, expression)) {
        inspectVisibleText(fragment.text, fragment.node);
      }
    }
    const expressions = [];
    machineExpressions(expression, expressions, expression);
    for (const machineExpression of expressions) {
      if (isControlOnly(machineExpression, expression)) continue;
      const name = propertyName(machineExpression);
      addFinding(
        findings,
        sourceFile,
        path,
        "main_view_machine_field",
        machineExpression.getStart(),
        machineExpression.getText(),
        `untranslated machine field: ${name}`,
      );
    }
  };

  const visit = (node) => {
    if (ts.isJsxText(node)) inspectVisibleText(node.text, node);

    if (ts.isJsxExpression(node) && node.expression && (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent))) {
      if (!isInsideHiddenDetails(node)) {
        if (!containsNestedJsx(node.expression)) {
          inspectVisibleExpression(node.expression);
        }
      }
    }

    if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = jsxTagName(node);
      const attributes = attributeMap(node);
      for (const name of USER_TEXT_ATTRIBUTES) {
        const attribute = attributes.get(name);
        if (!attribute || isInsideHiddenDetails(attribute)) continue;
        const value = staticAttributeValue(attribute, copyValues);
        if (value) {
          inspectVisibleText(value, attribute);
        } else if (ts.isJsxExpression(attribute.initializer) && attribute.initializer.expression) {
          inspectVisibleExpression(attribute.initializer.expression);
        }
      }

      if (tag === "EmptyState") {
        for (const name of ["title", "description", "actionLabel"]) {
          const attribute = attributes.get(name);
          const value = staticAttributeValue(attribute, copyValues);
          if (value && !CJK_PATTERN.test(value)) {
            addFinding(
              findings,
              sourceFile,
              path,
              "english_empty_state",
              attribute.getStart(),
              `${name}=${value}`,
              "empty-state copy must contain a Chinese explanation",
            );
          }
        }
      }

      if (tag === "ErrorState") {
        const actionLabel = attributes.get("actionLabel");
        const onAction = attributes.get("onAction");
        const description = staticAttributeValue(attributes.get("description"), copyValues);
        const details = staticAttributeValue(attributes.get("details"), copyValues);
        const descriptionNode = attributes.get("description");
        const descriptionSource = descriptionNode?.getText() || "";
        const siblingActionKey = descriptionSource.match(/\.([A-Za-z0-9]+)Description\b/)?.[1];
        const siblingAction = siblingActionKey ? copyValues.get(`${siblingActionKey}Action`) || "" : "";
        const hasGuidance = Boolean(actionLabel && onAction)
          || ACTION_PATTERN.test(description)
          || ACTION_PATTERN.test(details)
          || ACTION_PATTERN.test(siblingAction);
        if (!hasGuidance) {
          const state = staticAttributeValue(attributes.get("dataState"), copyValues) || "unknown";
          addFinding(
            findings,
            sourceFile,
            path,
            "actionless_error",
            node.getStart(),
            `ErrorState:${state}`,
            "error state has no action control or actionable guidance",
          );
        }
      }

      const stateSignature = `${classNameText(node)} ${staticAttributeValue(attributes.get("dataState"), copyValues)}`;
      if (tag !== "EmptyState" && /(?:^|[-_\s])empty(?:$|[-_\s])/i.test(stateSignature)) {
        const text = staticElementText(node, copyValues);
        if (text && !CJK_PATTERN.test(text) && /[A-Za-z]{2}/.test(text)) {
          addFinding(
            findings,
            sourceFile,
            path,
            "english_empty_state",
            node.getStart(),
            `empty-block=${text}`,
            "ad hoc empty-state copy must contain a Chinese explanation",
          );
        }
      }
      if (tag !== "ErrorState" && /(?:^|[-_\s])(?:error|failure|failed)(?:$|[-_\s])/i.test(stateSignature)) {
        const text = staticElementText(node, copyValues);
        if (text && !ACTION_PATTERN.test(text)) {
          addFinding(
            findings,
            sourceFile,
            path,
            "actionless_error",
            node.getStart(),
            `error-block=${text}`,
            "ad hoc error state has no actionable guidance",
          );
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
}

function finalizeFindings(rawFindings) {
  const sorted = rawFindings.sort((left, right) =>
    left.path.localeCompare(right.path) || left.rule.localeCompare(right.rule) || left.line - right.line || left.anchor.localeCompare(right.anchor));
  const occurrences = new Map();
  return sorted.map((finding) => {
    const key = `${finding.rule}\0${finding.path}\0${finding.anchor}`;
    const occurrence = (occurrences.get(key) || 0) + 1;
    occurrences.set(key, occurrence);
    const fingerprint = createHash("sha256").update(`${key}\0${occurrence}`).digest("hex").slice(0, 16);
    return { ...finding, fingerprint };
  });
}

function audit(srcRoot, config) {
  const files = walkSourceFiles(srcRoot);
  const parsed = files.map((path) => {
    const text = readFileSync(path, "utf8");
    const kind = extname(path) === ".tsx" ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
    return {
      path,
      rel: relative(srcRoot, path).split("\\").join("/"),
      text,
      sourceFile: ts.createSourceFile(path, text, ts.ScriptTarget.Latest, true, kind),
    };
  });
  const copySource = parsed.find((item) => item.rel === "i18n/zh-CN.ts");
  const copyValues = copySource ? collectCopyValues(copySource.sourceFile) : new Map();
  const rawFindings = [];

  for (const item of parsed) {
    for (const marker of MOJIBAKE_MARKERS) {
      let offset = item.text.indexOf(marker);
      while (offset >= 0) {
        const lineStart = item.text.lastIndexOf("\n", offset) + 1;
        const lineEnd = item.text.indexOf("\n", offset);
        const lineText = item.text.slice(lineStart, lineEnd < 0 ? undefined : lineEnd);
        addFinding(rawFindings, item.sourceFile, item.rel, "mojibake", offset, `${marker}:${lineText}`, `mojibake marker: ${marker}`);
        offset = item.text.indexOf(marker, offset + marker.length);
      }
    }
    for (const pattern of MOJIBAKE_PATTERNS) {
      pattern.lastIndex = 0;
      for (const match of item.text.matchAll(pattern)) {
        const offset = match.index;
        if (offset === undefined) continue;
        const lineStart = item.text.lastIndexOf("\n", offset) + 1;
        const lineEnd = item.text.indexOf("\n", offset);
        const lineText = item.text.slice(lineStart, lineEnd < 0 ? undefined : lineEnd);
        addFinding(rawFindings, item.sourceFile, item.rel, "mojibake", offset, `${match[0]}:${lineText}`, "UTF-8 text decoded as Latin-1/Windows-1252");
      }
    }
    scanJsx(item.sourceFile, item.rel, rawFindings, copyValues);
  }

  const findings = finalizeFindings(rawFindings);
  const knownByFingerprint = new Map(config.known_findings.map((finding) => [finding.fingerprint, finding]));
  const actualByFingerprint = new Map(findings.map((finding) => [finding.fingerprint, finding]));
  const unexpected = findings.filter((finding) => !knownByFingerprint.has(finding.fingerprint));
  const missing = config.known_findings.filter((finding) => !actualByFingerprint.has(finding.fingerprint));
  const metadataDrift = findings.filter((finding) => {
    const known = knownByFingerprint.get(finding.fingerprint);
    return known && (known.rule !== finding.rule || known.path !== finding.path || known.anchor !== finding.anchor);
  });
  const counts = Object.fromEntries(RULES.map((rule) => [rule, findings.filter((finding) => finding.rule === rule).length]));
  const baselineExact = unexpected.length === 0 && missing.length === 0 && metadataDrift.length === 0;

  return {
    status: baselineExact ? "PASS" : "FAIL",
    schema_version: SCHEMA_VERSION,
    task_id: config.task_id,
    remediation_task: config.remediation_task,
    profile_bindings: config.profile_bindings,
    source_file_count: files.length,
    finding_count: findings.length,
    known_finding_count: config.known_findings.length,
    known_t3_debt_count: config.known_findings.length,
    semantic_readability_clean: findings.length === 0,
    rule_counts: counts,
    baseline_exact: baselineExact,
    findings,
    unexpected_findings: unexpected,
    missing_known_findings: missing,
    metadata_drift: metadataDrift,
    safety: {
      parser: "typescript",
      source_mutation: false,
      raw_data_read: false,
      remote_write: false,
      standalone_profile_created: false,
    },
  };
}

function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const config = loadConfig(args.config);
    const result = audit(args.srcRoot, config);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    process.exitCode = result.status === "PASS" ? 0 : 2;
  } catch (error) {
    process.stdout.write(`${JSON.stringify({
      status: "FAIL",
      schema_version: SCHEMA_VERSION,
      reason: error instanceof Error ? error.message : String(error),
    }, null, 2)}\n`);
    process.exitCode = 2;
  }
}

main();
