# Recording Artifacts Reorganization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize test folder structure to move recording artifacts into `recording/` subfolder for cleaner organization

**Architecture:** All recording artifacts (touch_events.json, typing_sequences.json, verifications.json, checkpoints.json, recording.mp4, screenshots/) move into `tests/{name}/recording/` subdirectory. The test.yaml file stays at top level as it's the actual test, not a recording artifact.

**Tech Stack:** Python 3, Bash, Markdown (command files)

---

## Task 1: Update Python Scripts - analyze-typing.py

**Files:**
- Modify: `scripts/analyze-typing.py:25`
- Modify: `scripts/analyze-typing.py:140`

**Step 1: Write the test for path changes**

Since this is path refactoring, manual verification will suffice. Skip automated test.

**Step 2: Update touch_events.json path**

```python
# Line 25
events_file = test_folder / "recording" / "touch_events.json"
```

**Step 3: Update typing_sequences.json path**

```python
# Line 140
output_file = test_folder / "recording" / "typing_sequences.json"
```

**Step 4: Verify changes**

Run: `python3 scripts/analyze-typing.py --help` (check no syntax errors)
Expected: Help message or error about missing args (not syntax error)

**Step 5: Commit**

```bash
git add scripts/analyze-typing.py
git commit -m "refactor: use recording/ subfolder in analyze-typing.py

- Read touch_events.json from recording/ subdirectory
- Write typing_sequences.json to recording/ subdirectory

Part of recording artifacts reorganization."
```

---

## Task 2: Update Python Scripts - analyze-checkpoints.py

**Files:**
- Modify: `scripts/analyze-checkpoints.py:261-262`

**Step 1: Update events and screenshots paths**

```python
# Lines 261-262
events_file = test_folder / "recording" / "touch_events.json"
screenshots_dir = test_folder / "recording" / "screenshots"
```

**Step 2: Verify syntax**

Run: `python3 scripts/analyze-checkpoints.py` (check no syntax errors)
Expected: Error about missing args (not syntax error)

**Step 3: Commit**

```bash
git add scripts/analyze-checkpoints.py
git commit -m "refactor: use recording/ subfolder in analyze-checkpoints.py

- Read touch_events.json from recording/
- Read screenshots from recording/screenshots/

Part of recording artifacts reorganization."
```

---

## Task 3: Update Python Scripts - generate-test.py

**Files:**
- Modify: `scripts/generate-test.py:263-265`

**Step 1: Update input file paths**

```python
# Lines 263-265
events_file = test_folder / "recording" / "touch_events.json"
verifications_file = test_folder / "recording" / "verifications.json"
typing_file = test_folder / "recording" / "typing_sequences.json"
```

Note: Line 287 stays unchanged - `test.yaml` remains at top level.

**Step 2: Verify syntax**

Run: `python3 scripts/generate-test.py`
Expected: Usage error (not syntax error)

**Step 3: Commit**

```bash
git add scripts/generate-test.py
git commit -m "refactor: use recording/ subfolder in generate-test.py

- Read all input files from recording/ subdirectory
- Keep test.yaml output at top level (not an artifact)

Part of recording artifacts reorganization."
```

---

## Task 4: Update Python Scripts - extract-frames.py

**Files:**
- Modify: `scripts/extract-frames.py:75`

**Step 1: Update screenshot path in metadata**

```python
# Line 75
event["screenshot"] = f"recording/screenshots/touch_{event['index']:03d}.png"
```

**Step 2: Verify syntax**

Run: `python3 scripts/extract-frames.py`
Expected: Usage error (not syntax error)

**Step 3: Commit**

```bash
git add scripts/extract-frames.py
git commit -m "refactor: use recording/ prefix in screenshot paths

- Update screenshot metadata path to recording/screenshots/

Part of recording artifacts reorganization."
```

---

## Task 5: Update Python Scripts - analyze-touches.py

**Files:**
- Modify: `scripts/analyze-touches.py:73-74`

