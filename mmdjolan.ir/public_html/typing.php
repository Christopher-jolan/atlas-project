<?php
// typing.php
session_start();
require_once 'config.php';

if (!isset($_SESSION['user_id'])) {
    exit;
}

$userId = $_SESSION['user_id'];
$receiverId = isset($_POST['receiver_id']) ? intval($_POST['receiver_id']) : 0;
$isTyping = isset($_POST['typing']) ? intval($_POST['typing']) : 0;

// Rate-limit typing toggles to avoid rapid flood
require_once __DIR__ . '/includes/rate_limit.php';
if (!rate_limit_check('typing_toggle', 60, 60)) {
    // silently ignore excessive typing toggles
    echo json_encode(['success' => false, 'error' => 'Too many requests']);
    exit;
}

// Store typing status in temp file
$typingFile = sys_get_temp_dir() . '/typing_' . $receiverId . '_' . $userId . '.txt';
if ($isTyping) {
    file_put_contents($typingFile, time());
} else {
    if (file_exists($typingFile)) {
        unlink($typingFile);
    }
}

echo json_encode(['success' => true]);
?>