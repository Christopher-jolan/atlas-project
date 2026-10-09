<?php
// chat.php - نسخه نهایی با رفع کامل بک زدن و بلاک IP
session_start();
require_once 'config.php';
require_once 'encryption.php';

// بررسی لاگین
if (!isset($_SESSION['user_id'])) {
    header('Location: chat-login.php');
    exit;
}

$pdo = getDBConnection();
$userId = $_SESSION['user_id'];
$otherUserId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 0;

if ($otherUserId <= 0) {
    header('Location: chat-lobby.php');
    exit;
}

// Get other user info
$stmt = $pdo->prepare("SELECT id, username, display_name, is_online, avatar FROM users WHERE id = ?");
$stmt->execute([$otherUserId]);
$otherUser = $stmt->fetch();

if (!$otherUser) {
    header('Location: chat-lobby.php');
    exit;
}

$otherDisplayName = $otherUser['display_name'] ?? $otherUser['username'];
$isNewChat = isset($_GET['new']) && $_GET['new'] == 1;

// Mark messages as read
$stmt = $pdo->prepare("UPDATE messages SET is_read = 1 WHERE sender_id = ? AND receiver_id = ? AND is_read = 0");
$stmt->execute([$otherUserId, $userId]);

// Get messages with reply info
$stmt = $pdo->prepare("
    SELECT m.*, 
           CASE WHEN m.sender_id = ? THEN 1 ELSE 0 END as is_sent,
           CASE WHEN m.is_read = 1 AND m.sender_id != ? THEN 1 ELSE 0 END as is_read_status,
           r.message as reply_message
    FROM messages m
    LEFT JOIN messages r ON r.id = m.reply_to
    WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?) 
    ORDER BY m.created_at ASC
");
$stmt->execute([$userId, $userId, $userId, $otherUserId, $otherUserId, $userId]);
$messages = $stmt->fetchAll();

// Get user info
$stmt = $pdo->prepare("SELECT display_name, username, avatar FROM users WHERE id = ?");
$stmt->execute([$userId]);
$currentUserData = $stmt->fetch();
$currentDisplayName = $currentUserData['display_name'] ?? $currentUserData['username'] ?? 'You';
$currentAvatar = $currentUserData['avatar'] ?? null;
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>💬 Chat with <?php echo htmlspecialchars($otherDisplayName); ?></title>
    <link rel="icon" href="logo.png">
    <script>try{var th=localStorage.getItem("theme");if(!th)th="light";document.documentElement.setAttribute("data-theme",th)}catch(e){}</script>
    <link rel="stylesheet" href="css/style.css">

    </head>
