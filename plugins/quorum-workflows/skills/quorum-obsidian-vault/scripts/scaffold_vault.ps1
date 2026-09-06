<#
.SYNOPSIS
    Scaffold an Obsidian vault note set for any KIND of work, from the bundled templates.

.DESCRIPTION
    One scaffolder for every kind of work the vault captures. -Kind drives three things:
      1. the top-level folder + path shape,
      2. which template(s) get expanded,
      3. the Home.md section the entry is filed under.

    Layout produced (idempotent — never clobbers an existing note):
      story | bugfix  -> Stories\<Key>\<Key>.md + status.md + attachments\
      initiative      -> Initiatives\<slug>\<slug>.md + status.md + lessons.md
                         + decisions\_index.md (+ decisions\)            [always]
                         + migration\dashboard.md (+ migration\areas\)   [only -Subtype migration]
                         + attachments\
      effort          -> Efforts\<slug>.md                  (single self-contained note)
      reference       -> Resources\<slug>.md                (single evergreen note)

    The script only lays down the skeleton with frontmatter filled in. Filling the body
    (summary, goal, AC, findings, progress) is the agent's job afterward — that content comes
    from Jira / the conversation / the work itself, not from a template.

.EXAMPLE
    pwsh scaffold_vault.ps1 -Kind story -Key PROJ-68433 -Title "AcmeSync virtual tours" -Branch PROJ-68433-virtual-tours

.EXAMPLE
    pwsh scaffold_vault.ps1 -Kind initiative -Subtype migration -Title "platform-v2 migration" -Owner alex

.EXAMPLE
    pwsh scaffold_vault.ps1 -Kind effort -Title "spike: evaluate gRPC vs REST"

.EXAMPLE
    pwsh scaffold_vault.ps1 -Kind reference -Subtype recipe -Title "AcmeSync getfees probe"
#>
[CmdletBinding()]
param(
    [ValidateSet('story', 'bugfix', 'initiative', 'effort', 'reference')]
    [string]$Kind = 'story',

    [string]$Key = '',          # required for story|bugfix
    [string]$Slug = '',         # optional id for ticketless kinds; else auto-slugified from -Title
    [string]$Title = '',
    [string]$Subtype = '',      # initiative: poc|migration|tooling ; reference: recipe|feedback|repo-map

    [ValidateSet('not-started', 'in-progress', 'blocked', 'in-review', 'done', 'abandoned', 'archived')]
    [string]$Status = 'in-progress',

    [string]$Branch = '(none yet)',
    [string]$Jira = '',
    [string]$Owner = '',
    [string]$Vault = $(if ($env:QUORUM_VAULT) { $env:QUORUM_VAULT } else { Join-Path $HOME 'quorum-vault' })
)

$ErrorActionPreference = 'Stop'
$skillDir = Split-Path -Parent $PSScriptRoot
$assets = Join-Path $skillDir 'assets'
$today = (Get-Date).ToString('yyyy-MM-dd')
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

function Get-Slug([string]$s) {
    $x = $s.ToLower().Trim()
    $x = $x -replace '[^a-z0-9]+', '-'
    $x = $x -replace '(^-+|-+$)', ''
    return $x
}

function Expand-Template([string]$Path, [hashtable]$Subs, [string[]]$Strip) {
    $text = Get-Content -Path $Path -Raw -Encoding utf8
    # Drop whole lines that carry a strippable token whose value is empty
    # (kills dangling '[ in Jira]()' / dead QA-plan links on ticketless notes).
    foreach ($t in $Strip) {
        if ([string]::IsNullOrWhiteSpace($Subs[$t])) {
            $kept = ($text -split "`r?`n") | Where-Object { $_ -notmatch [regex]::Escape("{{$t}}") }
            $text = $kept -join "`n"
        }
    }
    foreach ($k in $Subs.Keys) { $text = $text.Replace("{{$k}}", [string]$Subs[$k]) }
    return $text
}

