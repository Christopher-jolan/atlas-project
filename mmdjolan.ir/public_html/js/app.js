(function () {
  try {
    var t = localStorage.getItem("theme");
    if (!t) t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", t);
  } catch (e) {}
})();

const languageData = {
    en: {
        title: "Mohamad Reza Jolan Zadeh",
        description: "Mohamad Reza Jolan Zadeh — Python, Full Stack & AI Developer.",
        dir: "ltr",
        button: "🇮🇷 ترجمه",
        brandTag: "Python · Full Stack · AI",
        nav: {
            home: "Home",
            about: "About",
            skills: "Skills",
            experience: "Experience",
            projects: "Projects",
            contact: "Contact",
            chat: "Chat"
        },
        footerCopy: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir",
        indexChat: "Private Chat",
        contactEmail: "Email",
        contactSite: "Website",
        contactChat: "Encrypted chat",
        pageTitle: "Mohamad Reza Jolan Zadeh",
        index: {
            heroMeta: "25 Years Old · Tehran / Ahvaz · Available for Remote & On-site",
            projectsButton: "View Projects",
            aboutTitle: "About",
            aboutLead: "Computer Engineering Graduate — Jundi Shapur University of Dezful",
            aboutText: "Python Developer · Full Stack Developer · AI Developer",
            experienceTitle: "Experience",
            exp1: "Support Manager",
            exp1Company: "Atiran Software",
            exp2: "IT Help Desk (Intern)",
            exp2Company: "National Iranian South Oil Company",
            skillsTitle: "Skills",
            programming: "Programming",
            frameworks: "Frameworks",
            frontend: "Frontend",
            backend: "Backend",
            certTitle: "Certificates",
            cert1: "Python Certificate",
            certCompany: "Harvard University",
            contactTitle: "Contact",
            contactText: "GitHub · LinkedIn · Email",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        projects: {
            pageTitle: "Projects | Mohamad Reza Jolan Zadeh",
            pageDescription: "Mohamad Reza Jolan Zadeh projects — AI chatbots, Laravel, WooCommerce.",
            heroTitle: "My Projects",
            heroText: "Five real software development projects",
            card1Title: "Saman Bank Chatbot",
            card1Desc: "Smart assistant that answers Saman Bank customer questions with trainable AI.",
            card2Title: "Atiran Support Assistant",
            card2Desc: "Local support chatbot installed beside the Atiran accounting software.",
            card3Title: "University Sports Booking System",
            card3Desc: "Booking platform with team creation and team joining for university sports halls.",
            card4Title: "Honey Shop Online Store",
            card4Desc: "WooCommerce online store for a honey business with custom design and checkout.",
            card5Title: "Atlas — Call Analytics & Automation",
            card5Desc: "Comprehensive call center intelligence platform with AI-driven insights, workflow automation, and live performance monitoring.",
            projectLink: "View Project",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        atiran: {
            pageTitle: "Atiran Support Assistant | Projects",
            pageDescription: "Atiran local support assistant — Python chatbot deployed on customer servers.",
            heroSub: "2 · Python · Support Automation",
            heroTitle: "Atiran Local Support Assistant",
            heroDesc: "Local chatbot installed next to Atiran accounting software to solve user issues without helpdesk calls.",
            backLink: "← Back to Projects",
            section1Title: "Problem & Solution",
            problemTitle: "High Support Call Volume",
            problemDesc: "Atiran users had to contact support for simple repeated issues, wasting time and resources.",
            solutionTitle: "Local Intelligent Assistant",
            solutionDesc: "The chatbot installs on the customer server and answers accurately without internet or helpdesk calls.",
            section2Title: "Unique Features",
            feature1Title: "Local Deployment",
            feature1Desc: "Unlike cloud bots, this assistant runs on the customer server and never sends data externally.",
            feature2Title: "Atiran Accounting Knowledge",
            feature2Desc: "The model is trained on Atiran-specific product knowledge, common errors and solutions.",
            feature3Title: "Integration with Atiran UI",
            feature3Desc: "Users can ask questions from inside the software, with the assistant directly available in the interface.",
            feature4Title: "Reduced Support Pressure",
            feature4Desc: "Automatic answers to frequent problems significantly reduce helpdesk workload.",
            section3Title: "Technologies",
            viewProject: "View Project",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        saman: {
            pageTitle: "Saman Bank Chatbot | Projects",
            pageDescription: "Saman Bank AI chatbot with NLP training and instant customer support.",
            heroSub: "1 · Python · AI",
            heroTitle: "Saman Bank Chatbot",
            heroDesc: "Smart assistant for Saman Bank customers with trained, accurate replies.",
            backLink: "← Back to Projects",
            section1Title: "Key Features",
            feature1Title: "Trainable AI",
            feature1Desc: "The system learns from new data to deliver more accurate answers.",
            feature2Title: "Intelligent Replies",
            feature2Desc: "It understands common bank customer questions and responds appropriately.",
            feature3Title: "Continuous Improvement",
            feature3Desc: "Quality improves over time with each new interaction.",
            feature4Title: "Instant Answers",
            feature4Desc: "Users receive immediate responses without waiting in a queue.",
            section2Title: "How It Works",
            step1Title: "Receive Customer Question",
            step1Desc: "The user types a question into Persian like ‘How do I unblock my card?’.",
            step2Title: "Smart Processing",
            step2Desc: "The language model processes the query and retrieves the best answer from the knowledge base.",
            step3Title: "Deliver Accurate Response",
            step3Desc: "The assistant provides a precise reply with step-by-step guidance if needed.",
            step4Title: "Update Model",
            step4Desc: "New interactions improve the model over time for better future answers.",
            section3Title: "Technologies Used",
            techDesc: "Demo and source code will be available soon.",
            viewProject: "View Live Project",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        sports: {
            pageTitle: "University Sports Booking | Projects",
            pageDescription: "University sports hall booking system with team creation and slot reservation.",
            heroSub: "3 · Laravel · University Project",
            heroTitle: "University Sports Booking System",
            heroDesc: "Smart booking platform for student sports slots with team creation and joining.",
            backLink: "← Back to Projects",
            section1Title: "User Roles",
            role1Title: "Student",
            role1Desc: "Book slots, create a team or search for teams to join.",
            role2Title: "Team Captain",
            role2Desc: "Manage the team and approve or reject membership requests.",
            role3Title: "Hall Admin",
            role3Desc: "Manage schedules, capacities and weekly sports hall planning.",
            section2Title: "Usage Flow",
            step1Title: "View Available Slots",
            step1Desc: "Students see the weekly sports hall schedule and open slot availability.",
            step2Title: "Choose and Reserve",
            step2Desc: "Select a session and reserve it with instant confirmation.",
            step3Title: "Create or Join Teams",
            step3Desc: "Users can create a team or request to join teams that are looking for members.",
            step4Title: "Captain Approval",
            step4Desc: "The team captain approves or rejects membership requests.",
            step5Title: "Manage Reservations",
            step5Desc: "Active reservations are shown with options to cancel or transfer bookings.",
            section3Title: "Unique Feature",
            featureTitle: "Smart Team Matching",
            featureDesc: "Solo students can find open teams and request to join, so they are never left without a partner.",
            section4Title: "Technologies",
            viewProject: "View Project",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        honey: {
            pageTitle: "Honey Shop Online Store | Projects",
            pageDescription: "WooCommerce honey shop website with custom design and online sales.",
            heroSub: "4 · WordPress · WooCommerce",
            heroTitle: "Honey Shop Online Store",
            heroDesc: "Complete e-commerce site for a honey business with design, payments and product management.",
            backLink: "← Back to Projects",
            section1Title: "Delivery",
            item1Title: "Custom Visual Design",
            item1Desc: "Warm, natural brand style matching honey and bee visuals.",
            item2Title: "Online Store",
            item2Desc: "Complete sales system with cart, checkout and order management.",
            item3Title: "Fully Responsive",
            item3Desc: "Optimized for mobile, tablet and desktop screens.",
            item4Title: "Simple Admin Panel",
            item4Desc: "The owner can manage products, prices and stock without technical help.",
            section2Title: "Site Pages",
            page1Title: "Home Page",
            page1Desc: "Intro, featured products and promotional banners.",
            page2Title: "Shop",
            page2Desc: "Product listing with type and price filters.",
            page3Title: "About",
            page3Desc: "Business story, history and values.",
            page4Title: "Blog",
            page4Desc: "Articles about honey, varieties and beekeeping.",
            page5Title: "Contact",
            page5Desc: "Contact form, address and support details.",
            section3Title: "Technologies",
            featureTitle: "Complete Non-Technical Buyer Solution",
            featureDesc: "The owner can add new products, change prices and follow orders without technical knowledge.",
            viewProject: "View Website",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir",
            shopTitle: "A taste of the store",
            shopLead: "Custom product cards, cart and checkout — designed around honey, not a generic theme.",
            prod1: "Mountain honey",
            prod2: "Sidr honey",
            prod3: "Thyme honey",
            prod4: "Royal jelly",
            prodPrice: "From the shop",
            kpiOrders: "Online orders",
            kpiMobile: "Mobile ready",
            kpiAdmin: "Owner-managed",
            payTitle: "From jar to checkout",
            pay1Title: "Browse",
            pay1Desc: "Filter by type, weight and price.",
            pay2Title: "Cart",
            pay2Desc: "Quantity, notes and gift wrap.",
            pay3Title: "Pay",
            pay3Desc: "Iranian payment gateway and SMS of the order."
        },
        atlas: {
            pageTitle: "Atlas — Call Analytics & Automation | Projects",
            pageDescription: "AI-powered call center management with PostgreSQL, n8n automation, and real-time analytics dashboard.",
            heroSub: "5 · Python · PostgreSQL · n8n · Real-time Analytics",
            heroTitle: "Atlas — Call Analytics & Automation",
            heroDesc: "Comprehensive call center intelligence platform with AI-driven insights, workflow automation, and live performance monitoring.",
            backLink: "← Back to Projects",
            hubTitle: "Atlas Project Hub",
            hubDesc: "Explore all Atlas modules — upload voice calls for AI analysis, access the analytics dashboard, manage workflows, and review the architecture.",
            hubUploadNum: "Module 1 · Voice Analysis",
            hubUploadTitle: "Upload & Analyze Calls",
            hubUploadDesc: "Upload a voice recording and run the full Atlas pipeline — transcription, AI analysis, database storage, and manager notification.",
            hubDashNum: "Module 2 · Analytics",
            hubDashTitle: "Analytics Dashboard",
            hubDashDesc: "Real-time KPIs, agent performance, customer satisfaction, sales pipeline, and AI executive insights.",
            hubFlowNum: "Module 3 · Automation",
            hubFlowTitle: "n8n Workflows",
            hubFlowDesc: "Automated call intelligence pipeline — webhook triggers, AI analysis, email dispatch, and monthly reports.",
            hubArchNum: "Module 4 · Architecture",
            hubArchTitle: "System Architecture",
            hubArchDesc: "Technology stack, data flow, Docker infrastructure, and security design of the Atlas platform.",
            hubOpen: "Open →",
            section1Title: "Problem & Solution",
            problemTitle: "Manual Call Analysis Burden",
            problemDesc: "Call centers struggle with manual data analysis, slow reporting, inconsistent quality tracking, and no predictive insights for customer satisfaction.",
            solutionTitle: "Automated Intelligence Pipeline",
            solutionDesc: "Atlas captures, analyzes, and categorizes call data in real-time with AI insights, automated workflow triggers, and predictive analytics—all accessible from an intuitive dashboard.",
            section2Title: "Core Features",
            feature1Title: "Live Analytics Dashboard",
            feature1Desc: "Real-time KPI monitoring, agent performance, customer satisfaction scores, and automated 30-day trend analysis.",
            feature2Title: "AI-Powered Insights",
            feature2Desc: "Gemini AI analyzes calls to identify hot leads, unhappy customers, successful sales patterns, and actionable recommendations.",
            feature3Title: "Workflow Automation",
            feature3Desc: "n8n orchestrates automated processes triggered by call outcomes—follow-ups, escalations, and data enrichment.",
            feature5Title: "Voice Upload & Analysis",
            feature5Desc: "Upload call recordings directly from the web — automatic transcription, AI analysis, and instant results.",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        atlasUpload: {
            pageTitle: "Atlas — Upload & Analyze | Voice Analysis",
            pageDescription: "Upload voice call recordings for Atlas AI analysis — transcription, insights, and automated reporting.",
            navAtlas: "Atlas Hub",
            subnavHome: "🛰️ Atlas Hub",
            subnavUpload: "🎙️ Upload",
            subnavDashboard: "📊 Dashboard",
            subnavWorkflows: "🤖 Workflows",
            subnavArchitecture: "🏗️ Architecture",
            heroSub: "Voice Upload · AI Transcription · Call Intelligence",
            heroTitle: "Upload & Analyze Calls",
            heroDesc: "Upload a voice recording to run the full Atlas pipeline — transcription, AI analysis, database storage, and manager email notification.",
            backLink: "← Back to Atlas Hub",
            uploadTitle: "Voice File Upload",
            dropTitle: "Drag & drop your call recording here",
            dropHint: "Supported: MP3, M4A, WAV, OGG, WEBM — max 25 MB",
            browseBtn: "Browse Files",
            agentLabel: "Agent Name",
            agentPlaceholder: "Ali Rezaei",
            customerLabel: "Customer Name",
            customerPlaceholder: "Alpha Company",
            deptLabel: "Department",
            deptAuto: "Auto Detect",
            deptSales: "Sales",
            deptSupport: "Support",
            submitBtn: "Start Analysis",
            stepUpload: "Uploading",
            stepTranscribe: "Transcribing",
            stepAnalyze: "Analyzing",
            stepDone: "Complete",
            howTitle: "How It Works",
            how1Title: "Upload Recording",
            how1Desc: "Select or drag a call recording file from your device.",
            how2Title: "AI Transcription",
            how2Desc: "Gemini AI transcribes the Persian conversation with speaker labels.",
            how3Title: "Call Intelligence",
            how3Desc: "n8n workflow analyzes sentiment, sales intent, agent quality, and generates a ticket.",
            how4Title: "Results & Dashboard",
            how4Desc: "Results are saved to PostgreSQL and visible in the analytics dashboard.",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        atlasDashboard: {
            pageTitle: "Atlas — Analytics Dashboard",
            pageDescription: "Atlas Call Intelligence analytics dashboard — KPIs, agent performance, and AI insights.",
            navAtlas: "Atlas Hub",
            subnavHome: "🛰️ Atlas Hub",
            subnavUpload: "🎙️ Upload",
            subnavDashboard: "📊 Dashboard",
            subnavWorkflows: "🤖 Workflows",
            subnavArchitecture: "🏗️ Architecture",
            heroSub: "Real-time KPIs · Agent Performance · AI Insights",
            heroTitle: "Analytics Dashboard",
            heroDesc: "Live call center analytics powered by PostgreSQL — monitor performance, identify opportunities, and track customer satisfaction.",
            backLink: "← Back to Atlas Hub",
            accessTitle: "Dashboard Access",
            accessDesc: "The analytics panel runs as a Docker service on port 8080. Click below to open the full dashboard in a new tab.",
            openPanel: "Open Analytics Panel",
            openAI: "AI Executive Insights",
            accessNote: "💡 The panel displays live data from analyzed calls. Upload new recordings from the Upload page to see fresh results.",
            featuresTitle: "Dashboard Features",
            feat1Title: "Overview KPIs",
            feat1Desc: "Total calls, average satisfaction, purchase intent, and agent quality scores with 30-day trends.",
            feat2Title: "Top Performers",
            feat2Desc: "Rank agents by response quality, communication skills, and customer satisfaction.",
            feat3Title: "Ready to Buy",
            feat3Desc: "Hot leads with high purchase intent — prioritized for follow-up.",
            feat4Title: "Unhappy Customers",
            feat4Desc: "Calls with low satisfaction scores requiring immediate attention.",
            feat5Title: "Monthly Reports",
            feat5Desc: "Automated monthly executive summaries with trends and recommendations.",
            feat6Title: "Search & Export",
            feat6Desc: "Full-text search across transcripts and CSV export for all reports.",
            liveStatsTitle: "Live Stats Preview",
            statCalls: "Total Calls",
            statSat: "Avg Satisfaction",
            statIntent: "Avg Purchase Intent",
            statQuality: "Avg Agent Quality",
            statsLoading: "Loading live stats from panel…",
            recentCallsTitle: "Recent Calls",
            colCallId: "Call ID",
            colCustomer: "Customer",
            colAgent: "Agent",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        atlasWorkflows: {
            pageTitle: "Atlas — n8n Workflows",
            pageDescription: "Atlas n8n workflow automation — call intelligence pipeline, webhooks, and monthly reports.",
            navAtlas: "Atlas Hub",
            subnavHome: "🛰️ Atlas Hub",
            subnavUpload: "🎙️ Upload",
            subnavDashboard: "📊 Dashboard",
            subnavWorkflows: "🤖 Workflows",
            subnavArchitecture: "🏗️ Architecture",
            heroSub: "n8n · Webhooks · Automated Pipeline",
            heroTitle: "Workflow Automation",
            heroDesc: "n8n orchestrates the Atlas call intelligence pipeline — from webhook trigger to AI analysis, database storage, and email notification.",
            backLink: "← Back to Atlas Hub",
            accessTitle: "n8n Access",
            accessDesc: "The workflow engine runs on port 5678 with Basic Auth enabled. Use the button below to open the n8n editor.",
            openN8n: "Open n8n Editor",
            accessNote: "🔒 Basic Auth is enabled. Credentials are configured in docker-compose.yml.",
            pipelineTitle: "Call Intelligence Pipeline",
            pipe1Title: "Webhook Trigger",
            pipe1Desc: "POST /webhook/atlas/call-intelligence receives transcript or audio URL with call metadata.",
            pipe2Title: "AI Analysis",
            pipe2Desc: "LLM analyzes the transcript for sentiment, sales intent, agent quality, and generates a CRM ticket.",
            pipe3Title: "Save to PostgreSQL",
            pipe3Desc: "Structured analysis JSON is stored in call_analyses table for dashboard queries.",
            pipe4Title: "Manager Email",
            pipe4Desc: "Automated ticket email sent via the mailer service to the configured manager address.",
            webhooksTitle: "Webhook Endpoints",
            wh1Title: "Call Intelligence",
            wh1Desc: "Primary pipeline — accepts transcript + metadata, returns full analysis JSON.",
            wh2Title: "Monthly Report",
            wh2Desc: "Generates monthly executive summary. Also triggered by cron on the 1st of each month.",
            workflowsTitle: "Active Workflows",
            wf1Desc: "Full Persian call analysis with sales/support detection, ticket generation, DB save, and email.",
            wf2Desc: "Aggregates monthly call data into executive summary with trends and recommendations.",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        },
        atlasArchitecture: {
            pageTitle: "Atlas — System Architecture",
            pageDescription: "Atlas Call Intelligence system architecture — Docker, PostgreSQL, n8n, AI pipeline design.",
            navAtlas: "Atlas Hub",
            subnavHome: "🛰️ Atlas Hub",
            subnavUpload: "🎙️ Upload",
            subnavDashboard: "📊 Dashboard",
            subnavWorkflows: "🤖 Workflows",
            subnavArchitecture: "🏗️ Architecture",
            heroSub: "Docker · PostgreSQL · n8n · Gemini AI",
            heroTitle: "System Architecture",
            heroDesc: "Modern microservices architecture running in Docker — designed for reliability, scalability, and real-time call intelligence.",
            backLink: "← Back to Atlas Hub",
            stackTitle: "Technology Stack",
            svc1Title: "PostgreSQL",
            svc1Desc: "Persistent store for call analyses, monthly reports, panel settings, and alert rules. Port 15432.",
            svc2Title: "n8n Workflow Engine",
            svc2Desc: "Orchestrates transcription, AI analysis, DB writes, and email dispatch. Port 5678.",
            svc3Title: "Analytics Panel",
            svc3Desc: "FastAPI dashboard with Jinja2 templates, Chart.js charts, and Gemini AI insights. Port 8080.",
            svc4Title: "Mailer Service",
            svc4Desc: "Lightweight Python HTTP service for Yahoo SMTP email delivery. Port 8765.",
            flowTitle: "Data Flow",
            flow1: "Voice Upload",
            flow2: "Transcription",
            flow3: "n8n Webhook",
            flow4: "AI Analysis",
            flow5: "PostgreSQL",
            flow6: "Dashboard",
            flowNote: "Parallel path: AI analysis also triggers manager email notification via the mailer service.",
            securityTitle: "Security & Design",
            sec1Title: "Rate Limiting",
            sec1Desc: "Built-in flood protection on all endpoints prevents abuse and ensures platform stability.",
            sec2Title: "Authentication",
            sec2Desc: "Panel supports optional password auth. n8n runs with Basic Auth. API keys stored in Docker env.",
            sec3Title: "Container Isolation",
            sec3Desc: "Each service runs in its own Docker container with health checks and automatic restart.",
            sec4Title: "Bilingual Frontend",
            sec4Desc: "Static HTML pages with client-side i18n (EN/FA) — no server-side Python required on the main site.",
            dbTitle: "Database Schema",
            tbl1Desc: "Main table — call metadata, transcript, full analysis JSON, scores, and ticket priority.",
            tbl2Desc: "Automated monthly executive summaries with aggregated metrics and AI recommendations.",
            tbl3Desc: "SMTP configuration, manager email, and alert cooldown settings.",
            tbl4Desc: "Configurable alert rules for unhappy customers, low satisfaction, and high-intent leads.",
            footer: "© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir"
        }
    },
    fa: {
        title: "محمدرضا جولان زاده",
        description: "رزومه محمدرضا جولان زاده",
        dir: "rtl",
        button: "🇬🇧 English",
        brandTag: "پایتون · فول‌استک · هوش مصنوعی",
        nav: {
            home: "خانه",
            about: "درباره من",
            skills: "مهارت‌ها",
            experience: "سوابق",
            projects: "پروژه‌ها",
            contact: "ارتباط",
            chat: "چت"
        },
        footerCopy: "© ۲۰۲۶ محمدرضا جولان‌زاده — mmdjolan.ir",
        indexChat: "چت خصوصی",
        contactEmail: "ایمیل",
        contactSite: "وب‌سایت",
        contactChat: "چت رمزنگاری‌شده",
        pageTitle: "محمدرضا جولان زاده",
        index: {
            heroMeta: "۲۵ ساله • تهران / اهواز • آماده همکاری حضوری و ریموت",
            projectsButton: "مشاهده پروژه ها",
            aboutTitle: "درباره من",
            aboutLead: "فارغ التحصیل مهندسی کامپیوتر دانشگاه جندی شاپور دزفول",
            aboutText: "توسعه دهنده پایتون • فول استک • هوش مصنوعی",
            experienceTitle: "سوابق کاری",
            exp1: "مدیر پشتیبانی",
            exp1Company: "شرکت آتیران",
            exp2: "کارآموز واحد فناوری اطلاعات",
            exp2Company: "شرکت ملی مناطق نفت خیز جنوب",
            skillsTitle: "مهارت ها",
            programming: "برنامه نویسی",
            frameworks: "فریم ورک ها",
            frontend: "فرانت اند",
            backend: "بک اند",
            certTitle: "مدارک",
            cert1: "مدرک پایتون",
            certCompany: "دانشگاه هاروارد",
            contactTitle: "ارتباط با من",
            contactText: "گیت هاب • لینکدین • ایمیل",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        projects: {
            pageTitle: "پروژه ها | محمدرضا جولان زاده",
            pageDescription: "پروژه های محمدرضا جولان زاده — چت بات هوش مصنوعی، Laravel، WooCommerce، تحلیل تماس.",
            heroTitle: "پروژه های من",
            heroText: "پنج پروژه واقعی از تجربه های برنامه نویسی و توسعه نرم افزار",
            card1Title: "چت بات بانک سامان",
            card1Desc: "دستیار هوشمندی که به سوالات مشتریان بانک سامان پاسخ می دهد و قابلیت آموزش دارد.",
            card2Title: "دستیار پشتیبانی اتیران",
            card2Desc: "چت بات پشتیبانی محلی نصب شده کنار نرم افزار حسابداری اتیران.",
            card3Title: "سامانه رزرو ورزشی دانشگاه",
            card3Desc: "پلتفرم رزرو با ساخت تیم و پیوستن به تیم برای سالن ورزشی دانشگاه.",
            card4Title: "فروشگاه آنلاین عسل",
            card4Desc: "سایت WooCommerce برای کسب و کار عسل با طراحی سفارشی و پرداخت آنلاین.",
            card5Title: "اطلس — تحلیل تماس و اتوماسیون",
            card5Desc: "سامانه جامع هوش تجاری مرکز تماس با بینش هوش مصنوعی، اتوماسیون جریان کار و نظارت عملکرد بلادرنگ.",
            projectLink: "مشاهده پروژه",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        atiran: {
            pageTitle: "دستیار اتیران | پروژه ها",
            pageDescription: "دستیار پشتیبانی محلی اتیران — چت بات Python نصب شده روی سرور مشتری.",
            heroSub: "۲ · Python · اتوماسیون پشتیبانی",
            heroTitle: "دستیار پشتیبانی اتیران",
            heroDesc: "چت بات محلی نصب شده کنار نرم افزار حسابداری اتیران برای حل مسائل بدون تماس با پشتیبانی.",
            backLink: "← بازگشت به پروژه ها",
            section1Title: "مشکل و راه حل",
            problemTitle: "حجم بالای تماس های پشتیبانی",
            problemDesc: "کاربران اتیران برای مسائل ساده و تکراری با پشتیبانی تماس می گرفتند و زمان زیادی تلف می شد.",
            solutionTitle: "دستیار هوشمند محلی",
            solutionDesc: "چت بات روی سرور مشتری نصب می شود و بدون اینترنت یا تماس پشتیبانی پاسخ دقیق می دهد.",
            section2Title: "ویژگی های منحصربه فرد",
            feature1Title: "نصب محلی",
            feature1Desc: "برخلاف بات های ابری، این دستیار روی سرور مشتری اجرا می شود و داده ها خارج نمی شود.",
            feature2Title: "دانش حسابداری اتیران",
            feature2Desc: "مدل با دانش محصول اتیران، خطاهای رایج و راه حل ها آموزش دیده است.",
            feature3Title: "یکپارچگی با رابط اتیران",
            feature3Desc: "کاربر می تواند بدون خروج از نرم افزار سوال بپرسد و دستیار مستقیماً در رابط فعال است.",
            feature4Title: "کاهش فشار پشتیبانی",
            feature4Desc: "پاسخ خودکار به مشکلات رایج فشار تیم پشتیبانی را کاهش می دهد.",
            section3Title: "تکنولوژی ها",
            viewProject: "مشاهده پروژه",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        saman: {
            pageTitle: "چت بات بانک سامان | پروژه ها",
            pageDescription: "چت بات بانک سامان — هوش مصنوعی با NLP و پاسخ سریع مشتری.",
            heroSub: "۱ · Python · هوش مصنوعی",
            heroTitle: "چت بات بانک سامان",
            heroDesc: "دستیار هوشمند برای مشتریان بانک سامان با پاسخ های دقیق و آموزش دیده.",
            backLink: "← بازگشت به پروژه ها",
            section1Title: "ویژگی های کلیدی",
            feature1Title: "آموزش پذیر هوش مصنوعی",
            feature1Desc: "سیستم با داده های جدید یاد می گیرد تا پاسخ های دقیق تر بدهد.",
            feature2Title: "پاسخ های هوشمند",
            feature2Desc: "سوالات متداول مشتریان بانک را درک می کند و پاسخ مناسب می دهد.",
            feature3Title: "بهبود مستمر",
            feature3Desc: "کیفیت با هر تعامل جدید بهتر می شود.",
            feature4Title: "پاسخ فوری",
            feature4Desc: "کاربر بدون انتظار در صف، پاسخ فوری دریافت می کند.",
            section2Title: "نحوه عملکرد",
            step1Title: "دریافت سوال مشتری",
            step1Desc: "کاربر سوال خود را تایپ می کند مانند «چطور کارت را آزاد کنم؟».",
            step2Title: "پردازش هوشمند",
            step2Desc: "مدل زبانی پرسش را پردازش می کند و بهترین پاسخ را از پایگاه دانش می یابد.",
            step3Title: "ارائه پاسخ دقیق",
            step3Desc: "دستیار پاسخ دقیق را با راهنمای گام به گام ارائه می دهد.",
            step4Title: "به روز رسانی مدل",
            step4Desc: "تعاملات جدید مدل را برای پاسخ های بهتر در آینده تقویت می کند.",
            section3Title: "تکنولوژی های استفاده شده",
            techDesc: "دمو و سورس کد به زودی در اینجا قرار می گیرد.",
            viewProject: "مشاهده پروژه زنده",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        sports: {
            pageTitle: "سامانه رزرو ورزشی دانشگاه | پروژه ها",
            pageDescription: "سامانه رزرو سالن ورزشی دانشگاه با تیم سازی و رزرو سانس.",
            heroSub: "۳ · Laravel · پروژه دانشگاهی",
            heroTitle: "سامانه رزرو سالن ورزشی دانشگاه",
            heroDesc: "پلتفرم هوشمند رزرو سانس با امکان تیم سازی و پیوستن به تیم.",
            backLink: "← بازگشت به پروژه ها",
            section1Title: "نقش های کاربری",
            role1Title: "دانشجو",
            role1Desc: "رزرو سانس، ساخت تیم یا جستجوی تیم برای پیوستن.",
            role2Title: "کاپیتان تیم",
            role2Desc: "مدیریت تیم و تأیید یا رد درخواست های عضویت.",
            role3Title: "ادمین سالن",
            role3Desc: "مدیریت برنامه ها، ظرفیت ها و هفتگی سالن.",
            section2Title: "جریان استفاده",
            step1Title: "مشاهده سانس های موجود",
            step1Desc: "دانشجو برنامه هفتگی سالن و ظرفیت های خالی را می بیند.",
            step2Title: "انتخاب و رزرو",
            step2Desc: "سانس مورد نظر را انتخاب و رزرو می کند، سپس تأیید فوری می شود.",
            step3Title: "ساخت یا پیوستن به تیم",
            step3Desc: "می تواند تیم بسازد یا درخواست پیوستن به تیم های موجود دهد.",
            step4Title: "تأیید کاپیتان",
            step4Desc: "کاپیتان درخواست عضویت را تأیید یا رد می کند.",
            step5Title: "مدیریت رزروها",
            step5Desc: "رزروهای فعال نمایش داده می شوند و امکان لغو یا انتقال وجود دارد.",
            section3Title: "ویژگی منحصربه فرد",
            featureTitle: "تیم سازی هوشمند",
            featureDesc: "دانشجویان تنها می توانند تیم های باز را پیدا کرده و درخواست ملحق شدن دهند.",
            section4Title: "تکنولوژی ها",
            viewProject: "مشاهده پروژه",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        honey: {
            pageTitle: "فروشگاه آنلاین عسل | پروژه ها",
            pageDescription: "فروشگاه WooCommerce عسل با طراحی سفارشی.",
            heroSub: "۴ · WordPress · WooCommerce",
            heroTitle: "فروشگاه آنلاین عسل",
            heroDesc: "سایت فروشگاهی کامل برای کسب و کار عسل با طراحی، پرداخت و مدیریت محصول.",
            backLink: "← بازگشت به پروژه ها",
            section1Title: "آنچه تحویل شد",
            item1Title: "طراحی بصری سفارشی",
            item1Desc: "سبک گرم و طبیعی مرتبط با عسل و زنبور.",
            item2Title: "فروشگاه آنلاین",
            item2Desc: "سیستم کامل فروش با سبد خرید، پرداخت و مدیریت سفارش.",
            item3Title: "ریسپانسیو کامل",
            item3Desc: "بهینه برای موبایل، تبلت و دسکتاپ.",
            item4Title: "پنل مدیریت ساده",
            item4Desc: "مالک می تواند محصولات، قیمت ها و موجودی را بدون نیاز فنی مدیریت کند.",
            section2Title: "صفحات سایت",
            page1Title: "صفحه اصلی",
            page1Desc: "معرفی مجموعه، محصولات ویژه و بنرهای تبلیغاتی.",
            page2Title: "فروشگاه",
            page2Desc: "نمایش محصولات با فیلتر نوع و قیمت.",
            page3Title: "درباره ما",
            page3Desc: "معرفی کسب و کار، تاریخچه و ارزش ها.",
            page4Title: "وبلاگ",
            page4Desc: "مقالات درباره عسل و زنبورداری.",
            page5Title: "تماس با ما",
            page5Desc: "فرم تماس، آدرس و پشتیبانی.",
            section3Title: "تکنولوژی ها",
            featureTitle: "راه حل کامل برای خریدار غیرتکنیکال",
            featureDesc: "مالک می تواند محصولات جدید اضافه کند، قیمت ها را تغییر دهد و سفارش ها را پیگیری کند.",
            viewProject: "مشاهده سایت",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir",
            shopTitle: "نمایی از فروشگاه",
            shopLead: "کارت محصول سفارشی، سبد خرید و پرداخت — طراحی شده برای عسل، نه یک قالب آماده.",
            prod1: "عسل کوهستان",
            prod2: "عسل کنار",
            prod3: "عسل آویشن",
            prod4: "ژل رویال",
            prodPrice: "از فروشگاه",
            kpiOrders: "سفارش آنلاین",
            kpiMobile: "موبایل‌فرندلی",
            kpiAdmin: "مدیریت توسط مالک",
            payTitle: "از شیشه تا پرداخت",
            pay1Title: "مرور",
            pay1Desc: "فیلتر نوع، وزن و قیمت.",
            pay2Title: "سبد",
            pay2Desc: "تعداد، یادداشت و بسته‌بندی هدیه.",
            pay3Title: "پرداخت",
            pay3Desc: "درگاه ایرانی و پیامک ثبت سفارش."
        },
        atlas: {
            pageTitle: "اطلس — تحلیل تماس و اتوماسیون | پروژه ها",
            pageDescription: "سامانه مدیریت مرکز تماس هوش مصنوعی با PostgreSQL، اتوماسیون n8n و داشبورد تحلیلی بلادرنگ.",
            heroSub: "۵ · Python · PostgreSQL · n8n · تحلیل بلادرنگ",
            heroTitle: "اطلس — تحلیل تماس و اتوماسیون",
            heroDesc: "سامانه جامع هوش تجاری مرکز تماس با بینش هوش مصنوعی، اتوماسیون جریان کار و نظارت عملکرد بلادرنگ.",
            backLink: "← بازگشت به پروژه ها",
            hubTitle: "مرکز پروژه اطلس",
            hubDesc: "تمام ماژول‌های اطلس را کاوش کنید — آپلود تماس صوتی برای تحلیل هوش مصنوعی، دسترسی به داشبورد، مدیریت جریان کار و بررسی معماری.",
            hubUploadNum: "ماژول ۱ · تحلیل صوتی",
            hubUploadTitle: "آپلود و تحلیل تماس",
            hubUploadDesc: "یک فایل صوتی آپلود کنید و خط لوله کامل اطلس را اجرا کنید — رونویسی، تحلیل هوش مصنوعی، ذخیره در پایگاه داده و اطلاع‌رسانی به مدیر.",
            hubDashNum: "ماژول ۲ · تحلیل‌ها",
            hubDashTitle: "داشبورد تحلیلی",
            hubDashDesc: "KPI بلادرنگ، عملکرد نمایندگان، رضایت مشتری، خط لوله فروش و بینش مدیریتی هوش مصنوعی.",
            hubFlowNum: "ماژول ۳ · اتوماسیون",
            hubFlowTitle: "جریان کار n8n",
            hubFlowDesc: "خط لوله هوش تماس خودکار — webhook، تحلیل هوش مصنوعی، ارسال ایمیل و گزارش ماهانه.",
            hubArchNum: "ماژول ۴ · معماری",
            hubArchTitle: "معماری سامانه",
            hubArchDesc: "پشته فناوری، جریان داده، زیرساخت Docker و طراحی امنیتی پلتفرم اطلس.",
            hubOpen: "باز کردن ←",
            section1Title: "مشکل و راه حل",
            problemTitle: "دردسر تحلیل دستی تماس ها",
            problemDesc: "مراکز تماس با تحلیل دستی داده ها، گزارشات آهسته، ردیابی کیفیت نامنسجم و بدون بینش پیش بینی کننده برای رضایت مشتری دست و پنجه نرم می کنند.",
            solutionTitle: "خط لوله هوش اتوماتیک",
            solutionDesc: "اطلس تماس ها را بلادرنگ ضبط، تحلیل و دسته بندی می کند — با بینش هوش مصنوعی، شروع جریان کار خودکار و تحلیل پیش بینی کننده.",
            section2Title: "ویژگی های اصلی",
            feature1Title: "داشبورد تحلیلی بلادرنگ",
            feature1Desc: "نظارت KPI، عملکرد نماینده، امتیازات رضایت مشتری و تحلیل خودکار روند ۳۰ روزه.",
            feature2Title: "بینش هوش مصنوعی",
            feature2Desc: "Gemini تماس ها را تحلیل کرده تا سرنخ های داغ، مشتریان ناراضی، الگوهای فروش موفق و توصیه های عملی را شناسایی کند.",
            feature3Title: "اتوماسیون جریان کار",
            feature3Desc: "n8n فرآیندهای خودکار را ترتیب می دهد — پیگیری، افزایش سطح و غنی سازی داده.",
            feature5Title: "آپلود و تحلیل صوتی",
            feature5Desc: "ضبط تماس را مستقیماً از وب آپلود کنید — رونویسی خودکار، تحلیل هوش مصنوعی و نتایج فوری.",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        atlasUpload: {
            pageTitle: "اطلس — آپلود و تحلیل | تحلیل صوتی",
            pageDescription: "آپلود فایل صوتی تماس برای تحلیل هوش مصنوعی اطلس — رونویسی، بینش و گزارش خودکار.",
            navAtlas: "مرکز اطلس",
            subnavHome: "🛰️ مرکز اطلس",
            subnavUpload: "🎙️ آپلود",
            subnavDashboard: "📊 داشبورد",
            subnavWorkflows: "🤖 جریان کار",
            subnavArchitecture: "🏗️ معماری",
            heroSub: "آپلود صوتی · رونویسی هوش مصنوعی · هوش تماس",
            heroTitle: "آپلود و تحلیل تماس",
            heroDesc: "یک فایل صوتی آپلود کنید تا خط لوله کامل اطلس اجرا شود — رونویسی، تحلیل هوش مصنوعی، ذخیره در پایگاه داده و ایمیل به مدیر.",
            backLink: "← بازگشت به مرکز اطلس",
            uploadTitle: "آپلود فایل صوتی",
            dropTitle: "فایل ضبط تماس را اینجا بکشید و رها کنید",
            dropHint: "پشتیبانی: MP3, M4A, WAV, OGG, WEBM — حداکثر ۲۵ مگابایت",
            browseBtn: "انتخاب فایل",
            agentLabel: "نام اپراتور",
            agentPlaceholder: "علی رضایی",
            customerLabel: "نام مشتری",
            customerPlaceholder: "شرکت آلفا",
            deptLabel: "بخش",
            deptAuto: "تشخیص خودکار",
            deptSales: "فروش",
            deptSupport: "پشتیبانی",
            submitBtn: "شروع تحلیل",
            stepUpload: "آپلود",
            stepTranscribe: "رونویسی",
            stepAnalyze: "تحلیل",
            stepDone: "تکمیل",
            howTitle: "نحوه عملکرد",
            how1Title: "آپلود ضبط",
            how1Desc: "فایل ضبط تماس را از دستگاه خود انتخاب یا بکشید.",
            how2Title: "رونویسی هوش مصنوعی",
            how2Desc: "Gemini مکالمه فارسی را با برچسب گوینده رونویسی می‌کند.",
            how3Title: "هوش تماس",
            how3Desc: "جریان کار n8n احساسات، تمایل خرید، کیفیت اپراتور را تحلیل و تیکت تولید می‌کند.",
            how4Title: "نتایج و داشبورد",
            how4Desc: "نتایج در PostgreSQL ذخیره و در داشبورد تحلیلی قابل مشاهده است.",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        atlasDashboard: {
            pageTitle: "اطلس — داشبورد تحلیلی",
            pageDescription: "داشبورد تحلیلی اطلس — KPI، عملکرد نمایندگان و بینش هوش مصنوعی.",
            navAtlas: "مرکز اطلس",
            subnavHome: "🛰️ مرکز اطلس",
            subnavUpload: "🎙️ آپلود",
            subnavDashboard: "📊 داشبورد",
            subnavWorkflows: "🤖 جریان کار",
            subnavArchitecture: "🏗️ معماری",
            heroSub: "KPI بلادرنگ · عملکرد نمایندگان · بینش هوش مصنوعی",
            heroTitle: "داشبورد تحلیلی",
            heroDesc: "تحلیل بلادرنگ مرکز تماس با PostgreSQL — نظارت بر عملکرد، شناسایی فرصت‌ها و ردیابی رضایت مشتری.",
            backLink: "← بازگشت به مرکز اطلس",
            accessTitle: "دسترسی به داشبورد",
            accessDesc: "پنل تحلیلی به عنوان سرویس Docker روی پورت 8080 اجرا می‌شود. برای باز کردن داشبورد کامل کلیک کنید.",
            openPanel: "باز کردن پنل تحلیلی",
            openAI: "بینش مدیریتی هوش مصنوعی",
            accessNote: "💡 پنل داده‌های زنده از تماس‌های تحلیل‌شده را نمایش می‌دهد. برای نتایج تازه، از صفحه آپلود ضبط جدید آپلود کنید.",
            featuresTitle: "ویژگی‌های داشبورد",
            feat1Title: "KPI کلی",
            feat1Desc: "کل تماس‌ها، میانگین رضایت، تمایل خرید و کیفیت اپراتور با روند ۳۰ روزه.",
            feat2Title: "برترین‌ها",
            feat2Desc: "رتبه‌بندی نمایندگان بر اساس کیفیت پاسخ، مهارت ارتباطی و رضایت مشتری.",
            feat3Title: "آماده خرید",
            feat3Desc: "سرنخ‌های داغ با تمایل خرید بالا — اولویت‌بندی برای پیگیری.",
            feat4Title: "مشتریان ناراضی",
            feat4Desc: "تماس‌های با امتیاز رضایت پایین که نیاز به توجه فوری دارند.",
            feat5Title: "گزارش‌های ماهانه",
            feat5Desc: "خلاصه مدیریتی ماهانه خودکار با روندها و توصیه‌ها.",
            feat6Title: "جستجو و خروجی",
            feat6Desc: "جستجوی متنی در رونوشت‌ها و خروجی CSV برای تمام گزارش‌ها.",
            liveStatsTitle: "پیش‌نمایش آمار زنده",
            statCalls: "کل تماس‌ها",
            statSat: "میانگین رضایت",
            statIntent: "میانگین تمایل خرید",
            statQuality: "میانگین کیفیت اپراتور",
            statsLoading: "در حال بارگذاری آمار از پنل…",
            recentCallsTitle: "آخرین تماس‌ها",
            colCallId: "شناسه تماس",
            colCustomer: "مشتری",
            colAgent: "اپراتور",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        atlasWorkflows: {
            pageTitle: "اطلس — جریان کار n8n",
            pageDescription: "اتوماسیون جریان کار n8n اطلس — خط لوله هوش تماس، webhook و گزارش ماهانه.",
            navAtlas: "مرکز اطلس",
            subnavHome: "🛰️ مرکز اطلس",
            subnavUpload: "🎙️ آپلود",
            subnavDashboard: "📊 داشبورد",
            subnavWorkflows: "🤖 جریان کار",
            subnavArchitecture: "🏗️ معماری",
            heroSub: "n8n · Webhook · خط لوله خودکار",
            heroTitle: "اتوماسیون جریان کار",
            heroDesc: "n8n خط لوله هوش تماس اطلس را ترتیب می‌دهد — از webhook تا تحلیل هوش مصنوعی، ذخیره در پایگاه داده و ایمیل.",
            backLink: "← بازگشت به مرکز اطلس",
            accessTitle: "دسترسی به n8n",
            accessDesc: "موتور جریان کار روی پورت 5678 با Basic Auth فعال اجرا می‌شود.",
            openN8n: "باز کردن ویرایشگر n8n",
            accessNote: "🔒 Basic Auth فعال است. اطلاعات ورود در docker-compose.yml تنظیم شده.",
            pipelineTitle: "خط لوله هوش تماس",
            pipe1Title: "Webhook",
            pipe1Desc: "POST /webhook/atlas/call-intelligence رونوشت یا URL صوتی با متادیتای تماس دریافت می‌کند.",
            pipe2Title: "تحلیل هوش مصنوعی",
            pipe2Desc: "LLM رونوشت را برای احساسات، تمایل خرید، کیفیت اپراتور تحلیل و تیکت CRM تولید می‌کند.",
            pipe3Title: "ذخیره در PostgreSQL",
            pipe3Desc: "JSON تحلیل ساختاریافته در جدول call_analyses برای کوئری‌های داشبورد ذخیره می‌شود.",
            pipe4Title: "ایمیل مدیر",
            pipe4Desc: "ایمیل تیکت خودکار از طریق سرویس mailer به آدرس مدیر تنظیم‌شده ارسال می‌شود.",
            webhooksTitle: "Webhook ها",
            wh1Title: "هوش تماس",
            wh1Desc: "خط لوله اصلی — رونوشت + متادیتا دریافت، JSON تحلیل کامل برمی‌گرداند.",
            wh2Title: "گزارش ماهانه",
            wh2Desc: "خلاصه مدیریتی ماهانه تولید می‌کند. همچنین با cron در اول هر ماه فعال می‌شود.",
            workflowsTitle: "جریان کارهای فعال",
            wf1Desc: "تحلیل کامل تماس فارسی با تشخیص فروش/پشتیبانی، تولید تیکت، ذخیره DB و ایمیل.",
            wf2Desc: "داده‌های ماهانه تماس را به خلاصه مدیریتی با روندها و توصیه‌ها تجمیع می‌کند.",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        },
        atlasArchitecture: {
            pageTitle: "اطلس — معماری سامانه",
            pageDescription: "معماری سامانه Atlas Call Intelligence — Docker، PostgreSQL، n8n، طراحی خط لوله AI.",
            navAtlas: "مرکز اطلس",
            subnavHome: "🛰️ مرکز اطلس",
            subnavUpload: "🎙️ آپلود",
            subnavDashboard: "📊 داشبورد",
            subnavWorkflows: "🤖 جریان کار",
            subnavArchitecture: "🏗️ معماری",
            heroSub: "Docker · PostgreSQL · n8n · Gemini AI",
            heroTitle: "معماری سامانه",
            heroDesc: "معماری میکروسرویس مدرن در Docker — طراحی شده برای قابلیت اطمینان، مقیاس‌پذیری و هوش تماس بلادرنگ.",
            backLink: "← بازگشت به مرکز اطلس",
            stackTitle: "پشته فناوری",
            svc1Title: "PostgreSQL",
            svc1Desc: "ذخیره‌سازی پایدار برای تحلیل تماس‌ها، گزارش‌های ماهانه، تنظیمات پنل و قوانین هشدار. پورت 15432.",
            svc2Title: "موتور جریان کار n8n",
            svc2Desc: "رونویسی، تحلیل AI، نوشتن DB و ارسال ایمیل را ترتیب می‌دهد. پورت 5678.",
            svc3Title: "پنل تحلیلی",
            svc3Desc: "داشبورد FastAPI با قالب Jinja2، نمودار Chart.js و بینش Gemini AI. پورت 8080.",
            svc4Title: "سرویس Mailer",
            svc4Desc: "سرویس HTTP سبک Python برای ارسال ایمیل Yahoo SMTP. پورت 8765.",
            flowTitle: "جریان داده",
            flow1: "آپلود صوتی",
            flow2: "رونویسی",
            flow3: "Webhook n8n",
            flow4: "تحلیل AI",
            flow5: "PostgreSQL",
            flow6: "داشبورد",
            flowNote: "مسیر موازی: تحلیل AI همچنین ایمیل اطلاع‌رسانی مدیر را از طریق سرویس mailer فعال می‌کند.",
            securityTitle: "امنیت و طراحی",
            sec1Title: "محدودیت نرخ",
            sec1Desc: "حفاظت سیل در تمام endpointها از سوءاستفاده جلوگیری و ثبات سامانه را تضمین می‌کند.",
            sec2Title: "احراز هویت",
            sec2Desc: "پنل از رمز عبور اختیاری پشتیبانی می‌کند. n8n با Basic Auth اجرا می‌شود. کلیدهای API در env Docker.",
            sec3Title: "ایزolation کانتینر",
            sec3Desc: "هر سرویس در کانتینر Docker جداگانه با health check و restart خودکار اجرا می‌شود.",
            sec4Title: "فرانت‌اند دوزبانه",
            sec4Desc: "صفحات HTML استاتیک با i18n سمت کلاینت (EN/FA) — بدون نیاز به Python سمت سرور در سایت اصلی.",
            dbTitle: "طرح پایگاه داده",
            tbl1Desc: "جدول اصلی — متادیتای تماس، رونوشت، JSON تحلیل کامل، امتیازات و اولویت تیکت.",
            tbl2Desc: "خلاصه‌های مدیریتی ماهانه خودکار با معیارهای تجمیعی و توصیه‌های AI.",
            tbl3Desc: "تنظیمات SMTP، ایمیل مدیر و cooldown هشدار.",
            tbl4Desc: "قوانین هشدار قابل تنظیم برای مشتریان ناراضی، رضایت پایین و سرنخ‌های با تمایل بالا.",
            footer: "© 2026 محمدرضا جولان زاده — mmdjolan.ir"
        }
    }
};


const typingTexts = {
  en: ["Python Developer", "Full Stack Developer", "AI Developer"],
  fa: ["توسعه‌دهنده پایتون", "توسعه‌دهنده فول‌استک", "توسعه‌دهنده هوش مصنوعی"]
};

let currentLanguage = localStorage.getItem("lang") || "en";
let typingIndex = 0;
let charIndex = 0;
let typingDirection = 1;
const pageKey = (document.body && document.body.dataset.page) || "index";

function startTyping() {
  const el = document.getElementById("typing");
  if (!el) return;
  setInterval(function () {
    const arr = typingTexts[currentLanguage] || typingTexts.en;
    el.textContent = arr[typingIndex].substring(0, charIndex);
    charIndex += typingDirection;
    if (charIndex > arr[typingIndex].length) typingDirection = -1;
    if (charIndex < 0) {
      typingDirection = 1;
      typingIndex = (typingIndex + 1) % arr.length;
      charIndex = 0;
    }
  }, 110);
}

function getNestedValue(obj, key) {
  return key.split(".").reduce(function (value, segment) {
    if (value && typeof value === "object" && segment in value) return value[segment];
    return undefined;
  }, obj);
}

function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem("lang", lang);
  const baseData = languageData[lang] || languageData.en;
  const pageData = (baseData[pageKey] && typeof baseData[pageKey] === "object") ? baseData[pageKey] : {};
  document.documentElement.lang = lang;
  document.documentElement.dir = baseData.dir || (lang === "fa" ? "rtl" : "ltr");
  document.body && document.body.classList.toggle("rtl", lang === "fa");
  document.title = getNestedValue(pageData, "pageTitle") || baseData.pageTitle || baseData.title;
  const metaDescription = document.getElementById("meta-description");
  const description = getNestedValue(pageData, "pageDescription") || baseData.description;
  if (metaDescription && description) metaDescription.setAttribute("content", description);
  const langButton = document.getElementById("lang-toggle");
  if (langButton) langButton.textContent = baseData.button;
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    const key = el.dataset.i18n;
    const translation = getNestedValue(pageData, key) || getNestedValue(baseData, key);
    if (translation !== undefined) el.innerHTML = translation;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
    const key = el.dataset.i18nPlaceholder;
    const translation = getNestedValue(pageData, key) || getNestedValue(baseData, key);
    if (translation !== undefined) el.setAttribute("placeholder", translation);
  });
}

function sitePrefix() {
  return /\/atlas_project\//.test(location.pathname.replace(/\\/g, "/")) ? "../" : "";
}

function mountSiteChrome() {
  if (!document.body || document.body.classList.contains("chat-room") || document.body.classList.contains("no-chrome")) return;
  var p = sitePrefix();
  var page = document.body.dataset.page || "";
  var active = ({
    index: "home",
    projects: "projects",
    saman: "projects",
    atiran: "projects",
    sports: "projects",
    honey: "projects",
    atlas: "projects",
    atlasUpload: "projects",
    atlasDashboard: "projects",
    atlasWorkflows: "projects",
    atlasArchitecture: "projects"
  })[page] || "home";
  var header = '<header class="site-header">' +
    '<a class="brand" href="' + p + 'index.html"><span class="brand-mark">م</span><span class="brand-text"><strong>MMDJOLAN</strong><small data-i18n="brandTag">Python · Full Stack · AI</small></span></a>' +
    '<nav class="nav-links" id="nav-links">' +
    '<a class="drawer-brand" href="' + p + 'index.html"><span class="brand-mark">م</span><span class="brand-text"><strong>MMDJOLAN</strong><small data-i18n="brandTag">Python · Full Stack · AI</small></span></a>' +
    '<a href="' + p + 'index.html" data-nav="home" data-i18n="nav.home">Home</a>' +
    '<a href="' + p + 'index.html#about" data-i18n="nav.about">About</a>' +
    '<a href="' + p + 'index.html#skills" data-i18n="nav.skills">Skills</a>' +
    '<a href="' + p + 'index.html#experience" data-i18n="nav.experience">Experience</a>' +
    '<a href="' + p + 'projects.html" data-nav="projects" data-i18n="nav.projects">Projects</a>' +
    '<a href="' + p + 'index.html#contact" data-i18n="nav.contact">Contact</a>' +
    '<a href="' + p + 'chat-login.php" data-nav="chat" data-i18n="nav.chat">Chat</a>' +
    '</nav>' +
    '<div class="header-actions">' +
    '<button type="button" class="icon-btn" id="theme-toggle" aria-label="Theme">◐</button>' +
    '<button type="button" class="lang-btn" id="lang-toggle">🇮🇷 ترجمه</button>' +
    '<button type="button" class="icon-btn nav-toggle" id="nav-toggle" aria-label="Menu">☰</button>' +
    '</div></header><div class="nav-overlay" id="nav-overlay"></div>';
  var oldHeader = document.querySelector(".site-header");
  var oldOverlay = document.getElementById("nav-overlay");
  if (oldHeader) oldHeader.outerHTML = header.split('<div class="nav-overlay"')[0];
  else document.body.insertAdjacentHTML("afterbegin", header.split('<div class="nav-overlay"')[0]);
  if (oldOverlay) oldOverlay.outerHTML = '<div class="nav-overlay" id="nav-overlay"></div>';
  else {
    var hdr = document.querySelector(".site-header");
    if (hdr) hdr.insertAdjacentHTML("afterend", '<div class="nav-overlay" id="nav-overlay"></div>');
  }
  document.querySelectorAll(".nav-links a[data-nav]").forEach(function (a) {
    if (a.getAttribute("data-nav") === active) a.classList.add("active");
  });
  var footer = '<footer class="site-footer"><p class="footer-copy" data-i18n="footerCopy">© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir</p></footer>';
  var oldFooter = document.querySelector(".site-footer");
  if (oldFooter) oldFooter.outerHTML = footer;
  else document.body.insertAdjacentHTML("beforeend", footer);
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  var btn = document.getElementById("theme-toggle");
  if (btn) btn.setAttribute("aria-label", theme === "dark" ? "Light mode" : "Dark mode");
}

function parkNav() {
  var nav = document.getElementById("nav-links");
  var overlay = document.getElementById("nav-overlay");
  var header = document.querySelector(".site-header");
  var actions = header && header.querySelector(".header-actions");
  if (!nav) return;
  if (window.matchMedia("(max-width: 1080px)").matches) {
    document.body.appendChild(nav);
    if (overlay) document.body.appendChild(overlay);
  } else if (header && actions && nav.parentElement !== header) {
    header.insertBefore(nav, actions);
  }
}

function wireChrome() {
  var nav = document.getElementById("nav-links");
  var overlay = document.getElementById("nav-overlay");
  var toggle = document.getElementById("nav-toggle");
  parkNav();
  nav = document.getElementById("nav-links");
  overlay = document.getElementById("nav-overlay");
  function setOpen(open) {
    nav = document.getElementById("nav-links");
    overlay = document.getElementById("nav-overlay");
    if (open) parkNav();
    if (nav) nav.classList.toggle("open", open);
    if (overlay) overlay.classList.toggle("open", open);
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("nav-open", open);
  }
  function closeNav() { setOpen(false); }
  if (toggle && nav) {
    toggle.setAttribute("aria-expanded", "false");
    toggle.addEventListener("click", function () {
      setOpen(!nav.classList.contains("open"));
    });
  }
  if (overlay) overlay.addEventListener("click", closeNav);
  document.querySelectorAll(".nav-links a").forEach(function (a) { a.addEventListener("click", closeNav); });
  window.addEventListener("resize", function () {
    if (window.innerWidth > 1080) closeNav();
    parkNav();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeNav();
  });
  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  }
  var langToggle = document.getElementById("lang-toggle");
  if (langToggle) {
    langToggle.addEventListener("click", function () {
      setLanguage(currentLanguage === "en" ? "fa" : "en");
    });
  }
}

document.addEventListener("DOMContentLoaded", function () {
  applyTheme(document.documentElement.getAttribute("data-theme") || "light");
  mountSiteChrome();
  setLanguage(currentLanguage);
  startTyping();
  wireChrome();
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) entry.target.classList.add("visible");
      });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach(function (item) {
      observer.observe(item);
      if (item.getBoundingClientRect().top < window.innerHeight) item.classList.add("visible");
    });
  } else {
    document.querySelectorAll(".reveal").forEach(function (item) { item.classList.add("visible"); });
  }
});
