<?php
// config.php - نسخه دیباگ
define('DB_HOST', 'localhost');
define('DB_NAME', 'mmdjolan_chat_system');
define('DB_USER', 'mmdjolan_owner');
define('DB_PASS', 'Jolan1380'); // ★★★ پسورد واقعی رو اینجا بذار ★★★

define('ENCRYPTION_KEY', 'my-secret-key-32-bytes-for-aes-256-encryption');
define('ENCRYPTION_IV', '1234567890123456');

function getDBConnection() {
    try {
        $pdo = new PDO("mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4", DB_USER, DB_PASS);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        return $pdo;
    } catch(PDOException $e) {
        error_log("DB connection failed: " . $e->getMessage());
        die("Service temporarily unavailable.");
    }
}
?>