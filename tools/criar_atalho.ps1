# Cria no ambiente de trabalho o atalho "OSMbot (dev)": corre a ultima versao do codigo, sem consola,
# com o ícone do osmbot compilado. Uso: powershell -File tools\criar_atalho.ps1
$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $desktop "OSMbot (dev).lnk"))
$link.TargetPath = Join-Path $root ".venv\Scripts\pythonw.exe"
$link.Arguments = '"' + (Join-Path $root "tools\osmbot_janela.pyw") + '"'
$link.WorkingDirectory = $root
$link.IconLocation = (Join-Path $root "tools\assets\osmbot.ico") + ",0"
$link.WindowStyle = 7
$link.Description = "OSMbot a partir do código"
$link.Save()
Write-Output "Atalho criado em $desktop"