# ---- Resolve identifier --------------------------------------------------
$ticketed = $Kind -in @('story', 'bugfix')
if ($ticketed) {
    if (-not $Key) { throw "Kind '$Kind' requires -Key (e.g. -Key PROJ-68433)." }
    $id = $Key
}
else {
    if ($Slug) { $id = Get-Slug $Slug }
    elseif ($Title) { $id = Get-Slug $Title }
    else { throw "Kind '$Kind' requires -Slug or -Title to derive an identifier." }
}
$displayTitle = if ($Title) { $Title } else { $id }

# ---- Token values --------------------------------------------------------
$jiraUrl = if ($ticketed) { if ($Jira) { $Jira } else { "https://your-org.atlassian.net/browse/$id" } } else { '' }
$qaPlan = if ($ticketed) { "qa-test-plans/$id/plan.md" } else { '' }
$lessonsLink = if ($Kind -eq 'initiative') { '[[lessons]]' } else { '' }

$subs = @{
    ID = $id; KEY = $id; TITLE = $displayTitle; KIND = $Kind; SUBTYPE = $Subtype
    STATUS = $Status; BRANCH = $Branch; OWNER = $Owner; DATE = $today
    JIRA_URL = $jiraUrl; QA_PLAN = $qaPlan; LESSONS_LINK = $lessonsLink; INITIATIVE = $id
}
$strip = @('JIRA_URL', 'QA_PLAN', 'LESSONS_LINK')

# ---- Plan: folder + (template -> output file) ----------------------------
$created = @(); $skipped = @()
function Stamp([string]$TemplateName, [string]$OutPath) {
    if (Test-Path $OutPath) { $script:skipped += $OutPath; return }
    Write-Utf8 $OutPath (Expand-Template (Join-Path $assets $TemplateName) $subs $strip)
    $script:created += $OutPath
}

switch ($Kind) {
    { $_ -in 'story', 'bugfix' } {
        $dir = Join-Path $Vault "Stories\$id"
        New-Item -ItemType Directory -Force -Path (Join-Path $dir 'attachments') | Out-Null
        $overviewTemplate = if ($Kind -eq 'bugfix') { 'bugfix-note.md' } else { 'story-note.md' }
        Stamp $overviewTemplate (Join-Path $dir "$id.md")
        Stamp 'status-note.md' (Join-Path $dir 'status.md')
    }
    'initiative' {
        $dir = Join-Path $Vault "Initiatives\$id"
        New-Item -ItemType Directory -Force -Path (Join-Path $dir 'attachments') | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $dir 'decisions') | Out-Null
        Stamp 'initiative-note.md' (Join-Path $dir "$id.md")
        Stamp 'status-note.md' (Join-Path $dir 'status.md')
        Stamp 'lessons-note.md' (Join-Path $dir 'lessons.md')
        $adl = "---`nkind: decision-index`nof: `"[[$id]]`"`ntags:`n  - decision-index`n  - $id`n---`n`n" +
        "# $displayTitle — Decision Log (ADL)`n`n" +
        "Immutable MADR records, newest on top. Add one with the ``decision-note.md`` template: copy it to ``decisions/NNNN-verb-phrase.md``, fill it, then add a row here. When a decision changes, write a NEW record and link them with ``supersedes`` / ``superseded-by``.`n`n" +
        "| # | Decision | Status | Date |`n|---|---|---|---|`n<!-- | [[0001-...]] | ... | accepted | YYYY-MM-DD | -->`n"
        $adlPath = Join-Path $dir 'decisions\_index.md'
        if (Test-Path $adlPath) { $skipped += $adlPath } else { Write-Utf8 $adlPath $adl; $created += $adlPath }

        if ($Subtype -eq 'migration') {
            New-Item -ItemType Directory -Force -Path (Join-Path $dir 'migration\areas') | Out-Null
            $dash = "---`nkind: migration-dashboard`nof: `"[[$id]]`"`ntags:`n  - migration-dashboard`n  - $id`n---`n`n" +
            "# $displayTitle — Migration Dashboard`n`n" +
            "One note per seam/component under ``areas/`` (use the ``migration-area.md`` template). Status flows not-started -> in-progress -> migrated -> verified.`n`n" +
            "| Area | Status | Owner | Target |`n|---|---|---|---|`n<!-- | [[auth-module]] | not-started | | | -->`n`n" +
            "**Burndown:** remaining (not-started + in-progress) vs migrated + verified — update as areas move.`n`n" +
            "> First session: enumerate the legacy solution's components/seams, create one area note each, then fill this table.`n"
            $dashPath = Join-Path $dir 'migration\dashboard.md'
            if (Test-Path $dashPath) { $skipped += $dashPath } else { Write-Utf8 $dashPath $dash; $created += $dashPath }
        }
    }
    'effort' {
        $dir = Join-Path $Vault 'Efforts'
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Stamp 'effort-note.md' (Join-Path $dir "$id.md")
    }
    'reference' {
        $dir = Join-Path $Vault 'Resources'
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        $refTemplate = if ($Subtype -eq 'feedback') { 'reference-feedback.md' } else { 'reference-recipe.md' }
        Stamp $refTemplate (Join-Path $dir "$id.md")
    }
}

