<?php
// chat-login.php - نسخه کاملاً امن
ob_start();
session_start();

require_once 'config.php';
require_once 'encryption.php';

// Handle logout
if (isset($_GET['logout'])) {
    if (isset($_SESSION['user_id'])) {
        try {
            $pdo = getDBConnection();
            $stmt = $pdo->prepare("UPDATE users SET is_online = 0 WHERE id = ?");
            $stmt->execute([$_SESSION['user_id']]);
        } catch(Exception $e) {
            // Ignore
        }
    }
    session_destroy();
    header('Location: chat-login.php');
    exit;
}

// If already logged in
if (isset($_SESSION['user_id']) && isset($_SESSION['username'])) {
    header('Location: chat-lobby.php');
    exit;
}

$error = '';
$isRegister = false;

// Rate limiter utilities
require_once __DIR__ . '/includes/rate_limit.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        // Determine action early and enforce rate limits before heavy work
        $isRegister = isset($_POST['register']);
        $action = $isRegister ? 'register' : 'login';
        // Limits: register = 5 attempts per 5 minutes, login = 10 attempts per minute
        $ok = rate_limit_check($action, $isRegister ? 5 : 10, $isRegister ? 300 : 60);
        if (!$ok) {
            $error = 'Too many attempts from your IP. Please wait a while and try again.';
            goto show_form;
        }

        // ✅ تلاش برای اتصال به دیتابیس
        try {
            $pdo = getDBConnection();
        } catch(Exception $e) {
            // ❌ خطای دیتابیس رو قایم کن
            $error = 'System error. Please try again later.';
            error_log("DB Connection failed: " . $e->getMessage());
            // ادامه نده
            goto show_form;
        }
        
        $username = trim($_POST['username'] ?? '');
        $password = $_POST['password'] ?? '';
        
        if ($isRegister) {
            // Register
            if (empty($username) || empty($password)) {
                $error = 'Please fill all fields';
            } elseif (strlen($username) < 3) {
                $error = 'Username must be at least 3 characters';
            } elseif (strlen($password) < 4) {
                $error = 'Password must be at least 4 characters';
            } else {
                $stmt = $pdo->prepare("SELECT id FROM users WHERE username = ?");
                $stmt->execute([$username]);
                if ($stmt->fetch()) {
                    $error = 'Username already exists';
                } else {
                    $hashedPassword = password_hash($password, PASSWORD_DEFAULT);
                    $displayName = trim($_POST['display_name'] ?? $username);
                    $stmt = $pdo->prepare("INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)");
                    $stmt->execute([$username, $hashedPassword, $displayName]);
                    
                    $userId = $pdo->lastInsertId();
                    $_SESSION['user_id'] = $userId;
                    $_SESSION['username'] = $username;
                    $_SESSION['display_name'] = $displayName;
                    
                    $stmt = $pdo->prepare("UPDATE users SET is_online = 1 WHERE id = ?");
                    $stmt->execute([$userId]);
                    
                    header('Location: chat-lobby.php');
                    exit;
                }
            }
        } else {
            // Login
            if (empty($username) || empty($password)) {
                $error = 'Invalid username or password';
            } else {
                $stmt = $pdo->prepare("SELECT id, username, display_name, password FROM users WHERE username = ?");
                $stmt->execute([$username]);
                $user = $stmt->fetch();
                
                if ($user && password_verify($password, $user['password'])) {
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['username'] = $user['username'];
                    $_SESSION['display_name'] = $user['display_name'] ?? $user['username'];
                    
                    $stmt = $pdo->prepare("UPDATE users SET is_online = 1 WHERE id = ?");
                    $stmt->execute([$user['id']]);
                    
                    header('Location: chat-lobby.php');
                    exit;
                } else {
                    $error = 'Invalid username or password';
                    error_log("Failed login: " . $username . " from " . $_SERVER['REMOTE_ADDR']);
                }
            }
        }
    } catch (PDOException $e) {
        // ❌ خطاهای PDO رو قایم کن
        $error = 'System error. Please try again later.';
        error_log("Database error: " . $e->getMessage());
    } catch (Exception $e) {
        // ❌ همه خطاها رو قایم کن
        $error = 'System error. Please try again later.';
        error_log("System error: " . $e->getMessage());
    }
}