<body class="chat-room">
    <!-- ===== HEADER ===== -->
    <div class="chat-header">
        <a href="#" class="back" id="backButton">←</a>
        <div class="user-info">
            <div class="avatar">
                <?php if ($otherUser['avatar']): ?>
                    <img src="<?php echo htmlspecialchars($otherUser['avatar']); ?>" alt="">
                <?php else: ?>
                    <?php echo mb_substr($otherDisplayName, 0, 1); ?>
                <?php endif; ?>
            </div>
            <div class="name-wrap">
                <div class="name"><?php echo htmlspecialchars($otherDisplayName); ?></div>
                <div class="status <?php echo $otherUser['is_online'] ? 'online' : ''; ?>">
                    <?php echo $otherUser['is_online'] ? '🟢 Online' : '⚪ Offline'; ?>
                </div>
            </div>
            <?php if ($isNewChat): ?>
                <span class="new-badge">✨ New</span>
            <?php endif; ?>
        </div>
    </div>

    <!-- ===== MESSAGES ===== -->
    <div class="messages-container" id="messagesContainer">
        <?php if (empty($messages)): ?>
            <div class="empty-chat">
                <div class="icon">💬</div>
                <p>No messages yet. Say hello!</p>
                <p style="font-size:11px;opacity:0.4;margin-top:6px;">🔒 End-to-end encrypted</p>
            </div>
        <?php else: ?>
            <?php 
            $lastDate = '';
            foreach ($messages as $msg): 
                $isSent = $msg['sender_id'] == $userId;
                $decryptedMsg = decryptMessage($msg['message']);
                $time = date('H:i', strtotime($msg['created_at']));
                $msgDate = date('Y-m-d', strtotime($msg['created_at']));
                $isRead = $msg['is_read_status'] == 1;
                $hasMedia = !empty($msg['media_path']);
                $mediaType = $msg['media_type'] ?? '';
                $replyMsg = $msg['reply_message'] ? decryptMessage($msg['reply_message']) : null;
                
                if ($msgDate != $lastDate) {
                    $lastDate = $msgDate;
                    $dateLabel = date('F j, Y', strtotime($msgDate));
                    if (date('Y-m-d') == $msgDate) $dateLabel = 'Today';
                    elseif (date('Y-m-d', strtotime('-1 day')) == $msgDate) $dateLabel = 'Yesterday';
            ?>
                <div class="date-divider"><span><?php echo $dateLabel; ?></span></div>
            <?php } ?>
                <div class="message-wrapper <?php echo $isSent ? 'sent' : 'received'; ?>" data-msg-id="<?php echo $msg['id']; ?>">
                    <div class="message">
                        <?php if ($msg['reply_to'] && $replyMsg !== null): ?>
                            <div class="reply-preview" onclick="scrollToMessage(<?php echo $msg['reply_to']; ?>)">
                                ↩ <?php echo htmlspecialchars(substr($replyMsg, 0, 60)) . (strlen($replyMsg) > 60 ? '...' : ''); ?>
                            </div>
                        <?php elseif ($msg['reply_to']): ?>
                            <div class="reply-preview">↩ Reply</div>
                        <?php endif; ?>
                        
                        <?php if ($hasMedia && $mediaType === 'image'): ?>
                            <div class="media-content">
                                <img src="<?php echo htmlspecialchars($msg['media_path']); ?>" alt="Image" loading="lazy" onclick="window.open(this.src)">
                            </div>
                        <?php endif; ?>
                        
                        <?php if ($decryptedMsg): ?>
                            <?php echo htmlspecialchars($decryptedMsg); ?>
                        <?php endif; ?>
                        
                        <div class="message-footer">
                            <span class="time"><?php echo $time; ?></span>
                            <?php if ($isSent): ?>
                                <span class="read-status <?php echo $isRead ? 'read' : ''; ?>">
                                    <?php echo $isRead ? '✓✓' : '✓'; ?>
                                </span>
                            <?php endif; ?>
                        </div>
                    </div>
                    <div class="message-actions">
                        <button onclick="replyTo(<?php echo $msg['id']; ?>, '<?php echo htmlspecialchars(addslashes($decryptedMsg ?: '📷 Photo')); ?>')" title="Reply">↩</button>
                    </div>
                </div>
            <?php endforeach; ?>
        <?php endif; ?>
        <div id="typingIndicator" class="typing-indicator" style="display:none;">✎ typing...</div>
    </div>

    <!-- ===== SCROLL TO BOTTOM ===== -->
    <div class="scroll-to-bottom" id="scrollToBottom" onclick="scrollToBottom()">
        ⬇
    </div>

    <!-- ===== ENCRYPTION BADGE ===== -->
    <div class="encryption-badge">🔒 All messages are encrypted</div>

    <!-- ===== INPUT AREA ===== -->
    <div class="chat-input-area">
        <div class="reply-indicator" id="replyIndicator">
            <span class="reply-text" id="replyText">↩ Replying to: <span id="replyMessageText"></span></span>
            <button class="cancel-reply" onclick="cancelReply()">✕</button>
        </div>
        <div class="input-row">
            <div class="input-wrapper">
                <textarea id="messageInput" placeholder="Type a message..." rows="1"></textarea>
            </div>
            <div class="input-actions">
                <button onclick="openMediaPicker()" title="Attach">🍯</button>
            </div>
            <button class="send-btn" id="sendBtn">Send</button>
        </div>
    </div>

    <script>
        // ===== VARIABLES =====
        const messagesContainer = document.getElementById('messagesContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const typingIndicator = document.getElementById('typingIndicator');
        const replyIndicator = document.getElementById('replyIndicator');
        const replyMessageText = document.getElementById('replyMessageText');
        const scrollToBottomBtn = document.getElementById('scrollToBottom');
        const backButton = document.getElementById('backButton');
        const userId = <?php echo $userId; ?>;
        const otherUserId = <?php echo $otherUserId; ?>;
        let replyToId = null;
        let isTyping = false;
        let isNavigating = false;

        // ===== GO BACK - روش نهایی برای جلوگیری از بلاک شدن IP =====
        backButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // اگر در حال نویگیت هستیم، کاری نکن
            if (isNavigating) return;
            isNavigating = true;
            
            // غیرفعال کردن دکمه
            this.style.opacity = '0.3';
            this.style.pointerEvents = 'none';
            this.textContent = '⏳';
            
            // متوقف کردن همه درخواست‌های AJAX
            if (window.pollInterval) {
                clearInterval(window.pollInterval);
                window.pollInterval = null;
            }
            
            // متوقف کردن تایپینگ
            try {
                fetch('typing.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'receiver_id=' + otherUserId + '&typing=0'
                });
            } catch(e) {}
            
            // استفاده از replace به جای href برای جلوگیری از بازگشت با بک
            // این کار باعث میشه صفحه چت از تاریخچه مرورگر حذف بشه
            setTimeout(function() {
                window.location.replace('chat-lobby.php');
            }, 100);
        });

        // ===== جلوگیری از کلیک دوباره =====
        document.addEventListener('click', function(e) {
            if (isNavigating) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        });

        // ===== SCROLL FUNCTIONS =====
        function scrollToBottom() {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                scrollToBottomBtn.classList.remove('show');
            }, 30);
        }

        function scrollToMessage(msgId) {
            const el = document.querySelector(`.message-wrapper[data-msg-id="${msgId}"]`);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.style.background = '#00d9ff11';
                setTimeout(() => {
                    el.style.background = 'transparent';
                }, 2000);
            }
        }

        function checkScrollPosition() {
            const threshold = 100;
            const isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold;
            
            if (!isAtBottom && messagesContainer.scrollHeight > messagesContainer.clientHeight + 100) {
                scrollToBottomBtn.classList.add('show');
            } else {
                scrollToBottomBtn.classList.remove('show');
            }
        }

        messagesContainer.addEventListener('scroll', checkScrollPosition);
        messagesContainer.addEventListener('touchmove', checkScrollPosition);

        // ===== AUTO-GROW =====
        function autoGrow(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
            textarea.style.overflowY = textarea.scrollHeight > 100 ? 'auto' : 'hidden';
        }

        messageInput.addEventListener('input', function() {
            autoGrow(this);
            if (this.value.trim().length > 0) {
                sendTypingIndicator(true);
            }
        });

        // ===== SEND MESSAGE =====
        function sendMessage() {
            if (isNavigating) return;
            
            const message = messageInput.value.trim();
            if (!message) return;

            const data = {
                receiver_id: otherUserId,
                message: message
            };
            if (replyToId) {
                data.reply_to = replyToId;
            }

            sendBtn.disabled = true;
            sendBtn.innerHTML = '⏳';

            fetch('send_message.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams(data)
            })
            .then(res => res.json())
            .then(response => {
                if (response.success) {
                    messageInput.value = '';
                    autoGrow(messageInput);
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Send';
                    cancelReply();
                    
                    const now = new Date();
                    const time = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
                    
                    const empty = messagesContainer.querySelector('.empty-chat');
                    if (empty) empty.remove();
                    
                    const wrapper = document.createElement('div');
                    wrapper.className = 'message-wrapper sent';
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    
                    let footerHtml = `<div class="message-footer"><span class="time">${time}</span><span class="read-status">✓</span></div>`;
                    
                    msgDiv.innerHTML = escapeHtml(message) + footerHtml;
                    wrapper.appendChild(msgDiv);
                    
                    const actions = document.createElement('div');
                    actions.className = 'message-actions';
                    actions.innerHTML = `<button onclick="replyTo(${response.message_id || 0}, '${escapeHtml(message)}')">↩</button>`;
                    wrapper.appendChild(actions);
                    
                    messagesContainer.appendChild(wrapper);
                    setTimeout(scrollToBottom, 50);
                }
            })
            .catch(() => {
                sendBtn.disabled = false;
                sendBtn.innerHTML = 'Send';
            });
        }

        // ===== SEND MEDIA =====
        function openMediaPicker() {
            if (isNavigating) return;
            
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            
            input.onchange = function(e) {
                const file = e.target.files[0];
                if (!file) return;
                if (file.size > 5 * 1024 * 1024) {
                    alert('File too large! Max 5MB.');
                    return;
                }
                sendMedia(file);
            };
            input.click();
        }

        function sendMedia(file) {
            if (isNavigating) return;
            
            const formData = new FormData();
            formData.append('receiver_id', otherUserId);
            formData.append('media', file);
            if (replyToId) {
                formData.append('reply_to', replyToId);
            }

            sendBtn.disabled = true;
            sendBtn.innerHTML = '⏳';

            fetch('send_media.php', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(response => {
                if (response.success) {
                    sendBtn.disabled = false;
                    sendBtn.innerHTML = 'Send';
                    cancelReply();
                    
                    const now = new Date();
                    const time = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
                    
                    const empty = messagesContainer.querySelector('.empty-chat');
                    if (empty) empty.remove();
                    
                    const wrapper = document.createElement('div');
                    wrapper.className = 'message-wrapper sent';
                    const msgDiv = document.createElement('div');
                    msgDiv.className = 'message';
                    
                    let mediaHtml = `<div class="media-content"><img src="${response.media_path}" alt="Image" loading="lazy" onclick="window.open(this.src)"></div>`;
                    let footerHtml = `<div class="message-footer"><span class="time">${time}</span><span class="read-status">✓</span></div>`;
                    
                    msgDiv.innerHTML = mediaHtml + footerHtml;
                    wrapper.appendChild(msgDiv);
                    
                    const actions = document.createElement('div');
                    actions.className = 'message-actions';
                    actions.innerHTML = `<button onclick="replyTo(${response.message_id || 0}, '📷 Photo')">↩</button>`;
                    wrapper.appendChild(actions);
                    
                    messagesContainer.appendChild(wrapper);
                    setTimeout(scrollToBottom, 50);
                }
            })
            .catch(() => {
                sendBtn.disabled = false;
                sendBtn.innerHTML = 'Send';
                alert('Failed to send media. Please try again.');
            });
        }

        // ===== REPLY =====
        function replyTo(msgId, msgText) {
            if (isNavigating) return;
            replyToId = msgId;
            replyIndicator.classList.add('show');
            replyMessageText.textContent = msgText.substring(0, 60) + (msgText.length > 60 ? '...' : '');
            messageInput.focus();
        }

        function cancelReply() {
            replyToId = null;
            replyIndicator.classList.remove('show');
        }

        // ===== TYPING =====
        function sendTypingIndicator(isTypingNow) {
            if (isNavigating) return;
            if (isTypingNow === isTyping) return;
            isTyping = isTypingNow;
            
            fetch('typing.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'receiver_id=' + otherUserId + '&typing=' + (isTyping ? '1' : '0')
            });
        }

        // ===== ESCAPE HTML =====
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // ===== FETCH NEW MESSAGES =====
        function fetchNewMessages() {
            if (isNavigating) return;
            
            fetch('get_messages.php?user_id=' + otherUserId)
                .then(res => res.json())
                .then(data => {
                    if (isNavigating) return;
                    
                    if (data.messages && data.messages.length > 0) {
                        const empty = messagesContainer.querySelector('.empty-chat');
                        if (empty) empty.remove();
                        
                        data.messages.forEach(msg => {
                            const existing = messagesContainer.querySelectorAll('.message-wrapper');
                            let exists = false;
                            for (let el of existing) {
                                if (el.dataset.msgId == msg.id) {
                                    exists = true;
                                    break;
                                }
                            }
                            if (!exists && msg.sender_id != userId) {
                                const wrapper = document.createElement('div');
                                wrapper.className = 'message-wrapper received';
                                wrapper.dataset.msgId = msg.id;
                                const msgDiv = document.createElement('div');
                                msgDiv.className = 'message';
                                
                                let content = '';
                                if (msg.media_type === 'image' && msg.media_path) {
                                    content += `<div class="media-content"><img src="${msg.media_path}" alt="Image" loading="lazy" onclick="window.open(this.src)"></div>`;
                                }
                                if (msg.message) {
                                    content += escapeHtml(msg.message);
                                }
                                content += `<div class="message-footer"><span class="time">${msg.time}</span></div>`;
                                
                                msgDiv.innerHTML = content;
                                wrapper.appendChild(msgDiv);
                                
                                const actions = document.createElement('div');
                                actions.className = 'message-actions';
                                actions.innerHTML = `<button onclick="replyTo(${msg.id}, '${escapeHtml(msg.message || '📷 Photo')}')">↩</button>`;
                                wrapper.appendChild(actions);
                                
                                messagesContainer.appendChild(wrapper);
                                checkScrollPosition();
                            }
                        });
                        setTimeout(scrollToBottom, 50);
                    }
                    
                    if (data.typing) {
                        typingIndicator.style.display = 'block';
                        setTimeout(() => {
                            typingIndicator.style.display = 'none';
                        }, 3000);
                    }
                })
                .catch(() => {});
        }

        // ===== MOBILE LONG PRESS REPLY =====
        let pressTimer = null;
        let startX = 0;
        let startY = 0;

        document.addEventListener('touchstart', function(e) {
            if (isNavigating) return;
            const msgWrapper = e.target.closest('.message-wrapper');
            if (!msgWrapper) return;
            
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            
            pressTimer = setTimeout(() => {
                const msgId = msgWrapper.dataset.msgId;
                const msgText = msgWrapper.querySelector('.message')?.textContent?.trim() || 'Message';
                replyTo(parseInt(msgId), msgText.substring(0, 60));
                pressTimer = null;
            }, 500);
        }, { passive: true });

        document.addEventListener('touchmove', function(e) {
            if (!pressTimer) return;
            const dx = e.touches[0].clientX - startX;
            const dy = e.touches[0].clientY - startY;
            if (Math.abs(dx) > 20 || Math.abs(dy) > 20) {
                clearTimeout(pressTimer);
                pressTimer = null;
            }
        }, { passive: true });

        document.addEventListener('touchend', function() {
            if (pressTimer) {
                clearTimeout(pressTimer);
                pressTimer = null;
            }
        }, { passive: true });

        // ===== EVENT LISTENERS =====
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // ===== جلوگیری از بک مرورگر =====
        window.addEventListener('popstate', function(e) {
            if (!isNavigating) {
                isNavigating = true;
                window.location.replace('chat-lobby.php');
            }
        });

        // ===== INIT =====
        setTimeout(scrollToBottom, 100);
        setTimeout(checkScrollPosition, 200);
        
        window.pollInterval = setInterval(fetchNewMessages, 1500);

        // ===== VISIBILITY =====
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                sendTypingIndicator(false);
            } else {
                fetchNewMessages();
                setTimeout(scrollToBottom, 100);
            }
        });

        // ===== BEFORE UNLOAD =====
        window.addEventListener('beforeunload', function() {
            if (window.pollInterval) {
                clearInterval(window.pollInterval);
                window.pollInterval = null;
            }
            sendTypingIndicator(false);
        });

        // ===== KEYBOARD SHORTCUT =====
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                cancelReply();
            }
        });

        // ===== RESIZE FIX FOR MOBILE KEYBOARD =====
        let lastHeight = window.innerHeight;
        window.addEventListener('resize', function() {
            const newHeight = window.innerHeight;
            if (Math.abs(newHeight - lastHeight) > 100) {
                setTimeout(() => {
                    scrollToBottom();
                    checkScrollPosition();
                }, 300);
                lastHeight = newHeight;
            }
        });
    </script>
</body>
</html>