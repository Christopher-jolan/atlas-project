<?php
// send_media.php
session_start();
require_once 'config.php';
require_once 'encryption.php';

header('Content-Type: application/json');

require_once __DIR__ . '/includes/rate_limit.php';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'error' => 'Not logged in']);
    exit;
}

// Rate limit media uploads: max 6 uploads per 10 minutes per IP
if (!rate_limit_check('send_media', 6, 600)) {
    echo json_encode(['success' => false, 'error' => 'Too many uploads. Please wait.']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['success' => false, 'error' => 'Invalid method']);
    exit;
}

$senderId = $_SESSION['user_id'];
$receiverId = isset($_POST['receiver_id']) ? intval($_POST['receiver_id']) : 0;
$replyTo = isset($_POST['reply_to']) ? intval($_POST['reply_to']) : null;

if ($receiverId <= 0) {
    echo json_encode(['success' => false, 'error' => 'Invalid receiver']);
    exit;
}

// Check if file uploaded
if (!isset($_FILES['media']) || $_FILES['media']['error'] !== UPLOAD_ERR_OK) {
    echo json_encode(['success' => false, 'error' => 'File upload failed']);
    exit;
}

$file = $_FILES['media'];
$maxSize = 5 * 1024 * 1024; // 5MB
if ($file['size'] > $maxSize) {
    echo json_encode(['success' => false, 'error' => 'File too large']);
    exit;
}

// Validate file type
$allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
if (!in_array($file['type'], $allowedTypes)) {
    echo json_encode(['success' => false, 'error' => 'Invalid file type']);
    exit;
}

// Create uploads directory if not exists
$uploadDir = 'uploads/chat/';
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0755, true);
}

// Generate unique filename
$ext = pathinfo($file['name'], PATHINFO_EXTENSION);
$filename = uniqid() . '.' . $ext;
$filePath = $uploadDir . $filename;
$dbPath = '/' . $filePath;

// Move file
if (!move_uploaded_file($file['tmp_name'], $filePath)) {
    echo json_encode(['success' => false, 'error' => 'Failed to save file']);
    exit;
}

$pdo = getDBConnection();

// Encrypt message (empty for media)
$encrypted = encryptMessage('');

// Save message
if ($replyTo) {
    $stmt = $pdo->prepare("INSERT INTO messages (sender_id, receiver_id, message, reply_to, media_type, media_path) VALUES (?, ?, ?, ?, ?, ?)");
    $success = $stmt->execute([$senderId, $receiverId, $encrypted, $replyTo, 'image', $dbPath]);
} else {
    $stmt = $pdo->prepare("INSERT INTO messages (sender_id, receiver_id, message, media_type, media_path) VALUES (?, ?, ?, ?, ?)");
    $success = $stmt->execute([$senderId, $receiverId, $encrypted, 'image', $dbPath]);
}

if ($success) {
    $messageId = $pdo->lastInsertId();
    echo json_encode(['success' => true, 'message_id' => $messageId, 'media_path' => $dbPath]);
} else {
    echo json_encode(['success' => false, 'error' => 'Database error']);
}
?>