**Step 1: Update file paths**

```python
# Lines 73-74
events_file = output_path / "recording" / "touch_events.json"
screenshots_dir = output_path / "recording" / "screenshots"
```

**Step 2: Verify syntax**

Run: `python3 scripts/analyze-touches.py`
Expected: Usage error (not syntax error)

**Step 3: Commit**

```bash
git add scripts/analyze-touches.py
git commit -m "refactor: use recording/ subfolder in analyze-touches.py

- Read touch_events.json from recording/
- Read screenshots from recording/screenshots/

Part of recording artifacts reorganization."
```

---

## Task 6: Update Commands - record-test.md

**Files:**
- Modify: `commands/record-test.md:89`
- Modify: `commands/record-test.md:128`
- Modify: `commands/record-test.md:139`

**Step 1: Update directory creation**

Line 89:
```bash
mkdir -p tests/{TEST_NAME}/recording/screenshots tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
```

**Step 2: Update video recording path**

Line 128:
```bash
bash ./scripts/record-video.sh {DEVICE_ID} tests/{TEST_NAME}/recording/recording.mp4 &
```

**Step 3: Update touch monitor output directory**

Line 139:
```bash
python3 ./scripts/monitor-touches.py {DEVICE_ID} tests/{TEST_NAME}/recording &
```

**Step 4: Verify no syntax issues**

Read the file to ensure markdown is valid.

**Step 5: Commit**

```bash
git add commands/record-test.md
git commit -m "refactor: create recording/ subfolder in record-test

- Create recording/screenshots/ subdirectory
- Write video to recording/recording.mp4
- Output touch events to recording/ directory

Part of recording artifacts reorganization."
```

---

## Task 7: Update Commands - stop-recording.md (Part 1: Steps 5-7)

**Files:**
- Modify: `commands/stop-recording.md:77-78` (Step 5)
- Modify: `commands/stop-recording.md:89` (Step 6)
- Modify: `commands/stop-recording.md:106` (Step 7)

**Step 1: Update video verification paths (Step 5)**

Lines 77-78:
```bash
ls -la {TEST_FOLDER}/recording/recording.mp4
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 {TEST_FOLDER}/recording/recording.mp4
```

**Step 2: Update touch events read path (Step 6)**

Line 89:
```markdown
**Tool:** `Read` file `{TEST_FOLDER}/recording/touch_events.json`
```

**Step 3: Update extract-frames command (Step 7)**

Line 106:
```bash
python3 ./scripts/extract-frames.py {TEST_FOLDER}/recording/recording.mp4 {TEST_FOLDER}/recording/touch_events.json {VIDEO_START_TIME} {TEST_FOLDER}/recording/screenshots
```

**Step 4: Verify markdown**

Read the file to ensure formatting is correct.

**Step 5: Commit**

```bash
git add commands/stop-recording.md
git commit -m "refactor: update stop-recording steps 5-7 for recording/

- Update video verification to recording/recording.mp4
- Read touch_events.json from recording/
- Extract frames to recording/screenshots/

Part 1 of stop-recording.md refactor."
```

---

## Task 8: Update Commands - stop-recording.md (Part 2: Steps 8.1-8.6)

**Files:**
- Modify: `commands/stop-recording.md:133` (Step 8.1)
- Modify: `commands/stop-recording.md:142` (Step 8.2)
- Modify: `commands/stop-recording.md:176` (Step 8.4.2)
- Modify: `commands/stop-recording.md:249` (Step 8.4.5)
- Modify: `commands/stop-recording.md:380` (Step 8.6)

**Step 1: Update checkpoint detection output (Step 8.1)**

Line 133:
```bash
python3 ./scripts/analyze-checkpoints.py {TEST_FOLDER} > {TEST_FOLDER}/recording/checkpoints.json
```

**Step 2: Update checkpoint read path (Step 8.2)**

Line 142:
```markdown
**Tool:** `Read` file `{TEST_FOLDER}/recording/checkpoints.json`
```

