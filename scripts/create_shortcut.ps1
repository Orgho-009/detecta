$deskPath = [Environment]::GetFolderPath('Desktop')
$WshShell = New-Object -comObject WScript.Shell

$Shortcut = $WshShell.CreateShortcut("$deskPath\Detecta.lnk")
$Shortcut.TargetPath = "C:\detecta\Detecta.exe"
$Shortcut.WorkingDirectory = "C:\detecta"
$Shortcut.IconLocation = "C:\detecta\logo.ico"
$Shortcut.Description = "Detecta AI Security Camera Intelligence"
$Shortcut.Save()

$ShortcutLocal = $WshShell.CreateShortcut("C:\detecta\Detecta.lnk")
$ShortcutLocal.TargetPath = "C:\detecta\Detecta.exe"
$ShortcutLocal.WorkingDirectory = "C:\detecta"
$ShortcutLocal.IconLocation = "C:\detecta\logo.ico"
$ShortcutLocal.Description = "Detecta AI Security Camera Intelligence"
$ShortcutLocal.Save()

Write-Output "Shortcut successfully created on Desktop: $deskPath\Detecta.lnk"
