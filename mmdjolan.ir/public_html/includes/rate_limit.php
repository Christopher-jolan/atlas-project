<?php
// includes/rate_limit.php
// Simple file-based rate limiter utilities used across PHP endpoints.

function rl_get_temp_file($action, $ip) {
    $safeIp = preg_replace('/[^a-z0-9_.-]/i', '_', $ip);
    $dir = sys_get_temp_dir();
    return $dir . DIRECTORY_SEPARATOR . "rate_{$action}_{$safeIp}.json";
}

function rate_limit_check($action, $limit, $window_seconds) {
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $file = rl_get_temp_file($action, $ip);
    $now = time();

    $data = [];
    if (file_exists($file)) {
        $content = @file_get_contents($file);
        $data = $content ? json_decode($content, true) : [];
        if (!is_array($data)) $data = [];
    }

    // Remove old entries
    $data = array_filter($data, function($ts) use ($now, $window_seconds) { return ($now - $ts) < $window_seconds; });

    if (count($data) >= $limit) {
        // update file to keep cleaned timestamps
        @file_put_contents($file, json_encode(array_values($data)), LOCK_EX);
        rate_limit_log_block($action, $ip, count($data));
        return false;
    }

    // record this attempt
    $data[] = $now;
    @file_put_contents($file, json_encode(array_values($data)), LOCK_EX);
    return true;
}

function rate_limit_log_block($action, $ip, $count=0) {
    $logDir = __DIR__ . DIRECTORY_SEPARATOR . '..' . DIRECTORY_SEPARATOR . 'logs';
    if (!is_dir($logDir)) @mkdir($logDir, 0755, true);
    $logFile = $logDir . DIRECTORY_SEPARATOR . 'rate_limit.log';
    $time = date('Y-m-d H:i:s');
    $entry = "[$time] BLOCK action={$action} ip={$ip} attempts={$count}\n";
    @file_put_contents($logFile, $entry, FILE_APPEND | LOCK_EX);
}

?>