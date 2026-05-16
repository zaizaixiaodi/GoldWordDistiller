$ErrorActionPreference = "Continue"
$BITABLE_TOKEN = "Z5DubZ9DMaPkgDsbMWScnrgknSz"
$TABLE_ID = "tblg2nOd7LvMZCKC"
$BASE_DIR = "D:\AI Agent\金词挖掘机"
$COVER_DIR = "$BASE_DIR\scripts\covers"

$commands = Get-Content "$COVER_DIR\upload_commands.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$success = 0
$fail = 0

foreach ($cmd in $commands) {
    $recordId = $cmd.record_id
    $relFile = $cmd.file
    $absFile = "$BASE_DIR\$($relFile -replace '/','\')"
    $size = (Get-Item $absFile).Length
    $filename = "cover.jpg"

    Write-Host "`n[$recordId] $relFile ($size bytes)"

    # Step 1: Upload media - write JSON with UTF8 no BOM
    $uploadJson = "{`"file_name`":`"$filename`",`"parent_type`":`"bitable_image`",`"parent_node`":`"$BITABLE_TOKEN`",`"size`":`"$size`"}"
    [System.IO.File]::WriteAllText("$COVER_DIR\_upload_req.json", $uploadJson, [System.Text.UTF8Encoding]::new($false))

    Write-Host "  Uploading..." -NoNewline
    $uploadResp = & lark-cli api POST '/open-apis/drive/v1/medias/upload_all' --as user --data "@$COVER_DIR\_upload_req.json" --file "file=$absFile" 2>&1
    $uploadRespStr = $uploadResp -join "`n"

    try {
        $uploadResult = $uploadRespStr | ConvertFrom-Json
    } catch {
        Write-Host " FAIL (parse upload)"
        Write-Host "  $uploadRespStr"
        $fail++
        continue
    }

    if ($uploadResult.code -ne 0) {
        Write-Host " FAIL (upload code=$($uploadResult.code))"
        $fail++
        continue
    }

    $fileToken = $uploadResult.data.file_token
    Write-Host " OK (token: $fileToken)"

    # Step 2: Update record
    $updateJson = "{`"fields`":{`"封面`":[{`"file_token`":`"$fileToken`"}]}}"
    [System.IO.File]::WriteAllText("$COVER_DIR\_update_req.json", $updateJson, [System.Text.UTF8Encoding]::new($false))

    Write-Host "  Updating record..." -NoNewline
    $updateResp = & lark-cli api PUT "/open-apis/bitable/v1/apps/$BITABLE_TOKEN/tables/$TABLE_ID/records/$recordId" --as user --data "@$COVER_DIR\_update_req.json" 2>&1
    $updateRespStr = $updateResp -join "`n"

    try {
        $updateResult = $updateRespStr | ConvertFrom-Json
        if ($updateResult.code -eq 0) {
            Write-Host " OK"
            $success++
        } else {
            Write-Host " FAIL (update code=$($updateResult.code))"
            $fail++
        }
    } catch {
        Write-Host " FAIL (parse update)"
        Write-Host "  $updateRespStr"
        $fail++
    }

    Start-Sleep -Milliseconds 500
}

Write-Host "`n=== Done: $success success, $fail fail ==="

# Cleanup
Remove-Item "$COVER_DIR\_upload_req.json" -ErrorAction SilentlyContinue
Remove-Item "$COVER_DIR\_update_req.json" -ErrorAction SilentlyContinue
