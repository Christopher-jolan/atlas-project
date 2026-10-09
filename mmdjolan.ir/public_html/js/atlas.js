(function(){
    // ── API endpoint resolution ──────────────────────────────────
    // Override by defining window.ATLAS_API_OVERRIDE before this script,
    // or by setting localStorage.atlas_api (useful when the panel is
    // reachable through a tunnel / reverse proxy instead of :8080).
    const host = window.location.hostname;
    const port = window.location.port || "";
    const stored = (function(){ try { return localStorage.getItem("atlas_api"); } catch(e){ return null; } })();
    const LOCAL_PANEL = "http://localhost:8080";
    const REMOTE_PANEL = "https://atlas.mmdjolan.ir";
    const isLocalHost = host === "localhost" || host === "127.0.0.1";
    // Static preview (e.g. :8766) talks to the live panel; use localStorage atlas_api for Docker on :8080.
    const defaultApi = isLocalHost
        ? (port === "8080" ? LOCAL_PANEL : REMOTE_PANEL)
        : REMOTE_PANEL;
    const ATLAS_API = window.ATLAS_API_OVERRIDE || stored || defaultApi;

    window.ATLAS_API = ATLAS_API;

    const MAX_FILES = 10;
    const MAX_MB = 25;

    function lang(){ return localStorage.getItem("lang") || "en"; }
    function t(fa, en){ return lang() === "fa" ? fa : en; }
    function esc(s){
        return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
            ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
    }
    function formatDetail(detail){
        if(detail == null || detail === "") return "";
        if(typeof detail === "string") return detail;
        if(Array.isArray(detail)){
            return detail.map(function(item){
                if(typeof item === "string") return item;
                return (item && (item.msg || item.message)) || "";
            }).filter(Boolean).join(" ");
        }
        if(typeof detail === "object") return detail.msg || detail.message || "";
        return String(detail);
    }
    function departmentLabel(d){
        if(d.department_label) return d.department_label;
        const dep = (d.department || "").toLowerCase();
        if(dep === "sales") return t("فروش", "Sales");
        if(dep === "support") return t("پشتیبانی", "Support");
        if(dep === "auto") return t("تشخیص خودکار", "Auto detect");
        if(!dep) return "—";
        return d.department;
    }

    function cloneFile(file){
        try {
            return new File([file], file.name, {
                type: file.type || "application/octet-stream",
                lastModified: file.lastModified
            });
        } catch (err) {
            return file;
        }
    }

    // ── Live stats (dashboard page) ──────────────────────────────
    function initDashboardStats(){
        const grid = document.getElementById("stats-preview");
        if(!grid) return;

        const statusEl = document.getElementById("stats-status");
        const set = (id, val) => {
            const el = document.getElementById(id);
            if(el) el.textContent = val == null ? "—" : val;
        };

        function load(){
            fetch(`${ATLAS_API}/api/stats`, { cache: "no-store" })
                .then(r => r.ok ? r.json() : Promise.reject(r.status))
                .then(data => {
                    set("stat-calls", data.total_calls ?? data.total ?? 0);
                    set("stat-satisfaction", data.avg_satisfaction != null ? Math.round(data.avg_satisfaction) : null);
                    set("stat-intent", data.avg_purchase_intent != null ? Math.round(data.avg_purchase_intent) : null);
                    set("stat-quality", data.avg_agent_quality != null ? Math.round(data.avg_agent_quality) : null);
                    set("stat-hot", data.hot_leads ?? null);
                    set("stat-unhappy", data.unhappy_count ?? null);
                    if(statusEl){
                        statusEl.classList.remove("status-error");
                        statusEl.textContent = t(
                            "✅ داده‌ها زنده از پنل خوانده شد — " + new Date().toLocaleTimeString("fa-IR"),
                            "✅ Live data loaded — " + new Date().toLocaleTimeString()
                        );
                    }
                })
                .catch(() => {
                    if(statusEl){
                        statusEl.classList.add("status-error");
                        statusEl.textContent = t(
                            "⚠️ پنل در دسترس نیست — مطمئن شوید Docker روی پورت 8080 در حال اجراست.",
                            "⚠️ Panel unavailable — ensure the Docker panel is running on port 8080."
                        );
                    }
                });
        }

        load();
        setInterval(load, 30000);
    }

    // ── Recent calls table (dashboard page) ──────────────────────
    function initRecentCalls(){
        const tbody = document.getElementById("recent-calls-body");
        if(!tbody) return;

        function loadRecent(){
        fetch(`${ATLAS_API}/api/recent-calls?limit=10`, { cache: "no-store" })
            .then(r => r.ok ? r.json() : Promise.reject(r.status))
            .then(rows => {
                if(!Array.isArray(rows) || !rows.length){
                    tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">${t("تماسی ثبت نشده","No calls recorded yet")}</td></tr>`;
                    return;
                }
                tbody.innerHTML = rows.map(c => `
                    <tr>
                        <td><code>${esc(String(c.call_id).slice(0,18))}</code></td>
                        <td>${esc(c.customer_name || "—")}</td>
                        <td>${esc(c.agent_name || "—")}</td>
                        <td><span class="mini-badge">${esc(c.department || "—")}</span></td>
                        <td>${c.satisfaction_final_score ?? "—"}</td>
                        <td>${c.purchase_intent_score ?? "—"}</td>
                    </tr>`).join("");
            })
            .catch(() => {
                tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">${t("خطا در دریافت داده","Failed to load data")}</td></tr>`;
            });
        }
        loadRecent();
        setInterval(loadRecent, 30000);
    }

    // ── Upload (upload page) ─────────────────────────────────────
    function initUpload(){
        const form = document.getElementById("atlas-upload-form");
        if(!form) return;

        const dropZone = document.getElementById("drop-zone");
        const fileInput = document.getElementById("audio-file");
        const browseBtn = document.getElementById("browse-btn");
        const fileInfo = document.getElementById("file-info");
        const submitBtn = document.getElementById("submit-btn");
        const progressBox = document.getElementById("upload-progress");
        const progressFill = document.getElementById("progress-fill");
        const progressText = document.getElementById("progress-text");
        const resultBox = document.getElementById("upload-result");
        const errorBox = document.getElementById("upload-error");

        let selected = [];

        function formatSize(bytes){
            if(bytes < 1024) return bytes + " B";
            if(bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
            return (bytes / 1048576).toFixed(1) + " MB";
        }

        function renderFiles(){
            if(!selected.length){
                fileInfo.classList.add("hidden");
                fileInfo.innerHTML = "";
                submitBtn.disabled = true;
                dropZone.classList.remove("has-file");
                return;
            }
            fileInfo.classList.remove("hidden");
            fileInfo.innerHTML = selected.map((f, i) =>
                `<div class="file-row"><span class="file-name">${esc(f.name)}</span>` +
                `<span class="file-size">${formatSize(f.size)}</span>` +
                `<button type="button" class="file-remove" data-idx="${i}" aria-label="remove">✕</button></div>`
            ).join("");
            submitBtn.disabled = false;
            dropZone.classList.add("has-file");
        }

        fileInfo.addEventListener("click", e => {
            const btn = e.target.closest(".file-remove");
            if(!btn) return;
            selected.splice(Number(btn.dataset.idx), 1);
            renderFiles();
        });

        function addFiles(list){
            errorBox.classList.add("hidden");
            const rejected = [];
            for(const f of list){
                if(selected.length >= MAX_FILES){ rejected.push(`${f.name} (${t("سقف تعداد","file limit")})`); continue; }
                if(f.size > MAX_MB * 1048576){ rejected.push(`${f.name} (>${MAX_MB}MB)`); continue; }
                if(selected.some(s => s.name === f.name && s.size === f.size)) continue;
                selected.push(cloneFile(f));
            }
            renderFiles();
            if(rejected.length){
                errorBox.classList.remove("hidden");
                errorBox.textContent = t("رد شد: ", "Rejected: ") + rejected.join(", ");
            }
        }

        browseBtn.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", () => {
            addFiles(Array.from(fileInput.files || []));
            fileInput.value = "";
        });

        ["dragenter","dragover"].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
        });
        ["dragleave","drop"].forEach(evt => {
            dropZone.addEventListener(evt, e => { e.preventDefault(); dropZone.classList.remove("drag-over"); });
        });
        dropZone.addEventListener("drop", e => addFiles(Array.from(e.dataTransfer.files || [])));
        dropZone.addEventListener("keydown", e => {
            if(e.key === "Enter" || e.key === " "){ e.preventDefault(); fileInput.click(); }
        });

        const ORDER = ["upload","transcribe","analyze","done"];
        function setStep(step){
            document.querySelectorAll(".progress-step").forEach(el => {
                el.classList.toggle("active", el.dataset.step === step);
                el.classList.toggle("done", ORDER.indexOf(el.dataset.step) < ORDER.indexOf(step));
            });
        }
        function setProgress(pct, text){
            progressFill.style.width = pct + "%";
            if(text) progressText.textContent = text;
        }

        function scoreClass(v){
            if(v == null) return "";
            return v >= 70 ? "score-good" : v >= 45 ? "score-mid" : "score-bad";
        }

        function renderOne(d, meta){
            meta = meta || {};
            if(d && d.success === false){
                return `<div class="result-card"><div class="atlas-error" style="margin:0">${esc(d.filename ? d.filename + " — " : "")}${esc(d.error || t("تحلیل ناموفق بود.","Analysis failed."))}</div></div>`;
            }
            const deptLabel = esc(departmentLabel(d));
            const s = d.scores || {};
            const title = d.filename || t("تحلیل تماس آماده است","Call analysis is ready");
            return `
                <div class="result-card">
                    <div class="result-header">
                        <strong>${esc(title)}</strong>
                        ${d.call_id ? `<code>${esc(d.call_id)}</code>` : ""}
                        <span class="mini-badge">${t("نوع تماس","Call type")}: ${deptLabel}</span>
                        ${d.priority_label && d.priority_label !== "—" ? `<span class="mini-badge">${t("اولویت","Priority")}: ${esc(d.priority_label)}</span>` : ""}
                    </div>
                    <div class="result-grid">
                        ${meta.agent ? `<div class="result-item"><span class="result-label">${t("اپراتور","Agent")}</span><span class="result-value">${esc(meta.agent)}</span></div>` : ""}
                        ${meta.customer ? `<div class="result-item"><span class="result-label">${t("مشتری","Customer")}</span><span class="result-value">${esc(meta.customer)}</span></div>` : ""}
                        <div class="result-item"><span class="result-label">${t("نوع تماس","Call type")}</span><span class="result-value">${deptLabel}</span></div>
                        <div class="result-item"><span class="result-label">${t("رضایت","Satisfaction")}</span><span class="result-value ${scoreClass(s.satisfaction)}">${s.satisfaction ?? "—"}/100</span></div>
                        <div class="result-item"><span class="result-label">${t("تمایل خرید","Purchase Intent")}</span><span class="result-value ${scoreClass(s.purchase_intent)}">${s.purchase_intent ?? "—"}/100</span></div>
                        <div class="result-item"><span class="result-label">${t("کیفیت اپراتور","Agent Quality")}</span><span class="result-value ${scoreClass(s.agent_quality)}">${s.agent_quality ?? "—"}/100</span></div>
                    </div>
                    ${d.summary ? `<p class="result-summary"><strong>${t("خلاصه تماس:","Call summary:")}</strong> ${esc(d.summary)}</p>` : ""}
                    ${(d.actions || []).length ? `<p class="result-summary"><strong>${t("اقدامات پیش رو:","Next actions:")}</strong></p><ol class="result-actions">${d.actions.map(a => `<li>${esc(a)}</li>`).join("")}</ol>` : ""}
                    ${d.call_id ? `<div class="center-actions" style="margin-top:.85rem;">
                        <a class="btn btn-sm" href="${ATLAS_API}/calls/${encodeURIComponent(d.call_id)}" target="_blank" rel="noopener">${t("مشاهده در پنل","View in Panel")}</a>
                    </div>` : ""}
                </div>`;
        }

        function postUpload(url, fd, onProgress, onUploadDone){
            return new Promise(function(resolve, reject){
                const xhr = new XMLHttpRequest();
                xhr.open("POST", url);
                xhr.timeout = 600000;
                xhr.upload.onprogress = function(ev){
                    if(ev.lengthComputable && onProgress) onProgress(ev.loaded, ev.total);
                };
                xhr.upload.onloadend = function(){
                    if(onUploadDone) onUploadDone();
                };
                xhr.onload = function(){
                    let data = {};
                    try { data = JSON.parse(xhr.responseText || "{}"); }
                    catch (err) {
                        reject(new Error(xhr.responseText ? String(xhr.responseText).slice(0, 180) : ("HTTP " + xhr.status)));
                        return;
                    }
                    if(xhr.status >= 400){
                        reject(new Error(formatDetail(data.detail || data.error) || ("HTTP " + xhr.status)));
                        return;
                    }
                    resolve(data);
                };
                xhr.onerror = function(){
                    reject(new Error(t("ارتباط با پنل اطلس برقرار نشد.","Could not reach the Atlas panel.")));
                };
                xhr.ontimeout = function(){
                    reject(new Error(t("زمان تحلیل تمام شد. دوباره تلاش کنید.","The analysis timed out. Please try again.")));
                };
                xhr.send(fd);
            });
        }

        async function postUploadRetry(url, fd, hooks){
            const tries = 3;
            let lastErr;
            for(let i = 0; i < tries; i++){
                try {
                    return await postUpload(url, fd, hooks.onProgress, hooks.onUploadDone);
                } catch(err) {
                    lastErr = err;
                    const msg = err.message || "";
                    const retryable = /برقرار نشد|Could not reach|Failed|network|timeout|HTTP 5/i.test(msg);
                    if(!retryable || i === tries - 1) throw err;
                    await new Promise(r => setTimeout(r, 1200 * (i + 1)));
                    hooks.onRetry && hooks.onRetry(i + 1);
                }
            }
            throw lastErr;
        }

        form.addEventListener("submit", async e => {
            e.preventDefault();
            if(!selected.length) return;

            resultBox.classList.add("hidden");
            resultBox.innerHTML = "";
            errorBox.classList.add("hidden");
            progressBox.classList.remove("hidden");
            submitBtn.disabled = true;

            const agentName = document.getElementById("agent-name").value;
            const customerName = document.getElementById("customer-name").value;
            const department = document.getElementById("department").value;
            const meta = { agent: agentName, customer: customerName };
            const fd = new FormData();
            const batch = selected.length > 1;
            if(batch){
                selected.forEach(f => fd.append("files", f, f.name));
            } else {
                fd.append("file", selected[0], selected[0].name);
            }
            fd.append("agent_name", agentName);
            fd.append("customer_name", customerName);
            fd.append("department", department);

            let waitTimer = null;
            function clearWait(){ if(waitTimer){ clearInterval(waitTimer); waitTimer = null; } }
            function phase( step, pct, text ){
                setStep(step);
                setProgress(Math.max(0, Math.min(100, pct)), text);
            }
            function startWait(step, text, cap){
                clearWait();
                let p = 8;
                phase(step, p, text);
                waitTimer = setInterval(function(){
                    p = Math.min(cap, p + 3);
                    phase(step, p, text);
                    if(p >= cap) clearWait();
                }, 1400);
            }

            phase("upload", 0, t(`در حال آپلود ${selected.length} فایل…`, `Uploading ${selected.length} file(s)…`));

            try {
                const data = await postUploadRetry(
                    `${ATLAS_API}${batch ? "/api/upload-batch" : "/api/upload-voice"}`,
                    fd,
                    {
                        onProgress: function(loaded, total){
                            const pct = Math.round(loaded / total * 100);
                            phase("upload", pct, t("ارسال فایل… " + pct + "٪", "Uploading… " + pct + "%"));
                        },
                        onUploadDone: function(){
                            phase("upload", 100, t("ارسال فایل کامل شد.", "Upload complete."));
                            startWait("transcribe", t("رونویسی با هوش مصنوعی…","Transcribing with AI…"), 88);
                        },
                        onRetry: function(n){
                            phase("upload", 0, t("تلاش مجدد اتصال… (" + n + ")", "Retrying connection… (" + n + ")"));
                        }
                    }
                );
                clearWait();
                phase("analyze", 100, t("تحلیل تماس…","Analyzing call…"));
                phase("done", 100, t("تحلیل کامل شد!","Analysis complete!"));

                resultBox.classList.remove("hidden");
                if(batch){
                    const rows = data.results || [];
                    resultBox.innerHTML =
                        `<div class="batch-summary">${t("نتیجه:","Result:")} ${data.succeeded}/${data.total} ${t("موفق","succeeded")}</div>` +
                        rows.map(r => renderOne(r, meta)).join("") +
                        `<div class="center-actions" style="margin-top:1rem;"><a class="btn btn-outline" href="dashboard.html">${t("داشبورد","Dashboard")}</a></div>`;
                } else {
                    resultBox.innerHTML = renderOne(data, meta) +
                        `<div class="center-actions" style="margin-top:1rem;"><a class="btn btn-outline" href="dashboard.html">${t("داشبورد","Dashboard")}</a></div>`;
                }
                selected = [];
                renderFiles();
            } catch(err) {
                clearWait();
                errorBox.classList.remove("hidden");
                errorBox.textContent = t("خطا: ","Error: ") + (err.message || String(err));
                progressBox.classList.add("hidden");
            } finally {
                submitBtn.disabled = selected.length === 0;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        const panelLink = document.getElementById("panel-link");
        if (panelLink) panelLink.href = ATLAS_API + "/";
        const aiLink = document.querySelector('a[href*="ai-insights"]');
        if (aiLink) aiLink.href = ATLAS_API + "/ai-insights";
        const n8nLink = document.getElementById("n8n-link");
        if (n8nLink) n8nLink.href = "http://141.11.21.147:5678/";
        const uploadPanel = document.getElementById("panel-upload-link");
        if (uploadPanel) uploadPanel.href = ATLAS_API + "/upload";
        initDashboardStats();
        initRecentCalls();
        initUpload();
    });
})();
