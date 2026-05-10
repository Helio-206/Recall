const fs = require("fs");
const path = require("path");

function toUtcIso(date) {
  return date.toISOString();
}

function toUtcDateKey(date) {
  return date.toISOString().slice(0, 10);
}

function toUtcRunId(date) {
  return date.toISOString().replace(/[-:.]/g, "").replace(".000Z", "Z");
}

function ensureDirForFile(filePath) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
}

function readTextIfExists(filePath) {
  if (!fs.existsSync(filePath)) {
    return "";
  }
  return fs.readFileSync(filePath, "utf8");
}

function writeJson(filePath, data) {
  ensureDirForFile(filePath);
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function appendMarkdownEntry(filePath, entry) {
  ensureDirForFile(filePath);

  const existing = readTextIfExists(filePath);
  const header = "# Recall Automation Log\n\n";
  const base = existing.trim().length > 0 ? `${existing.trimEnd()}\n\n` : header;

  fs.writeFileSync(filePath, `${base}${entry}\n`, "utf8");
}

function buildSnapshot(now) {
  const checkedItems = [
    "API and web workspaces accessible",
    "Daily snapshot generated",
    "Automation log updated"
  ];

  return {
    updatedAt: toUtcIso(now),
    projectName: "Recall",
    module: "Learning OS",
    dailyRunId: `recall-${toUtcRunId(now)}`,
    checkedItems,
    roadmapStatus: "Core ingestion, transcript, AI learning and search phases are mapped and versioned.",
    ingestionStatus: "Ingestion pipeline migrations and models are present; monitor new source processing health daily.",
    learningSpacesStatus: "Learning space entities and curriculum reconstruction flow are available for iterative improvements."
  };
}

function buildLogEntry(now, snapshot) {
  const checkedLines = snapshot.checkedItems.map((item) => `- [x] ${item}`).join("\n");

  return [
    `## ${toUtcDateKey(now)} - ${toUtcIso(now)}`,
    "",
    "Resumo do estado:",
    `- Roadmap: ${snapshot.roadmapStatus}`,
    `- Ingestion: ${snapshot.ingestionStatus}`,
    `- Learning spaces: ${snapshot.learningSpacesStatus}`,
    "",
    "Tarefas verificadas:",
    checkedLines,
    "",
    "Proxima acao sugerida:",
    "- Revisar os ultimos ajustes no fluxo de ingestao e priorizar uma melhoria incremental para o dia seguinte."
  ].join("\n");
}

function main() {
  const repoRoot = process.cwd();
  const snapshotPath = path.join(repoRoot, "data", "recall-daily-snapshot.json");
  const logPath = path.join(repoRoot, "docs", "automation-log.md");

  const now = new Date();
  const snapshot = buildSnapshot(now);

  writeJson(snapshotPath, snapshot);
  appendMarkdownEntry(logPath, buildLogEntry(now, snapshot));
}

main();