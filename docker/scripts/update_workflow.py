"""Rewrite the call-intelligence workflow: generic prompt, manager-ready fields, panel-rendered email."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PATH = Path(__file__).resolve().parents[1] / "n8n" / "workflows" / "atlas-call-intelligence-v1.json"

raw = json.loads(PATH.read_text(encoding="utf-8"))
wf = raw[0] if isinstance(raw, list) else raw
nodes = {n["name"]: n for n in wf["nodes"]}

PARSE_INPUT = r"""const body = $input.item.json.body || $input.item.json;
const audioUrl = body.audioUrl || body.audio_url || body.fileUrl || body.file_url || body.url || '';
const transcript = (body.transcript || body.text || body.transcript_text || '').trim();
const meta = {
  call_id: body.call_id || body.callId || `call_${Date.now()}`,
  department: (body.department || body.dept || 'auto').toLowerCase(),
  agent_name: body.agent_name || body.agentName || '',
  agent_id: body.agent_id || body.agentId || '',
  customer_phone: body.customer_phone || body.customerPhone || '',
  customer_name: body.customer_name || body.customerName || '',
  call_direction: body.call_direction || body.callDirection || 'inbound',
  call_duration_seconds: Number(body.call_duration_seconds || body.callDuration || 0) || 0,
  call_date: body.call_date || body.callDate || new Date().toISOString(),
  company_name: body.company_name || body.companyName || '',
  product_context: body.product_context || body.productContext || ''
};
if (!transcript && !audioUrl) {
  throw new Error('ورودی نامعتبر: transcript یا audioUrl الزامی است.');
}
return { json: { audioUrl, transcript, meta } };"""

SCHEMA = {
    "executive_summary": "",
    "sms_brief": "",
    "next_actions": [],
    "meta": {"department": "sales|support|mixed|unknown", "confidence_overall": 0},
    "customer": {
        "request_summary": "", "needs": [], "pain_points": [], "products_mentioned": [],
        "sentiment": {"overall": "positive|neutral|negative|mixed", "score": 0},
        "satisfaction": {"initial_score": 0, "final_score": 0, "resolved": None},
    },
    "agent_performance": {
        "response_quality_score": 0, "communication_skills": 0, "product_knowledge": 0,
        "empathy_score": 0, "process_adherence": 0, "strengths": [], "improvements": [],
    },
    "sales_analysis": {
        "applicable": False, "purchase_intent_score": 0,
        "purchase_stage": "awareness|interest|consideration|evaluation|negotiation|decision|purchase|closed_won|closed_lost",
        "main_objections": [], "price_sensitivity": "low|medium|high",
        "estimated_discount_to_close_percent": None, "estimated_close_probability_percent": 0,
        "recommended_next_step": "", "competitor_mentions": [],
    },
    "support_analysis": {
        "applicable": False, "issue_category": "", "issue_summary": "",
        "resolution_status": "resolved|partial|unresolved|escalated", "first_call_resolution": None,
        "customer_retention_risk": "low|medium|high",
    },
    "ticket": {
        "title": "", "priority": "low|medium|high|urgent", "description": "", "actionable": True,
        "recommended_assignee": "", "follow_up_required": False, "follow_up_date": "YYYY-MM-DD or empty", "tags": [],
    },
    "insights": {"key_takeaways": [], "risks": [], "opportunities": [], "compliance_notes": []},
    "quality_control": {"transcript_quality": "good|fair|poor", "needs_human_review": False, "review_reason": ""},
}

PREPARE_PROMPT = r"""const item = $input.item.json;
const transcript = item.transcript || '';
const meta = item.meta || {};
const deptHint = meta.department === 'sales' ? 'This is a SALES call.' : meta.department === 'support' ? 'This is a SUPPORT call.' : 'Detect the department yourself.';
const schema = __SCHEMA__;
const today = new Date().toISOString().slice(0, 10);
let todayFa = today;
try { todayFa = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { dateStyle: 'full', timeZone: 'Asia/Tehran' }).format(new Date()); } catch (e) {}
const prompt = `You are a senior sales and customer-experience analyst writing for the managers of the company whose staff answered this call.
Business context (use it to make every recommendation specific to this business; take company and product names from the transcript): ${meta.product_context || 'not provided'}
${deptHint}
Call metadata: agent=${meta.agent_name || 'unknown'}, customer=${meta.customer_name || meta.customer_phone || 'unknown'}, date=${meta.call_date}, today=${today} (${todayFa})

Analyze the call transcript below and return ONLY one valid JSON object (no markdown) with exactly this structure:
${JSON.stringify(schema)}

Writing rules:
- Every text value must be fluent, natural, polite Persian (Farsi) that a busy manager can read in seconds. Keys stay in English. Enum fields use one of the listed English values.
- executive_summary: 2 to 4 sentences — who called, what they wanted, what happened, and the single most important point for the manager.
- sms_brief: the single most important action for the manager in at most 45 Persian characters, no links, no emoji, e.g. "ارسال پیش‌فاکتور تا امروز عصر".
- next_actions: 1 to 5 concrete, imperative actions in Persian, each with what/who/when where possible. Examples: "ارسال پیش‌فاکتور ۲۰ دستگاه برای مشتری تا پایان امروز"، "تماس مجدد کارشناس فنی با مشتری فردا صبح برای رفع مشکل نصب". Never write vague advice like "پیگیری شود".
- Inside Persian text never write Gregorian or ISO dates; use relative words such as «امروز»، «فردا صبح»، «تا پایان هفته» or a Persian (Jalali) date. Only ticket.follow_up_date uses YYYY-MM-DD.
- Name companies, brands and products exactly as they are said in the transcript; if no name is said, write «شرکت» or «محصول» instead of guessing one.
- Use only facts from the transcript. If something is unknown, leave the string empty or the list empty. Do not invent prices, names or dates.
- All scores and percentages are integers from 0 to 100.
- meta.department: "sales" for buying/pricing/quotes, "support" for problems/complaints/how-to, "mixed" if both.
- sales_analysis.applicable=true only when buying is discussed; support_analysis.applicable=true only when a problem is discussed.
- ticket.priority "urgent" only for an angry/at-risk customer or a deal that needs action today. follow_up_date relative to today when a follow-up is needed.
- quality_control.needs_human_review=true when the customer is angry, there is legal/financial risk, a big deal is at stake, or the transcript is unclear; explain why in review_reason.

Transcript:
${transcript}`;
return { json: { prompt, meta, transcript, audioUrl: item.audioUrl } };""".replace("__SCHEMA__", json.dumps(SCHEMA, ensure_ascii=False))

PARSE_VALIDATE = r"""const aiResponse = $input.item.json;
const prev = $('Prepare Analysis Prompt').item.json;
const meta = prev.meta || {};
let text = aiResponse.choices?.[0]?.message?.content || aiResponse.choices?.[0]?.text || '';
if (!text && typeof aiResponse === 'object') text = JSON.stringify(aiResponse);
text = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/\s*```$/i, '').trim();
let analysis;
try { analysis = JSON.parse(text); } catch (e) {
  const m = text.match(/\{[\s\S]*\}/);
  try { analysis = m ? JSON.parse(m[0]) : null; } catch (e2) { analysis = null; }
  if (!analysis) analysis = { parse_error: true, raw_text: text, quality_control: { needs_human_review: true, review_reason: 'پاسخ هوش مصنوعی قابل پردازش نبود.' } };
}
const norm = (o, k) => { if (!o || typeof o[k] !== 'number') return; o[k] = Math.max(0, Math.min(100, Math.round(o[k] > 0 && o[k] <= 1 ? o[k] * 100 : o[k]))); };
norm(analysis.sales_analysis, 'purchase_intent_score');
norm(analysis.sales_analysis, 'estimated_close_probability_percent');
norm(analysis.customer?.satisfaction, 'initial_score');
norm(analysis.customer?.satisfaction, 'final_score');
['response_quality_score', 'communication_skills', 'product_knowledge', 'empathy_score', 'process_adherence'].forEach(k => norm(analysis.agent_performance, k));
analysis.meta = analysis.meta || {};
norm(analysis.meta, 'confidence_overall');
if (['sales', 'support'].includes(meta.department)) analysis.meta.department = meta.department;
if (!['sales', 'support', 'mixed', 'unknown'].includes(analysis.meta.department)) analysis.meta.department = 'unknown';
Object.assign(analysis.meta, {
  call_id: meta.call_id,
  analyzed_at: new Date().toISOString(),
  workflow_version: '2.0.0',
  language: 'fa',
  call_date: meta.call_date,
  call_direction: meta.call_direction,
  call_duration_seconds: meta.call_duration_seconds
});
if (!Array.isArray(analysis.next_actions)) analysis.next_actions = analysis.next_actions ? [String(analysis.next_actions)] : [];
analysis.transcript = { full_text: prev.transcript || '' };
analysis.input = {
  agent_id: meta.agent_id,
  agent_name: meta.agent_name,
  customer_phone: meta.customer_phone,
  customer_name: meta.customer_name
};
return { json: {
  success: !analysis.parse_error,
  call_id: meta.call_id,
  department: analysis.meta.department,
  analysis
} };"""

BUILD_RESPONSE = r"""const prev = $('Parse Validate and Enrich').item.json;
const notify = $input.item.json || {};
return { json: {
  success: prev.success,
  call_id: prev.call_id,
  department: prev.department,
  email_sent: notify.sent === true,
  email_skipped: notify.skipped || null,
  email_error: notify.error || null,
  sms_sent: notify.sms_sent === true,
  customer_sms_sent: notify.customer_sms_sent === true,
  sms: notify.sms || null,
  analysis: prev.analysis
} };"""

nodes["Parse Input"]["parameters"]["jsCode"] = PARSE_INPUT
nodes["Prepare Analysis Prompt"]["parameters"]["jsCode"] = PREPARE_PROMPT
nodes["Parse Validate and Enrich"]["parameters"]["jsCode"] = PARSE_VALIDATE
nodes["Build Response"]["parameters"]["jsCode"] = BUILD_RESPONSE
nodes["AI Request"]["parameters"]["jsonBody"] = (
    "={{ JSON.stringify({ model: $env.AI_MODEL || 'gemini-2.5-flash', messages: [{ role: 'user', content: $json.prompt }], "
    "temperature: 0.2, response_format: { type: 'json_object' } }) }}"
)

send = nodes["Send Manager Email"]
send["parameters"] = {
    "method": "POST",
    "url": "={{ ($env.PANEL_INTERNAL_URL || 'http://panel:8080') + '/api/notify-call' }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [{"name": "X-API-Token", "value": "={{ $env.PANEL_API_TOKEN || '' }}"}]},
    "sendBody": True,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ call_id: $json.call_id }) }}",
    "options": {"timeout": 90000},
}
send["onError"] = "continueRegularOutput"
send["alwaysOutputData"] = True

PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
print("workflow updated:", PATH)
