param(
  [Parameter(Mandatory=$true)][ValidateSet("codex","claude","cursor","agents","openclaw","path")][string]$Target,
  [ValidateSet("global","project")][string]$Scope = "global",
  [string]$ProjectDir = ".",
  [string]$Path,
  [switch]$Link,
  [switch]$Force,
  [switch]$DryRun
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArgsList = @("$ScriptDir/install.py", "install", "--target", $Target, "--scope", $Scope, "--project-dir", $ProjectDir)
if ($Path) { $ArgsList += @("--path", $Path) }
if ($Link) { $ArgsList += "--link" }
if ($Force) { $ArgsList += "--force" }
if ($DryRun) { $ArgsList += "--dry-run" }
& python @ArgsList
exit $LASTEXITCODE
