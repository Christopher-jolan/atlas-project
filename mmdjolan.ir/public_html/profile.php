<?php
// profile.php - نسخه با ویرایش کامل
session_start();
require_once 'config.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: chat-login.php');
    exit;
}

$pdo = getDBConnection();
$userId = $_SESSION['user_id'];
$isOwnProfile = true;

// Get user info
$stmt = $pdo->prepare("SELECT id, username, display_name, avatar, is_online FROM users WHERE id = ?");
$stmt->execute([$userId]);
$user = $stmt->fetch();

if (!$user) {
    header('Location: chat-lobby.php');
    exit;
}

$displayName = $user['display_name'] ?? $user['username'];
$username = $user['username'];
$avatar = $user['avatar'] ?? null;
$message = '';
$error = '';

// Update profile
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $newDisplayName = trim($_POST['display_name'] ?? '');
    $newUsername = trim($_POST['username'] ?? '');
    
    // Validate username
    if (empty($newUsername)) {
        $error = 'Username cannot be empty';
    } elseif (!preg_match('/^[a-zA-Z0-9_]{3,30}$/', $newUsername)) {
        $error = 'Username must be 3-30 characters (letters, numbers, underscore)';
    } elseif ($newUsername !== $username) {
        // Check if username is taken
        $stmt = $pdo->prepare("SELECT id FROM users WHERE username = ? AND id != ?");
        $stmt->execute([$newUsername, $userId]);
        if ($stmt->fetch()) {
            $error = 'Username already taken';
        }
    }
    
    if (empty($newDisplayName)) {
        $error = 'Display name cannot be empty';
    }
    
    if (empty($error)) {
        // Update username and display name
        $stmt = $pdo->prepare("UPDATE users SET username = ?, display_name = ? WHERE id = ?");
        if ($stmt->execute([$newUsername, $newDisplayName, $userId])) {
            $_SESSION['username'] = $newUsername;
            $_SESSION['display_name'] = $newDisplayName;
            $username = $newUsername;
            $displayName = $newDisplayName;
            $message = 'Profile updated successfully!';
        } else {
            $error = 'Update failed';
        }
    }
    
    // Avatar upload
    if (isset($_FILES['avatar']) && $_FILES['avatar']['error'] === UPLOAD_ERR_OK) {
        $file = $_FILES['avatar'];
        $maxSize = 2 * 1024 * 1024;
        if ($file['size'] <= $maxSize) {
            $allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
            if (in_array($file['type'], $allowedTypes)) {
                $uploadDir = 'uploads/avatars/';
                if (!is_dir($uploadDir)) mkdir($uploadDir, 0755, true);
                
                if ($avatar && file_exists(ltrim($avatar, '/'))) {
                    @unlink(ltrim($avatar, '/'));
                }
                
                $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
                $filename = 'avatar_' . $userId . '.' . $ext;
                $filePath = $uploadDir . $filename;
                $dbPath = '/' . $filePath;
                
                if (move_uploaded_file($file['tmp_name'], $filePath)) {
                    $stmt = $pdo->prepare("UPDATE users SET avatar = ? WHERE id = ?");
                    $stmt->execute([$dbPath, $userId]);
                    $avatar = $dbPath;
                    $message = 'Avatar updated successfully!';
                } else {
                    $error = 'Failed to upload image';
                }
            } else {
                $error = 'Invalid image format (use JPEG, PNG, GIF, WEBP)';
            }
        } else {
            $error = 'Image too large (max 2MB)';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>My Profile</title>
    <link rel="icon" href="logo.png">
    <script>try{var th=localStorage.getItem("theme");if(!th)th="light";document.documentElement.setAttribute("data-theme",th)}catch(e){}</script>
    <link rel="stylesheet" href="css/style.css">

    </head>
<body class="no-chrome">
    <div class="profile-container">
        <div class="avatar-wrap">
            <div class="avatar" id="avatarDisplay">
                <?php if ($avatar): ?>
                    <img src="<?php echo htmlspecialchars($avatar); ?>" alt="Avatar" id="avatarImg">
                <?php else: ?>
                    <?php echo mb_substr($displayName, 0, 1); ?>
                <?php endif; ?>
            </div>
            <button class="avatar-upload" onclick="document.getElementById('avatarInput').click()" title="Change avatar">📷</button>
        </div>
        
        <div class="name"><?php echo htmlspecialchars($displayName); ?></div>
        <div class="username-display">@<?php echo htmlspecialchars($username); ?></div>
        <div class="status"><?php echo $user['is_online'] ? '🟢 Online' : '⚪ Offline'; ?></div>

        <?php if ($message): ?>
            <div class="message">✅ <?php echo htmlspecialchars($message); ?></div>
        <?php endif; ?>
        <?php if ($error): ?>
            <div class="error">⚠️ <?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>

        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="avatar" id="avatarInput" accept="image/*" style="display:none;" onchange="previewAvatar(this)">
            
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" value="<?php echo htmlspecialchars($username); ?>" required 
                       pattern="[a-zA-Z0-9_]{3,30}" title="3-30 characters (letters, numbers, underscore)">
                <div class="hint">3-30 characters (letters, numbers, underscore)</div>
            </div>
            
            <div class="form-group">
                <label>Display Name</label>
                <input type="text" name="display_name" value="<?php echo htmlspecialchars($displayName); ?>" required>
            </div>
            
            <button type="submit" class="btn">💾 Update Profile</button>
        </form>

        <div class="profile-actions">
            <a href="chat-lobby.php" class="btn btn-secondary" style="text-decoration:none;text-align:center;">← Back</a>
        </div>
    </div>

    <script>
        function previewAvatar(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const avatarDisplay = document.getElementById('avatarDisplay');
                    avatarDisplay.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
    </script>
</body>
</html>