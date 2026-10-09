// Syntax-check every Code node in the call-intelligence workflow.
const w = require("../n8n/workflows/atlas-call-intelligence-v1.json");
const wf = Array.isArray(w) ? w[0] : w;
let failed = 0;
for (const n of wf.nodes) {
  const code = n.parameters.jsCode;
  if (!code) continue;
  try {
    new Function("$input", "$", "$env", code);
    console.log("syntax ok:", n.name);
  } catch (e) {
    failed++;
    console.log("SYNTAX ERROR:", n.name, e.message);
  }
}
const prep = wf.nodes.find((n) => n.name === "Prepare Analysis Prompt");
const run = new Function("$input", "$", "$env", prep.parameters.jsCode);
const out = run({ item: { json: { transcript: "اپراتور: سلام", meta: { company_name: "آتیران", department: "auto", call_date: "2026-10-09" } } } });
console.log(out.json.prompt.slice(0, 400));
process.exit(failed ? 1 : 0);
