<#
.SYNOPSIS
    Backward-compatible alias for scaffold_vault.ps1 -Kind story.

.DESCRIPTION
    The vault now supports multiple kinds of work (story / bugfix / initiative / effort / reference)
    via scaffold_vault.ps1. This wrapper preserves the original story-only invocation so existing
    calls keep working. For anything other than a ticket story, call scaffold_vault.ps1 directly.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Key,
    [string]$Title = '',
    [ValidateSet('not-started', 'in-progress', 'blocked', 'in-review', 'done')]
    [string]$Status = 'in-progress',
    [string]$Branch = '(none yet)',
    [string]$the tracker = '',
    [string]$Vault = $(if ($env:QUORUM_VAULT) { $env:QUORUM_VAULT } else { Join-Path $HOME 'quorum-vault' })
)
& (Join-Path $PSScriptRoot 'scaffold_vault.ps1') -Kind story `
    -Key $Key -Title $Title -Status $Status -Branch $Branch -the tracker $the tracker -Vault $Vault
