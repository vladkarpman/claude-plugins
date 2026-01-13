# Keyboard Typing Detection - Test Guide

## Implementation Status

✅ **Phase 1:** Detection script (analyze-typing.py) - COMPLETE
✅ **Phase 2:** Command updates (stop-recording.md) - COMPLETE
✅ **Phase 3:** YAML generation (generate-test.py) - COMPLETE
⏳ **Phase 4:** End-to-end testing - **REQUIRES USER**
✅ **Phase 5:** Documentation - COMPLETE

## Phase 4: End-to-End Testing

### Prerequisites

- Device connected (verify with `adb devices`)
- ffmpeg installed (verify with `ffmpeg -version`)
- YouTube app installed on device
- Plugin loaded in Claude Code session

### Test Steps

#### 1. Start Recording

```bash
/record-test youtube-typing-test
```

**Expected output:**
```
✓ ffmpeg available
✓ Device: RFCW318P7NV
✓ App: com.google.android.youtube
✓ Recording started

Recording in progress...

Perform your test actions, then run /stop-recording
```

#### 2. Perform Test Actions on Device

**Recommended test flow:**
1. Tap search icon
2. Type "flutter tutorial" in search box
3. Tap search/enter
4. Wait 2 seconds
5. Tap on first video
6. Wait 2 seconds

**Why this test:** Contains clear keyboard typing sequence with submit action.

#### 3. Stop Recording

```bash
/stop-recording
```

**Expected processing:**
1. Video and touch capture stops
2. Frames extracted (should see "Extracting frame..." messages)
3. **Typing detection runs** - should find 1-2 sequences
4. **Typing interview starts** (NEW!)

#### 4. Typing Interview

**Question 1:** "What text did you type in this sequence?"
**Answer:** `flutter tutorial`

**Question 2:** "Did you press Enter/Search after typing?"
**Answer:** `Yes` or `A`

**Expected:** Confirmation message showing typed text and submit flag

#### 5. Verification Interview (Optional)

If asked "Would you like to add verifications?", you can:
- Say **yes** to add checkpoints (recommended for full test)
- Say **no** to skip (faster, tests typing only)

If you say yes, select verifications at key points (e.g., "Search results loaded")

#### 6. Verify Generated YAML

**Check:** `tests/youtube-typing-test/test.yaml`

**Should contain:**
```yaml
tests:
  - name: youtube-typing-test
    steps:
      - tap: [50.0%, 10.0%]  # Search icon
      - type: {text: "flutter tutorial", submit: true}  # ✓ Type command with submit!
      # Replaced touches X-Y (8 keyboard taps)  # ✓ Comment showing replaced range

      - wait: 2s
      - tap: [50.0%, 40.0%]  # First video
```

**Verify:**
- ✅ Type command present (not individual keyboard taps)
- ✅ Submit flag set to true
- ✅ Comment showing replaced touch range
- ✅ Correct position in test sequence

#### 7. Run the Test

```bash
/run-test tests/youtube-typing-test/
```

**Expected execution:**
```
Running: youtube-typing-test
────────────────────────────────────────

  [1/5] tap [50.0%, 10.0%]
        ✓ Tapped at (540, 234)

  [2/5] type {text: "flutter tutorial", submit: true}
        ✓ Typed 16 characters
        ✓ Pressed Enter

  [3/5] wait 2s
        ✓ Waited 2.0s

  [4/5] tap [50.0%, 40.0%]
        ✓ Tapped at (540, 936)

────────────────────────────────────────
✓ PASSED  (4/4 steps in 5.2s)
```

**Verify on device:**
- Search box should show "flutter tutorial"
- Search should have been submitted (results page visible)
- First video should be playing

### Success Criteria

✅ **Detection:** Typing sequence identified correctly
✅ **Interview:** User can provide text and submit flag
✅ **Generation:** Type command appears in YAML (not individual taps)
✅ **Execution:** Text appears in app, submit works

### Troubleshooting

#### Issue: No typing sequences detected

**Possible causes:**
- Too few taps (< 3)
- Taps outside keyboard region (not in bottom 40%)
- Taps too far apart (> 1 second gap)

**Solution:** Tap more deliberately on keyboard, 3+ keys minimum

#### Issue: Wrong text detected

**Not applicable** - User provides text during interview, not auto-detected

#### Issue: Type command fails during execution

**Check:**
- Device still connected (`adb devices`)
- App in foreground
- Input field is focused

**Solution:** Ensure test focuses input field before typing

### Test Variations

#### Test 2: Multiple Typing Sequences

**Actions:**
1. Search for "android"
2. Clear search
3. Search for "ios development"

**Expected:** 2 type commands in YAML

#### Test 3: Typing Without Submit

**Actions:**
1. Tap username field
2. Type "john.doe@example.com"
3. Tap password field (don't press enter)

**Expected:** Type command with `submit: false`

#### Test 4: No Typing

**Actions:**
1. Only tap buttons and swipe
2. No keyboard interaction

**Expected:** No typing interview, no type commands

## Validation Checklist

After completing all tests:

- [ ] Detection script runs without errors
- [ ] Typing interview appears when sequences detected
- [ ] User can provide text for each sequence
- [ ] User can specify submit action
- [ ] Generated YAML contains type commands
- [ ] Type commands replace individual keyboard taps
- [ ] Comments show replaced touch ranges
- [ ] Tests execute successfully
- [ ] Text appears correctly in app
- [ ] Submit action works (if enabled)
- [ ] No typing interview when no sequences detected

## Next Steps

After Phase 4 passes:
1. Update CHANGELOG.md with v3.3.0 release notes
2. Consider additional test cases (emoji, special characters, etc.)
3. Monitor for edge cases in real usage

## Notes

- Typing detection is based on heuristics (position, timing, variance)
- False positives possible (non-typing taps in keyboard region)
- User interview provides ground truth (user knows what they typed)
- Submit detection relies on user memory (could show screenshot in future)