# ---- Maintain Home.md (kind-segmented map of content) --------------------
$homeFile = Join-Path $Vault 'Home.md'
$heading = switch ($Kind) {
    { $_ -in 'story', 'bugfix' } { '## Stories' }
    'initiative' { '## Initiatives & POCs' }
    'effort' { '## Efforts & Spikes' }
    'reference' { '## Resources' }
}
$marker = switch ($Kind) {
    'bugfix' { ' (bug)' }
    'initiative' { if ($Subtype) { " ($Subtype)" } else { '' } }
    'reference' { if ($Subtype) { " ($Subtype)" } else { '' } }
    default { '' }
}
$line = "- [[$id]] — $displayTitle$marker"

if (-not (Test-Path $homeFile)) {
    $skeleton = "# Work Vault`n`n" +
    "Knowledge bases that survive a session. Each entry links to its overview/home note; open the linked ``[[status]]`` (where present) for live progress and handoff.`n`n" +
    "## Stories`n`n## Initiatives & POCs`n`n## Efforts & Spikes`n`n## Resources`n"
    Write-Utf8 $homeFile $skeleton
}
$content = Get-Content -Path $homeFile -Raw -Encoding utf8
if ($content -notmatch "\[\[$([regex]::Escape($id))\]\]") {
    $lines = @($content -split "`r?`n")
    $idx = [array]::IndexOf($lines, $heading)
    if ($idx -lt 0) {
        # heading missing (older Home.md) — append a fresh section
        $newLines = $lines + @('', $heading, '', $line)
    }
    else {
        # find the section body (until the next '## ' heading or EOF), keep existing items
        $end = $idx + 1
        while ($end -lt $lines.Count -and $lines[$end] -notmatch '^## ') { $end++ }
        $items = @()
        for ($k = $idx + 1; $k -lt $end; $k++) { if ($lines[$k].Trim() -ne '') { $items += $lines[$k] } }
        $items = @($line) + $items   # newest on top
        $before = $lines[0..$idx]
        $after = if ($end -lt $lines.Count) { $lines[$end..($lines.Count - 1)] } else { @() }
        $newLines = $before + @('') + $items + @('') + $after
    }
    Write-Utf8 $homeFile (($newLines -join "`n").TrimEnd() + "`n")
}

# ---- Report --------------------------------------------------------------
Write-Host "Vault:  $Vault"
Write-Host "Kind:   $Kind$(if($Subtype){" ($Subtype)"})   Id: $id"
foreach ($c in $created) { Write-Host "  created: $c" }
foreach ($s in $skipped) { Write-Host "  kept (already exists): $s" }
Write-Host ""
switch ($Kind) {
    { $_ -in 'story', 'bugfix' } { Write-Host "Next: fill Summary / User Story / Acceptance Criteria from Jira; keep status.md current as you work." }
    'initiative' { Write-Host "Next: write Goal / Definition of Done from the user; log progress in status.md; record significant choices as decisions/NNNN-*.md; append durable insights to lessons.md." }
    'effort' { Write-Host "Next: state the Goal/Question + timebox; log what you try; capture Findings; record a go/no-go Outcome. Promote to an initiative if it outgrows one note." }
    'reference' { Write-Host "Next: fill the procedure/facts so it can be reread verbatim later. Bump 'updated' whenever you re-verify." }
}
