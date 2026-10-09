<?php
// encryption.php
function encryptMessage($message) {
    $key = ENCRYPTION_KEY;
    $iv = ENCRYPTION_IV;
    
    // Pad message to block size
    $blockSize = 16;
    $padSize = $blockSize - (strlen($message) % $blockSize);
    $message .= str_repeat(chr($padSize), $padSize);
    
    $encrypted = openssl_encrypt(
        $message,
        'AES-256-CBC',
        $key,
        OPENSSL_RAW_DATA,
        $iv
    );
    
    return base64_encode($encrypted);
}

function decryptMessage($encrypted) {
    $key = ENCRYPTION_KEY;
    $iv = ENCRYPTION_IV;
    
    $decrypted = openssl_decrypt(
        base64_decode($encrypted),
        'AES-256-CBC',
        $key,
        OPENSSL_RAW_DATA,
        $iv
    );
    
    // Remove padding
    $padSize = ord($decrypted[strlen($decrypted) - 1]);
    return substr($decrypted, 0, -$padSize);
}
?>