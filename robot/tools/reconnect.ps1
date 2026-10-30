# Rejoin the robot hotspot (if needed) and wait until SSH on the robot answers.
$ssid = 'HW-5930E4CB'
for ($i = 0; $i -lt 30; $i++) {
    $cur = (netsh wlan show interfaces | Select-String "^\s+SSID\s" | Select-Object -First 1)
    $state = (netsh wlan show interfaces | Select-String "^\s+State\s" | Select-Object -First 1)
    if ($cur -notmatch $ssid -or $state -notmatch 'connected') {
        netsh wlan connect name=$ssid ssid=$ssid interface="Wi-Fi" | Out-Null
        Start-Sleep -Seconds 8
    }
    $t = New-Object Net.Sockets.TcpClient
    $ok = $t.ConnectAsync('192.168.149.1', 22).Wait(2000) -and $t.Connected
    $t.Close()
    if ($ok) { "robot reachable (attempt $($i + 1))"; exit 0 }
    Start-Sleep -Seconds 3
}
"robot NOT reachable"; netsh wlan show interfaces | Select-String "^\s+(SSID|State|Signal)\s" | ForEach-Object { $_.Line.Trim() }
exit 1
