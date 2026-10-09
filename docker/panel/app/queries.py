"""PostgreSQL report queries for Atlas Manager Panel."""

import json

from .db import execute, fetch_all, fetch_one


# ── Overview & KPIs ──────────────────────────────────────────────

def overview_stats(date_from=None, date_to=None) -> dict:
    where, params = _date_filter(date_from, date_to)
    row = fetch_one(
        f"""
        SELECT
            COUNT(*)::int AS total_calls,
            COUNT(*) FILTER (WHERE department = 'sales')::int AS sales_calls,
            COUNT(*) FILTER (WHERE department = 'support')::int AS support_calls,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            ROUND(AVG(purchase_intent_score)::numeric, 1) AS avg_purchase_intent,
            ROUND(AVG(agent_quality_score)::numeric, 1) AS avg_agent_quality,
            COUNT(*) FILTER (WHERE needs_human_review)::int AS needs_review,
            COUNT(*) FILTER (WHERE purchase_intent_score >= 70)::int AS hot_leads,
            COUNT(*) FILTER (WHERE satisfaction_final_score < 60)::int AS unhappy_count,
            COALESCE(SUM(call_duration_seconds), 0)::int AS total_talk_seconds
        FROM call_analyses
        {where}
        """,
        tuple(params) if params else None,
    )
    return row or {}


def daily_trend(days: int = 30) -> list[dict]:
    return fetch_all(
        """
        SELECT
            DATE(call_date) AS day,
            COUNT(*)::int AS calls,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            ROUND(AVG(purchase_intent_score)::numeric, 1) AS avg_intent,
            COUNT(*) FILTER (WHERE purchase_intent_score >= 70)::int AS hot_leads
        FROM call_analyses
        WHERE call_date >= NOW() - (%s || ' days')::interval
        GROUP BY DATE(call_date)
        ORDER BY day ASC
        """,
        (str(days),),
    )


# ── Performers ───────────────────────────────────────────────────

def top_performers(limit: int = 10) -> list[dict]:
    return fetch_all(
        """
        SELECT
            COALESCE(agent_name, agent_id, 'نامشخص') AS agent_name,
            agent_id,
            COUNT(*)::int AS total_calls,
            ROUND(AVG(agent_quality_score)::numeric, 1) AS avg_quality,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            ROUND(AVG(purchase_intent_score)::numeric, 1) AS avg_intent,
            COUNT(*) FILTER (WHERE purchase_intent_score >= 70)::int AS hot_leads,
            COUNT(*) FILTER (WHERE satisfaction_final_score >= 80)::int AS happy_customers,
            ROUND(
                (COALESCE(AVG(agent_quality_score), 0) + COALESCE(AVG(satisfaction_final_score), 0)) / 2
            , 1) AS success_score
        FROM call_analyses
        WHERE agent_name IS NOT NULL OR agent_id IS NOT NULL
        GROUP BY agent_name, agent_id
        HAVING COUNT(*) >= 1
        ORDER BY success_score DESC NULLS LAST, total_calls DESC
        LIMIT %s
        """,
        (limit,),
    )