show_form:
ob_end_flush();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Chat</title>
    <link rel="icon" href="logo.png">
    <script>try{var th=localStorage.getItem("theme");if(!th)th="light";document.documentElement.setAttribute("data-theme",th)}catch(e){}</script>
    <link rel="stylesheet" href="css/style.css">
</head>
<body data-page="index">
    <header class="site-header">
      <a class="brand" href="index.html"><span class="brand-mark">م</span><span class="brand-text"><strong>MMDJOLAN</strong><small data-i18n="brandTag">Python · Full Stack · AI</small></span></a>
      <nav class="nav-links" id="nav-links">
        <a href="index.html" data-nav="home" data-i18n="nav.home">Home</a>
        <a href="index.html#about" data-i18n="nav.about">About</a>
        <a href="projects.html" data-nav="projects" data-i18n="nav.projects">Projects</a>
        <a href="chat-login.php" data-nav="chat" data-i18n="nav.chat">Chat</a>
      </nav>
      <div class="header-actions">
        <button type="button" class="icon-btn" id="theme-toggle" aria-label="Theme">◐</button>
        <button type="button" class="lang-btn" id="lang-toggle">🇮🇷 ترجمه</button>
        <button type="button" class="icon-btn nav-toggle" id="nav-toggle" aria-label="Menu">☰</button>
      </div>
    </header>
    <div class="nav-overlay" id="nav-overlay"></div>
    <div class="auth-wrap">
    <div class="auth-card">
        <div class="lock-icon">🔒</div>
        <h1 id="form-title"><?php echo $isRegister ? 'Register' : 'Login'; ?></h1>
        <p class="sub" id="form-sub"><?php echo $isRegister ? 'Create your private account' : 'Access your private chat'; ?></p>
        <?php if ($error): ?>
            <div class="alert error"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <form method="POST" id="auth-form" action="chat-login.php">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" id="username" required autofocus>
            </div>
            <div class="form-group" id="display-name-group" style="<?php echo $isRegister ? 'display:block;' : 'display:none;'; ?>">
                <label>Display Name</label>
                <input type="text" name="display_name" id="display_name" placeholder="Optional">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" id="password" required>
            </div>
            <button type="submit" name="<?php echo $isRegister ? 'register' : 'login'; ?>" class="btn" id="submit-btn">
                <?php echo $isRegister ? 'Register' : 'Login'; ?>
            </button>
        </form>
        <div class="toggle-text">
            <span id="toggle-text"><?php echo $isRegister ? "Already have an account?" : "Don't have an account?"; ?></span>
            <a href="#" id="toggle-link"><?php echo $isRegister ? 'Login' : 'Register'; ?></a>
        </div>
        <a href="index.html" class="back-btn" style="margin-top:1rem">← Back to Main</a>
        <div class="secure-badge">SECURE CONNECTION</div>
    </div>
    </div>
    <script>
        let isLogin = <?php echo $isRegister ? 'false' : 'true'; ?>;
        const formTitle = document.getElementById('form-title');
        const formSub = document.getElementById('form-sub');
        const submitBtn = document.getElementById('submit-btn');
        const toggleText = document.getElementById('toggle-text');
        const toggleLink = document.getElementById('toggle-link');
        const displayNameGroup = document.getElementById('display-name-group');
        function toggleForm() {
            isLogin = !isLogin;
            if (isLogin) {
                formTitle.textContent = 'Login';
                formSub.textContent = 'Access your private chat';
                submitBtn.textContent = 'Login';
                submitBtn.name = 'login';
                toggleText.textContent = "Don't have an account?";
                toggleLink.textContent = 'Register';
                displayNameGroup.style.display = 'none';
            } else {
                formTitle.textContent = 'Register';
                formSub.textContent = 'Create your private account';
                submitBtn.textContent = 'Register';
                submitBtn.name = 'register';
                toggleText.textContent = "Already have an account?";
                toggleLink.textContent = 'Login';
                displayNameGroup.style.display = 'block';
            }
        }
        toggleLink.addEventListener('click', function(e) { e.preventDefault(); toggleForm(); });
        document.getElementById('username').focus();
    </script>
    <footer class="site-footer"><p class="footer-copy" data-i18n="footerCopy">© 2026 Mohamad Reza Jolan Zadeh — mmdjolan.ir</p></footer>
    <script src="js/app.js"></script>
</body>
</html>