**Step 3: Update typing sequences read (Step 8.4.2)**

Line 176:
```markdown
**Tool:** `Read` file `{TEST_FOLDER}/recording/typing_sequences.json`
```

**Step 4: Update typing sequences write (Step 8.4.5)**

Line 249:
```markdown
**Tool:** `Write` to `{TEST_FOLDER}/recording/typing_sequences.json`
```

**Step 5: Update verifications write (Step 8.6)**

Line 380:
```markdown
**Tool:** `Write` to `{TEST_FOLDER}/recording/verifications.json`
```

**Step 6: Commit**

```bash
git add commands/stop-recording.md
git commit -m "refactor: update stop-recording steps 8.1-8.6 for recording/

- Write checkpoints.json to recording/
- Read/write typing_sequences.json in recording/
- Write verifications.json to recording/

Part 2 of stop-recording.md refactor."
```

---

## Task 9: Update Commands - stop-recording.md (Part 3: Output Files)

**Files:**
- Modify: `commands/stop-recording.md:490-502` (Output Files section)

**Step 1: Update documentation structure**

Lines 490-502:
```markdown
## Output Files

After completion:
\`\`\`
{TEST_FOLDER}/
├── test.yaml             ← Generated test (run with /run-test)
└── recording/            ← Recording artifacts (for debugging)
    ├── touch_events.json     ← Raw touch data
    ├── typing_sequences.json ← Detected typing + user input
    ├── verifications.json    ← User-selected verifications
    ├── checkpoints.json      ← Detected verification points
    ├── recording.mp4         ← Video file
    └── screenshots/          ← Extracted frames
        ├── touch_001.png
        ├── touch_002.png
        └── ...
\`\`\`
```

**Step 2: Commit**

```bash
git add commands/stop-recording.md
git commit -m "docs: update stop-recording output structure

- Document recording/ subfolder in output files section
- Show test.yaml at top level, artifacts in recording/

Part 3 of stop-recording.md refactor."
```

---

## Task 10: Update Commands - create-test.md and generate-test.md

**Files:**
- Modify: `commands/create-test.md:47`
- Modify: `commands/create-test.md:106-111`
- Modify: `commands/generate-test.md:67`

**Step 1: Remove screenshots from create-test mkdir**

commands/create-test.md line 47:
```bash
mkdir -p tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
```

**Step 2: Update create-test folder structure docs**

commands/create-test.md lines 106-111:
```markdown
tests/{TEST_NAME}/
├── test.yaml
├── baselines/
└── reports/
```

**Step 3: Remove screenshots from generate-test mkdir**

commands/generate-test.md line 67:
```bash
mkdir -p tests/{TEST_NAME}/baselines tests/{TEST_NAME}/reports
```

**Step 4: Commit**

```bash
git add commands/create-test.md commands/generate-test.md
git commit -m "refactor: remove screenshots/ from non-recording commands

- create-test no longer creates screenshots/ (recording artifact)
- generate-test no longer creates screenshots/ (recording artifact)
- Update folder structure documentation

Part of recording artifacts reorganization."
```

---

## Task 11: Update Documentation - CLAUDE.md

**Files:**
- Modify: `CLAUDE.md:149-164` (Test Folder Structure section)

**Step 1: Update structure documentation**

Lines 149-164:
```markdown
## Test Folder Structure (v3.3+)

\`\`\`
tests/{name}/
├── test.yaml           # Test definition
└── recording/          # Recording artifacts (for debugging)
    ├── touch_events.json   # Raw touch events with timestamps
    ├── typing_sequences.json # Detected keyboard typing
    ├── verifications.json  # User-selected checkpoints
    ├── checkpoints.json    # AI-detected verification points
    ├── recording.mp4       # Video recording
    └── screenshots/        # Extracted frames from video
        ├── touch_001.png   # Frame 100ms before touch 1
        ├── touch_002.png   # Frame 100ms before touch 2
        └── ...
\`\`\`

Note: `tests/` folder is gitignored - test artifacts are local only.

**Version History:**
- v3.3+: Recording artifacts in recording/ subfolder
- v2.0-3.2: All artifacts at top level alongside test.yaml
- v1.0: `tests/{name}.test.yaml` (single file)
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with v3.3 folder structure

- Document recording/ subfolder organization
- Add version history showing structure evolution

Part of recording artifacts reorganization."
```