def ready_to_buy(limit: int = 50, offset: int = 0, search: str = "") -> list[dict]:
    params = []
    where_extra = ""
    if search:
        where_extra = "AND (customer_name ILIKE %s OR customer_phone ILIKE %s OR agent_name ILIKE %s)"
        s = f"%{search}%"
        params += [s, s, s]
    params += [limit, offset]
    return fetch_all(
        f"""
        SELECT
            call_id, customer_name, customer_phone, agent_name, department,
            purchase_intent_score, satisfaction_final_score, call_date,
            analysis_json->'sales_analysis'->>'recommended_next_step' AS next_step,
            analysis_json->'sales_analysis'->>'estimated_discount_to_close_percent' AS discount_pct,
            analysis_json->'sales_analysis'->>'estimated_close_probability_percent' AS close_prob,
            analysis_json->'customer'->>'request_summary' AS request_summary,
            ticket_priority
        FROM call_analyses
        WHERE (purchase_intent_score >= 60
           OR (analysis_json->'sales_analysis'->>'purchase_intent_score')::float >= 0.6)
        {where_extra}
        ORDER BY purchase_intent_score DESC NULLS LAST, call_date DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )


def unhappy_customers(limit: int = 50, offset: int = 0, search: str = "") -> list[dict]:
    params = []
    where_extra = ""
    if search:
        where_extra = "AND (customer_name ILIKE %s OR customer_phone ILIKE %s OR agent_name ILIKE %s)"
        s = f"%{search}%"
        params += [s, s, s]
    params += [limit, offset]
    return fetch_all(
        f"""
        SELECT
            call_id, customer_name, customer_phone, agent_name, department,
            satisfaction_final_score, agent_quality_score, needs_human_review, call_date,
            analysis_json->'customer'->>'request_summary' AS request_summary,
            analysis_json->'support_analysis'->>'resolution_status' AS resolution_status,
            analysis_json->'support_analysis'->>'customer_retention_risk' AS retention_risk,
            analysis_json->'ticket'->>'description' AS ticket_description,
            ticket_priority
        FROM call_analyses
        WHERE (satisfaction_final_score < 60
           OR needs_human_review = TRUE
           OR analysis_json->'support_analysis'->>'customer_retention_risk' = 'high'
           OR analysis_json->'customer'->'satisfaction'->>'satisfied' = 'false')
        {where_extra}
        ORDER BY satisfaction_final_score ASC NULLS FIRST, call_date DESC
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )


# ── Staff ────────────────────────────────────────────────────────

def staff_performance() -> list[dict]:
    return fetch_all(
        """
        SELECT
            COALESCE(agent_name, agent_id, 'نامشخص') AS agent_name,
            agent_id, department,
            COUNT(*)::int AS total_calls,
            ROUND(AVG(agent_quality_score)::numeric, 1) AS avg_quality,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            ROUND(AVG(purchase_intent_score)::numeric, 1) AS avg_intent,
            COUNT(*) FILTER (WHERE department = 'sales')::int AS sales_calls,
            COUNT(*) FILTER (WHERE department = 'support')::int AS support_calls,
            COUNT(*) FILTER (WHERE needs_human_review)::int AS review_count
        FROM call_analyses
        GROUP BY agent_name, agent_id, department
        ORDER BY avg_quality DESC NULLS LAST
        """
    )


def staff_call_duration() -> list[dict]:
    return fetch_all(
        """
        SELECT
            COALESCE(agent_name, agent_id, 'نامشخص') AS agent_name,
            agent_id,
            COUNT(*)::int AS total_calls,
            COALESCE(SUM(call_duration_seconds), 0)::int AS total_seconds,
            ROUND(AVG(call_duration_seconds)::numeric, 0) AS avg_seconds,
            ROUND(MAX(call_duration_seconds)::numeric, 0) AS max_seconds
        FROM call_analyses
        GROUP BY agent_name, agent_id
        ORDER BY total_seconds DESC
        """
    )


def staff_satisfaction() -> list[dict]:
    return fetch_all(
        """
        SELECT
            COALESCE(agent_name, agent_id, 'نامشخص') AS agent_name,
            agent_id,
            COUNT(*)::int AS total_calls,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            COUNT(*) FILTER (WHERE satisfaction_final_score >= 80)::int AS satisfied_count,
            COUNT(*) FILTER (WHERE satisfaction_final_score < 60)::int AS unhappy_count,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE satisfaction_final_score >= 70)
                / NULLIF(COUNT(*) FILTER (WHERE satisfaction_final_score IS NOT NULL), 0)
            , 1) AS satisfaction_rate_percent
        FROM call_analyses
        GROUP BY agent_name, agent_id
        ORDER BY satisfaction_rate_percent DESC NULLS LAST
        """
    )


