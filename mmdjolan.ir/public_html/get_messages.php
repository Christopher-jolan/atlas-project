<?php
// get_messages.php
session_start();
require_once 'config.php';
require_once 'encryption.php';

header('Content-Type: application/json');

require_once __DIR__ . '/includes/rate_limit.php';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['messages' => [], 'typing' => false]);
    exit;
}

// Polling rate-limit: allow up to 120 polls per minute per IP (roughly 1 per 0.5s)
if (!rate_limit_check('poll', 120, 60)) {
    // Return empty but indicate throttle
    echo json_encode(['messages' => [], 'typing' => false, 'throttled' => true]);
    exit;
}

$userId = $_SESSION['user_id'];
$otherUserId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;

if ($otherUserId <= 0) {
    echo json_encode(['messages' => [], 'typing' => false]);
    exit;
}

$pdo = getDBConnection();

// Get new messages
$stmt = $pdo->prepare("
    SELECT * FROM messages 
    WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
    ORDER BY created_at ASC
");
$stmt->execute([$otherUserId, $userId]);
$messages = $stmt->fetchAll();

// Mark as read
$stmt = $pdo->prepare("UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ? AND is_read = 0");
$stmt->execute([$otherUserId, $userId]);

// Decrypt messages
$result = [];
foreach ($messages as $msg) {
    $result[] = [
        'id' => $msg['id'],
        'sender_id' => $msg['sender_id'],
        'message' => decryptMessage($msg['message']),
        'media_type' => $msg['media_type'],
        'media_path' => $msg['media_path'],
        'time' => date('H:i', strtotime($msg['created_at']))
    ];
}

// Check typing status (simple file-based)
$typingFile = sys_get_temp_dir() . '/typing_' . $userId . '_' . $otherUserId . '.txt';
$typing = false;
if (file_exists($typingFile)) {
    $timestamp = file_get_contents($typingFile);
    if (time() - $timestamp < 3) {
        $typing = true;
    } else {
        unlink($typingFile);
    }
}

echo json_encode(['messages' => $result, 'typing' => $typing]);
?>