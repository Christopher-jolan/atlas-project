<?php
// chat-lobby.php - نسخه کامل با پروفایل
session_start();
require_once 'config.php';
require_once 'encryption.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: chat-login.php');
    exit;
}

$pdo = getDBConnection();
$userId = $_SESSION['user_id'];
$currentUser = $_SESSION['display_name'] ?? $_SESSION['username'] ?? 'User';
$searchQuery = isset($_GET['search']) ? trim($_GET['search']) : '';

// Get user avatar
$stmt = $pdo->prepare("SELECT avatar, display_name, username FROM users WHERE id = ?");
$stmt->execute([$userId]);
$userData = $stmt->fetch();
$userAvatar = $userData['avatar'] ?? null;
$currentUser = $userData['display_name'] ?? $userData['username'] ?? 'User';

// Update online status
$stmt = $pdo->prepare("UPDATE users SET is_online = 1, last_seen = NOW() WHERE id = ?");
$stmt->execute([$userId]);

// Get chat users
$stmt = $pdo->prepare("
    SELECT DISTINCT 
        u.id, 
        u.username, 
        u.display_name, 
        u.is_online,
        u.avatar,
        MAX(m.created_at) as last_message_time
    FROM users u
    INNER JOIN messages m ON (m.sender_id = u.id AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = u.id)
    WHERE u.id != ?
    GROUP BY u.id, u.username, u.display_name, u.is_online, u.avatar
    ORDER BY last_message_time DESC
");
$stmt->execute([$userId, $userId, $userId]);
$chatUsers = $stmt->fetchAll();

// Search results
$searchResults = [];
if (!empty($searchQuery) && strlen($searchQuery) >= 2) {
    $stmt = $pdo->prepare("
        SELECT id, username, display_name, is_online, avatar 
        FROM users 
        WHERE id != ? 
        AND (username LIKE ? OR display_name LIKE ?)
        AND id NOT IN (
            SELECT DISTINCT 
                CASE 
                    WHEN sender_id = ? THEN receiver_id 
                    WHEN receiver_id = ? THEN sender_id 
                END
            FROM messages 
            WHERE sender_id = ? OR receiver_id = ?
        )
        LIMIT 10
    ");
    $searchParam = '%' . $searchQuery . '%';
    $stmt->execute([$userId, $searchParam, $searchParam, $userId, $userId, $userId, $userId]);
    $searchResults = $stmt->fetchAll();
}

// Get unread counts
$unreadCounts = [];
foreach ($chatUsers as $user) {
    $stmt = $pdo->prepare("SELECT COUNT(*) as count FROM messages WHERE sender_id = ? AND receiver_id = ? AND is_read = 0");
    $stmt->execute([$user['id'], $userId]);
    $unreadCounts[$user['id']] = $stmt->fetch()['count'];
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>💬 Chat Lobby</title>
    <link rel="icon" href="logo.png">
    <script>try{var th=localStorage.getItem("theme");if(!th)th="light";document.documentElement.setAttribute("data-theme",th)}catch(e){}</script>
    <link rel="stylesheet" href="css/style.css">

    </head>
<body class="no-chrome">
    <div class="lobby-container">
        <!-- HEADER -->
        <div class="header">
            <div class="header-left">
                <div class="profile-avatar" onclick="window.location.href='profile.php'">
                    <?php if ($userAvatar): ?>
                        <img src="<?php echo htmlspecialchars($userAvatar); ?>" alt="">
                    <?php else: ?>
                        <?php echo mb_substr($currentUser, 0, 1); ?>
                    <?php endif; ?>
                </div>
                <div class="user-info">
                    <div class="name"><?php echo htmlspecialchars($currentUser); ?></div>
                    <div class="username">@<?php echo htmlspecialchars($userData['username'] ?? ''); ?></div>
                </div>
            </div>
            <div class="header-actions">
                <button class="profile-btn" onclick="window.location.href='profile.php'">👤 Edit</button>
                <button class="refresh-btn" onclick="location.reload()">🔄</button>
                <a href="chat-login.php?logout=1" class="logout-btn" onclick="event.preventDefault(); if(confirm('Logout?')) { window.location.href='chat-login.php?logout=1'; }">🚪</a>
            </div>
        </div>

        <!-- SEARCH -->
        <div class="search-section">
            <div class="title">🔍 Find Users</div>
            <form method="GET" class="search-box" id="searchForm">
                <input type="text" name="search" placeholder="Search by username or display name..." 
                       value="<?php echo htmlspecialchars($searchQuery); ?>" 
                       minlength="2" autocomplete="off">
                <button type="submit">🔍 Search</button>
                <?php if (!empty($searchQuery)): ?>
                    <button type="button" class="clear" onclick="window.location.href='chat-lobby.php'">✕ Clear</button>
                <?php endif; ?>
            </form>
        </div>

        <!-- SEARCH RESULTS BADGE -->
        <?php if (!empty($searchQuery) && !empty($searchResults)): ?>
            <div style="margin-bottom: 10px;">
                <span class="search-result-badge">🔍 Found <?php echo count($searchResults); ?> result(s)</span>
            </div>
        <?php endif; ?>

        <!-- USERS LIST -->
        <div class="users-list">
            <div class="title">
                <span>💬 Your Chats</span>
                <span class="count"><?php echo count($chatUsers); ?> conversation(s)</span>
            </div>

            <?php if (empty($chatUsers) && empty($searchResults) && empty($searchQuery)): ?>
                <div class="empty-state">
                    <div class="icon">🔒</div>
                    <p>No chats yet</p>
                    <p class="sub">Search for users above to start a conversation</p>
                </div>
            <?php endif; ?>

            <!-- Search Results -->
            <?php if (!empty($searchResults)): ?>
                <?php foreach ($searchResults as $user): ?>
                    <?php
                    $displayName = $user['display_name'] ?? $user['username'];
                    $initial = mb_substr($displayName, 0, 1);
                    $isOnline = $user['is_online'] == 1;
                    $avatar = $user['avatar'] ?? null;
                    ?>
                    <a href="chat.php?user_id=<?php echo $user['id']; ?>&new=1" class="user-item" style="border-left: 3px solid #00d9ff;">
                        <div class="info">
                            <div class="avatar">
                                <?php if ($avatar): ?>
                                    <img src="<?php echo htmlspecialchars($avatar); ?>" alt="">
                                <?php else: ?>
                                    <?php echo htmlspecialchars($initial); ?>
                                <?php endif; ?>
                            </div>
                            <div class="name-wrap">
                                <div class="name"><?php echo htmlspecialchars($displayName); ?></div>
                                <div class="username">@<?php echo htmlspecialchars($user['username']); ?></div>
                                <div class="status <?php echo $isOnline ? 'online' : ''; ?>">
                                    <?php echo $isOnline ? '🟢 Online' : '⚪ Offline'; ?>
                                </div>
                            </div>
                        </div>
                        <div>
                            <span class="start-chat">✨ Start</span>
                        </div>
                    </a>
                <?php endforeach; ?>
            <?php endif; ?>

            <!-- Chat Users -->
            <?php foreach ($chatUsers as $user): ?>
                <?php
                $displayName = $user['display_name'] ?? $user['username'];
                $initial = mb_substr($displayName, 0, 1);
                $isOnline = $user['is_online'] == 1;
                $unread = $unreadCounts[$user['id']] ?? 0;
                $avatar = $user['avatar'] ?? null;
                $lastTime = isset($user['last_message_time']) ? date('H:i', strtotime($user['last_message_time'])) : '';
                ?>
                <a href="chat.php?user_id=<?php echo $user['id']; ?>" class="user-item">
                    <div class="info">
                        <div class="avatar">
                            <?php if ($avatar): ?>
                                <img src="<?php echo htmlspecialchars($avatar); ?>" alt="">
                            <?php else: ?>
                                <?php echo htmlspecialchars($initial); ?>
                            <?php endif; ?>
                        </div>
                        <div class="name-wrap">
                            <div class="name"><?php echo htmlspecialchars($displayName); ?></div>
                            <div class="username">@<?php echo htmlspecialchars($user['username']); ?></div>
                            <div class="status <?php echo $isOnline ? 'online' : ''; ?>">
                                <?php echo $isOnline ? '🟢 Online' : '⚪ Offline'; ?>
                                <?php if ($lastTime): ?>
                                    <span style="color:#9be7ff44;font-size:10px;">· <?php echo $lastTime; ?></span>
                                <?php endif; ?>
                            </div>
                        </div>
                    </div>
                    <div>
                        <?php if ($unread > 0): ?>
                            <span class="badge"><?php echo $unread; ?></span>
                        <?php else: ?>
                            <span class="badge empty">💬</span>
                        <?php endif; ?>
                    </div>
                </a>
            <?php endforeach; ?>

            <!-- No search results -->
            <?php if (!empty($searchQuery) && empty($searchResults)): ?>
                <div class="empty-state">
                    <div class="icon">😕</div>
                    <p>No users found for "<strong><?php echo htmlspecialchars($searchQuery); ?></strong>"</p>
                    <p class="sub">Try a different search term</p>
                </div>
            <?php endif; ?>
        </div>

        <a href="index.html" class="back-link" onclick="event.preventDefault(); window.location.replace('index.html');">← Back to Main</a>
    </div>

    <script>
        // Auto-submit search with Enter
        document.getElementById('searchForm').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submit();
            }
        });

        // Ctrl+/ for search
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                document.querySelector('input[name="search"]').focus();
            }
        });
    </script>
</body>
</html>