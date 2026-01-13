# Touch Event Parser

Parse `adb shell getevent -lt` output to detect user touch interactions.

## Starting the Event Stream

```bash
adb -s {device-id} shell getevent -lt
```

## Event Format

Raw events look like:
```
[    1234.567890] /dev/input/event2: EV_ABS ABS_MT_POSITION_X 000002a8
[    1234.567891] /dev/input/event2: EV_ABS ABS_MT_POSITION_Y 00000438
[    1234.567892] /dev/input/event2: EV_KEY BTN_TOUCH DOWN
[    1234.890123] /dev/input/event2: EV_KEY BTN_TOUCH UP
```

## Coordinate Conversion

ADB getevent returns raw hardware coordinates. Convert to screen coordinates:

```
screen_x = (raw_x / max_x) * screen_width
screen_y = (raw_y / max_y) * screen_height
```

Get max values with: `adb shell getevent -p`

## Gesture Detection

### Tap
- BTN_TOUCH DOWN followed by UP
- Duration < 200ms
- Movement < 50 pixels
- **Output:** `{type: "tap", x, y, timestamp}`

### Long Press
- BTN_TOUCH DOWN followed by UP
- Duration >= 500ms
- Movement < 50 pixels
- **Output:** `{type: "long_press", x, y, duration, timestamp}`

### Swipe
- BTN_TOUCH DOWN followed by UP
- Movement >= 100 pixels
- **Output:** `{type: "swipe", start_x, start_y, end_x, end_y, direction, timestamp}`

Direction calculation:
- `|dx| > |dy|` and `dx > 0` → "right"
- `|dx| > |dy|` and `dx < 0` → "left"
- `|dy| > |dx|` and `dy > 0` → "down"
- `|dy| > |dx|` and `dy < 0` → "up"

## Integration with Recording

When a gesture is detected:
1. Record timestamp and coordinates
2. Trigger screenshot capture
3. Get elements at touch location
4. Merge with element-based detection for confirmation

## Getting Max Coordinate Values

Before parsing, get the device's max touch coordinates:

```bash
adb -s {device} shell getevent -p | grep -A 5 "ABS_MT_POSITION"
```

Output example:
```
ABS_MT_POSITION_X: value 0, min 0, max 1079
ABS_MT_POSITION_Y: value 0, min 0, max 2339
```

Store max_x and max_y for coordinate conversion.

## Batch Parsing (Post-Processing)

When parsing a complete touch_log.txt file after recording:

1. Read entire file
2. Parse line by line, building gesture list
3. For each gesture, convert coordinates using stored max values
4. Return array of gestures with screen coordinates

Example batch parsing flow:
```
touch_log.txt → parse all events → detect gestures → convert coords → [{type, x, y, timestamp}, ...]
```

This is more accurate than real-time parsing because we have complete data.

## Example Parse Loop

```
touch_state = {down: false, x: 0, y: 0, time: 0}

for each event:
  if EV_ABS ABS_MT_POSITION_X:
    touch_state.x = parse_hex(value)
  if EV_ABS ABS_MT_POSITION_Y:
    touch_state.y = parse_hex(value)
  if EV_KEY BTN_TOUCH DOWN:
    touch_state.down = true
    touch_state.start_time = timestamp
    touch_state.start_x = touch_state.x
    touch_state.start_y = touch_state.y
  if EV_KEY BTN_TOUCH UP:
    duration = timestamp - touch_state.start_time
    distance = sqrt((x - start_x)^2 + (y - start_y)^2)

    if duration < 200ms and distance < 50:
      emit TAP event
    elif duration >= 500ms and distance < 50:
      emit LONG_PRESS event
    elif distance >= 100:
      emit SWIPE event

    touch_state.down = false
```