def successful_sales(limit: int = 50, offset: int = 0, search: str = "") -> list[dict]:
    params = []
    where_extra = ""
    if search:
        where_extra = "AND (customer_name ILIKE %s OR customer_phone ILIKE %s OR agent_name ILIKE %s)"
        s = f"%{search}%"
        params += [s, s, s]
    params += [limit, offset]
    return fetch_all(
        f"""
        SELECT
            call_id, customer_name, customer_phone, agent_name,
            purchase_intent_score, satisfaction_final_score, call_date,
            analysis_json->'sales_analysis'->>'purchase_stage' AS purchase_stage,
            analysis_json->'sales_analysis'->>'estimated_close_probability_percent' AS close_prob,
            analysis_json->'customer'->>'request_summary' AS request_summary
        FROM call_analyses
        WHERE department IN ('sales', 'mixed', 'unknown')
          AND (
            purchase_intent_score >= 75
            OR (analysis_json->'sales_analysis'->>'estimated_close_probability_percent')::int >= 50
          )
        {where_extra}
        ORDER BY purchase_intent_score DESC NULLS LAST
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )


# ── Monthly Reports ──────────────────────────────────────────────

def monthly_reports_list(limit: int = 12) -> list[dict]:
    return fetch_all(
        """
        SELECT id, report_month, department, total_calls, created_at
        FROM monthly_reports
        ORDER BY report_month DESC
        LIMIT %s
        """,
        (limit,),
    )


def monthly_report_detail(report_id: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM monthly_reports WHERE id = %s",
        (report_id,),
    )


# ── Recent / Search ──────────────────────────────────────────────

def recent_calls(limit: int = 20) -> list[dict]:
    return fetch_all(
        """
        SELECT call_id, customer_name, agent_name, department,
               purchase_intent_score, satisfaction_final_score,
               agent_quality_score, call_date, ticket_priority, needs_human_review
        FROM call_analyses
        ORDER BY COALESCE(call_date, analyzed_at) DESC
        LIMIT %s
        """,
        (limit,),
    )


def search_calls(q: str, limit: int = 50) -> list[dict]:
    s = f"%{q}%"
    return fetch_all(
        """
        SELECT call_id, customer_name, customer_phone, agent_name, department,
               purchase_intent_score, satisfaction_final_score,
               agent_quality_score, call_date, ticket_priority, needs_human_review
        FROM call_analyses
        WHERE call_id ILIKE %s
           OR customer_name ILIKE %s
           OR customer_phone ILIKE %s
           OR agent_name ILIKE %s
        ORDER BY COALESCE(call_date, analyzed_at) DESC
        LIMIT %s
        """,
        (s, s, s, s, limit),
    )


def call_detail(call_id: str) -> dict | None:
    return fetch_one(
        "SELECT * FROM call_analyses WHERE call_id = %s",
        (call_id,),
    )


def upsert_call_analysis(
    *,
    call_id: str,
    department: str,
    agent_name: str,
    customer_name: str,
    customer_phone: str,
    call_date: str,
    call_direction: str,
    call_duration_seconds: int,
    transcript_text: str,
    analysis: dict,
) -> None:
    """Persist analysis in PostgreSQL (mirrors n8n insert) so reports refresh immediately."""
    analysis = analysis or {}
    sales = analysis.get("sales_analysis") or {}
    customer = analysis.get("customer") or {}
    sat = customer.get("satisfaction") or {}
    agent = analysis.get("agent_performance") or {}
    ticket = analysis.get("ticket") or {}
    qc = analysis.get("quality_control") or {}
    execute(
        """
        INSERT INTO call_analyses (
            call_id, department, agent_id, agent_name, customer_phone, customer_name,
            call_date, call_direction, call_duration_seconds, transcript_text, analysis_json,
            purchase_intent_score, satisfaction_final_score, agent_quality_score,
            ticket_priority, needs_human_review, analyzed_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s::timestamptz, %s, %s, %s, %s::jsonb,
            %s, %s, %s, %s, %s, NOW()
        )
        ON CONFLICT (call_id) DO UPDATE SET
            department = EXCLUDED.department,
            agent_name = EXCLUDED.agent_name,
            customer_phone = EXCLUDED.customer_phone,
            customer_name = EXCLUDED.customer_name,
            call_date = EXCLUDED.call_date,
            call_direction = EXCLUDED.call_direction,
            call_duration_seconds = EXCLUDED.call_duration_seconds,
            transcript_text = EXCLUDED.transcript_text,
            analysis_json = EXCLUDED.analysis_json,
            purchase_intent_score = EXCLUDED.purchase_intent_score,
            satisfaction_final_score = EXCLUDED.satisfaction_final_score,
            agent_quality_score = EXCLUDED.agent_quality_score,
            ticket_priority = EXCLUDED.ticket_priority,
            needs_human_review = EXCLUDED.needs_human_review,
            analyzed_at = NOW()
        """,
        (
            call_id,
            department or "unknown",
            analysis.get("input", {}).get("agent_id") or "",
            agent_name or agent.get("name") or "",
            customer_phone or "",
            customer_name or "",
            call_date,
            call_direction or "inbound",
            int(call_duration_seconds or 0),
            transcript_text or "",
            json.dumps(analysis, ensure_ascii=False),
            sales.get("purchase_intent_score"),
            sat.get("final_score"),
            agent.get("response_quality_score"),
            ticket.get("priority") or "medium",
            bool(qc.get("needs_human_review")),
        ),
    )


def department_breakdown() -> list[dict]:
    return fetch_all(
        """
        SELECT
            COALESCE(department, 'unknown') AS department,
            COUNT(*)::int AS total,
            ROUND(AVG(satisfaction_final_score)::numeric, 1) AS avg_satisfaction,
            ROUND(AVG(purchase_intent_score)::numeric, 1) AS avg_intent
        FROM call_analyses
        GROUP BY department
        ORDER BY total DESC
        """
    )


# ── AI Context ───────────────────────────────────────────────────

def ai_context_payload() -> dict:
    return {
        "overview": overview_stats(),
        "top_performers": top_performers(5),
        "ready_to_buy": ready_to_buy(10),
        "unhappy": unhappy_customers(10),
        "staff_satisfaction": staff_satisfaction()[:10],
        "department_breakdown": department_breakdown(),
        "recent_calls": recent_calls(10),
    }


# ── Settings CRUD ────────────────────────────────────────────────

def get_settings() -> dict[str, str]:
    rows = fetch_all("SELECT key, value FROM panel_settings")
    return {r["key"]: r["value"] for r in rows}


def save_setting(key: str, value: str):
    from .db import get_conn
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO panel_settings (key, value, updated_at)
                   VALUES (%s, %s, NOW())
                   ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=NOW()""",
                (key, value),
            )
        conn.commit()


