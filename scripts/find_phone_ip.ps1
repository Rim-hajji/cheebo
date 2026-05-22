# Script PowerShell pour trouver l'adresse IP du telephone Android connecte
# Usage: powershell -ExecutionPolicy Bypass -File find_phone_ip.ps1

Write-Host "[*] Recherche du telephone Android connecte..." -ForegroundColor Cyan
Write-Host ""

# Verifier si adb est disponible
$adbPath = "adb"
try {
    $adbVersion = & $adbPath version 2>$null
    if (-not $?) {
        throw "ADB non trouve"
    }
} catch {
    Write-Host "[!] ADB (Android Debug Bridge) n'est pas installe ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "    Veuillez installer Android SDK Tools: https://developer.android.com/tools/releases/platform-tools" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] ADB trouve" -ForegroundColor Green
Write-Host ""

# Lister les appareils connectes
Write-Host "[*] Appareils connectes:" -ForegroundColor Cyan
$devices = & $adbPath devices
Write-Host $devices

# Extraire l'ID du premier appareil connecte
$deviceId = $devices | Select-String "device$" | Select-Object -First 1 | ForEach-Object { $_.Line.Split()[0] }

if (-not $deviceId) {
    Write-Host "[!] Aucun telephone connecte en mode debogage" -ForegroundColor Red
    Write-Host ""
    Write-Host "[INFO] Comment connecter votre telephone:" -ForegroundColor Yellow
    Write-Host "   1. Activez le Mode Developpeur: Parametres > A propos > Appuyez 7x sur 'Numero de version'"
    Write-Host "   2. Activez le Debogage USB: Parametres > Options pour les developpeurs > Debogage USB"
    Write-Host "   3. Branchez votre telephone via USB"
    Write-Host "   4. Acceptez l'autorisation sur votre telephone"
    exit 1
}

Write-Host "[OK] Telephone trouve: $deviceId" -ForegroundColor Green
Write-Host ""

# Recuperer l'adresse IP
Write-Host "[*] Recuperation de l'adresse IP..." -ForegroundColor Cyan
$output = & $adbPath -s $deviceId shell ip addr show wlan0
Write-Host $output
Write-Host ""

# Extraire l'IP avec regex
$ipMatch = $output | Select-String "inet (\d+\.\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value }

if ($ipMatch) {
    Write-Host "[OK] Adresse IP trouvee:" -ForegroundColor Green
    Write-Host ""
    Write-Host "    $ipMatch" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[*] Mettez a jour api_service.dart:" -ForegroundColor Cyan
    Write-Host "    static const String baseUrl = 'http://$ipMatch:8000/api/v1';" -ForegroundColor White
    Write-Host ""
    
    # Copier dans le presse-papiers (Windows)
    $ipMatch | Set-Clipboard
    Write-Host "[OK] IP copiee dans le presse-papiers!" -ForegroundColor Green
} else {
    Write-Host "[!] Impossible de trouver l'adresse IP" -ForegroundColor Red
    Write-Host ""
    Write-Host "[INFO] Assurez-vous que:" -ForegroundColor Yellow
    Write-Host "   - Le telephone est connecte au Wi-Fi"
    Write-Host "   - Le debogage USB est active"
    Write-Host "   - L'interface wlan0 existe (verifiez avec: adb shell ip addr show)"
}