---

## Task 12: Update Integration Tests

**Files:**
- Modify: `tests/integration/test_verification_interview.sh:18`
- Modify: `tests/integration/test_verification_interview.sh:21`
- Modify: `tests/integration/test_verification_interview.sh:34`
- Modify: `tests/integration/test_verification_interview.sh:39`
- Modify: `tests/integration/test_verification_interview.sh:43`
- Modify: `tests/integration/test_verification_interview.sh:60`

**Step 1: Update all test paths**

Line 18:
```bash
mkdir -p "$TEST_DIR/recording/screenshots"
```

Line 21:
```bash
cat > "$TEST_DIR/recording/touch_events.json" << 'EOF'
```

Line 34 (in loop):
```bash
touch "$TEST_DIR/recording/screenshots/touch_$(printf "%03d" $i).png"
```

Line 39:
```bash
python3 scripts/analyze-checkpoints.py "$TEST_DIR" > "$TEST_DIR/recording/checkpoints.json" 2>&1
```

Line 43:
```bash
if ! jq -e '.checkpoints | length > 0' "$TEST_DIR/recording/checkpoints.json" >/dev/null 2>&1; then
```

Line 60:
```bash
cat > "$TEST_DIR/recording/verifications.json" << 'EOF'
```

**Step 2: Run integration test**

Run: `./tests/integration/test_verification_interview.sh`
Expected: All assertions pass

**Step 3: Commit**

```bash
git add tests/integration/test_verification_interview.sh
git commit -m "test: update integration test for recording/ structure

- Create recording/screenshots/ directory
- Write test files to recording/ subdirectory
- Update all assertions to check recording/ paths

Part of recording artifacts reorganization."
```

---

## Task 13: Verification - Path Audit

**Step 1: Check for remaining old paths in Python**

Run:
```bash
grep -rn '"touch_events.json"' scripts/ --include="*.py" | grep -v "recording/"
grep -rn '"screenshots"' scripts/ --include="*.py" | grep -v "recording/"
```

Expected: No results

**Step 2: Check for remaining old paths in commands**

Run:
```bash
grep -rn "touch_events.json" commands/ | grep -v "recording/"
grep -rn "/screenshots" commands/ | grep -v "recording/"
```

Expected: Only references in comments or documentation

**Step 3: Run integration test**

Run: `./tests/integration/test_verification_interview.sh`
Expected: PASS

**Step 4: Document verification**

No commit - this is verification only.

---

## Verification Strategy

After all tasks complete:

1. **Path Audit:** Verify no old path patterns remain in code
2. **Integration Test:** Run test_verification_interview.sh - should pass
3. **Manual Test:** Record a real test and verify structure

Manual test steps:
```bash
/record-test structure-test
[perform 3-4 actions on device]
/stop-recording
[skip verifications]
ls -R tests/structure-test/

# Expected:
# tests/structure-test/
# ├── test.yaml
# └── recording/
#     ├── checkpoints.json
#     ├── recording.mp4
#     ├── screenshots/
#     ├── touch_events.json
#     ├── typing_sequences.json
#     └── verifications.json

/run-test tests/structure-test/
# Expected: Test runs successfully
```

---

## Success Criteria

✅ All Python scripts read/write from recording/ subdirectory
✅ Commands create recording/ subfolder
✅ test.yaml remains at top level
✅ Integration test passes
✅ Manual recording test produces correct structure
✅ Test execution works with new structure
✅ No old path patterns remain in codebase