# ── Alert Rules CRUD ─────────────────────────────────────────────

def list_alert_rules() -> list[dict]:
    return fetch_all("SELECT * FROM alert_rules ORDER BY id")


def save_alert_rule(rule_id: int | None, name: str, rule_type: str,
                    threshold: int, time_window_minutes: int,
                    enabled: bool, email_to: str):
    from .db import get_conn
    with get_conn() as conn:
        with conn.cursor() as cur:
            if rule_id:
                cur.execute(
                    """UPDATE alert_rules SET name=%s, rule_type=%s, threshold=%s,
                       time_window_minutes=%s, enabled=%s, email_to=%s WHERE id=%s""",
                    (name, rule_type, threshold, time_window_minutes, enabled, email_to, rule_id),
                )
            else:
                cur.execute(
                    """INSERT INTO alert_rules (name, rule_type, threshold, time_window_minutes, enabled, email_to)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (name, rule_type, threshold, time_window_minutes, enabled, email_to),
                )
        conn.commit()


def delete_alert_rule(rule_id: int):
    from .db import get_conn
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM alert_rules WHERE id = %s", (rule_id,))
        conn.commit()


def toggle_alert_rule(rule_id: int, enabled: bool):
    from .db import get_conn
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE alert_rules SET enabled=%s WHERE id=%s", (enabled, rule_id))
        conn.commit()


# ── Alert Checking ───────────────────────────────────────────────

def check_alerts() -> list[dict]:
    """Check all active alert rules and return triggered alerts."""
    rules = fetch_all("SELECT * FROM alert_rules WHERE enabled = TRUE")
    triggered = []
    for rule in rules:
        rt = rule["rule_type"]
        th = rule["threshold"]
        tw = rule["time_window_minutes"]

        if rt == "staff_unsatisfied_count":
            rows = fetch_all(
                f"""SELECT agent_name, COUNT(*)::int AS cnt
                    FROM call_analyses
                    WHERE satisfaction_final_score < 60
                      AND analyzed_at >= NOW() - (%s || ' minutes')::interval
                    GROUP BY agent_name HAVING COUNT(*) >= %s""",
                (str(tw or 60), th),
            )
            for r in rows:
                triggered.append({
                    "rule_id": rule["id"], "rule_name": rule["name"],
                    "email_to": rule["email_to"],
                    "subject": f"[هشدار] {rule['name']}: {r['agent_name']}",
                    "body": f"اپراتور {r['agent_name']} در {tw} دقیقه اخیر {r['cnt']} تماس ناراضی داشته است.",
                })

        elif rt == "urgent_ticket":
            rows = fetch_all(
                """SELECT call_id, customer_name, agent_name, ticket_priority
                   FROM call_analyses
                   WHERE ticket_priority = 'urgent' AND needs_human_review = TRUE
                   ORDER BY analyzed_at DESC LIMIT 10""",
            )
            for r in rows:
                triggered.append({
                    "rule_id": rule["id"], "rule_name": rule["name"],
                    "email_to": rule["email_to"],
                    "subject": f"[فوری] تیکت اضطراری - {r['customer_name'] or r['call_id']}",
                    "body": f"تماس {r['call_id']} | مشتری: {r['customer_name']} | اپراتور: {r['agent_name']}",
                })

        elif rt == "low_satisfaction":
            rows = fetch_all(
                """SELECT call_id, customer_name, agent_name, satisfaction_final_score
                   FROM call_analyses
                   WHERE satisfaction_final_score < %s
                   ORDER BY analyzed_at DESC LIMIT 10""",
                (th,),
            )
            for r in rows:
                triggered.append({
                    "rule_id": rule["id"], "rule_name": rule["name"],
                    "email_to": rule["email_to"],
                    "subject": f"[هشدار] رضایت بسیار پایین: {r['customer_name'] or r['call_id']}",
                    "body": f"رضایت {r['satisfaction_final_score']}/100 | مشتری: {r['customer_name']} | اپراتور: {r['agent_name']}",
                })

        elif rt == "hot_lead_no_followup":
            rows = fetch_all(
                f"""SELECT call_id, customer_name, customer_phone, purchase_intent_score
                    FROM call_analyses
                    WHERE purchase_intent_score >= 70
                      AND call_date < NOW() - (%s || ' minutes')::interval
                    ORDER BY call_date DESC LIMIT 10""",
                (str(tw or 1440),),
            )
            if len(rows) >= th:
                triggered.append({
                    "rule_id": rule["id"], "rule_name": rule["name"],
                    "email_to": rule["email_to"],
                    "subject": f"[هشدار] {len(rows)} سرنخ داغ بدون پیگیری",
                    "body": "\n".join(
                        f"- {r['customer_name']} ({r['customer_phone']}): امتیاز {r['purchase_intent_score']}"
                        for r in rows
                    ),
                })

    return triggered


# ── Helpers ──────────────────────────────────────────────────────

def _date_filter(date_from, date_to) -> tuple[str, list]:
    """Return (WHERE clause, params) — parameterized to prevent injection."""
    clauses, params = [], []
    if date_from:
        clauses.append("call_date >= %s::timestamptz")
        params.append(date_from)
    if date_to:
        clauses.append("call_date < %s::timestamptz")
        params.append(date_to)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params
