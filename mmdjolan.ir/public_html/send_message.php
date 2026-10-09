<?php
// send_message.php
session_start();
require_once 'config.php';
require_once 'encryption.php';

header('Content-Type: application/json');

require_once __DIR__ . '/includes/rate_limit.php';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'error' => 'Not logged in']);
    exit;
}

// Rate limit sending messages: max 30 sends per minute per IP
if (!rate_limit_check('send_message', 30, 60)) {
    echo json_encode(['success' => false, 'error' => 'Too many requests. Slow down.']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['success' => false, 'error' => 'Invalid method']);
    exit;
}

$senderId = $_SESSION['user_id'];
$receiverId = isset($_POST['receiver_id']) ? intval($_POST['receiver_id']) : 0;
$message = isset($_POST['message']) ? trim($_POST['message']) : '';
$replyTo = isset($_POST['reply_to']) ? intval($_POST['reply_to']) : null;

if ($receiverId <= 0 || empty($message)) {
    echo json_encode(['success' => false, 'error' => 'Invalid data']);
    exit;
}

$pdo = getDBConnection();

// Check if receiver exists
$stmt = $pdo->prepare("SELECT id FROM users WHERE id = ?");
$stmt->execute([$receiverId]);
if (!$stmt->fetch()) {
    echo json_encode(['success' => false, 'error' => 'User not found']);
    exit;
}

// Encrypt message
$encrypted = encryptMessage($message);

// Save message
if ($replyTo) {
    $stmt = $pdo->prepare("INSERT INTO messages (sender_id, receiver_id, message, reply_to) VALUES (?, ?, ?, ?)");
    $success = $stmt->execute([$senderId, $receiverId, $encrypted, $replyTo]);
} else {
    $stmt = $pdo->prepare("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)");
    $success = $stmt->execute([$senderId, $receiverId, $encrypted]);
}

if ($success) {
    $messageId = $pdo->lastInsertId();
    echo json_encode(['success' => true, 'message_id' => $messageId]);
} else {
    echo json_encode(['success' => false, 'error' => 'Database error']);
}
?>