# YAML Test Actions Reference

Complete reference for all actions in YAML mobile tests.

## Tap Actions

### Tap by Text/Description
```yaml
- tap: "Button text"
```
Finds element by text/description and taps it.

### Tap by Coordinates (Pixels)
```yaml
- tap: [100, 200]
```
Taps at specific x, y coordinates (pixels from top-left).

### Tap by Coordinates (Percentage)
```yaml
- tap: ["50%", "75%"]
```
Taps at percentage of screen width/height. Preferred for cross-device compatibility.

### Double Tap
```yaml
- double_tap: "Element"
- double_tap: [100, 200]
- double_tap: ["50%", "75%"]
```

### Long Press
```yaml
# Default duration (500ms)
- long_press: "Element"
- long_press: [100, 200]

# Custom duration
- long_press:
    element: "Element"
    duration: 2000  # milliseconds
```

## Type Actions

### Basic Type
```yaml
- type: "Hello world"
```
Types text into currently focused field.

### Type with Submit
```yaml
- type:
    text: "Search query"
    submit: true  # Press enter after typing
```

## Swipe Actions

### Simple Swipe
```yaml
- swipe: up
- swipe: down
- swipe: left
- swipe: right
```

### Swipe with Options
```yaml
- swipe:
    direction: up
    distance: 800    # pixels (optional)
    x: 540           # start x coordinate (optional)
    y: 1200          # start y coordinate (optional)
```

## Button Press

```yaml
# Navigation
- press: back        # Android back button (Android only)
- press: home        # Home button

# Volume
- press: volume_up
- press: volume_down

# Input
- press: enter       # Enter/return key

# Android TV (D-pad)
- press: dpad_center
- press: dpad_up
- press: dpad_down
- press: dpad_left
- press: dpad_right
```

## Wait Actions

```yaml
- wait: 2s      # 2 seconds
- wait: 500ms   # 500 milliseconds
- wait: 1m      # 1 minute
```

## App Control

### Launch App
```yaml
# Launch configured app (from config.app)
- launch_app

# Launch specific app
- launch_app: "com.other.app"
```

### Terminate App
```yaml
# Stop configured app
- terminate_app

# Stop specific app
- terminate_app: "com.other.app"
```

### Install App
```yaml
- install_app: "/path/to/app.apk"      # Android
- install_app: "/path/to/app.ipa"      # iOS device
- install_app: "/path/to/app.app"      # iOS simulator
```

### Uninstall App
```yaml
- uninstall_app: "com.example.app"
```

### List Apps
```yaml
- list_apps  # Lists all installed apps (useful for debugging)
```

## Orientation

### Set Orientation
```yaml
- set_orientation: portrait
- set_orientation: landscape
```

### Get Orientation
```yaml
- get_orientation  # Returns current orientation (useful for conditionals)
```

## Screen Info

### Get Screen Size
```yaml
- get_screen_size  # Returns width and height in pixels
```

### List Elements
```yaml
- list_elements  # Lists all elements on screen with coordinates
```
Useful for debugging when element not found.

## URL

```yaml
- open_url: "https://example.com"
```
Opens URL in device browser.

## Screenshot Actions

### Take Screenshot (Display Only)
```yaml
- screenshot: "descriptive_name"
```
Takes screenshot for viewing in test output.

### Save Screenshot to File
```yaml
- save_screenshot: "/path/to/file.png"
```
Saves screenshot to specific file path.

## Mobile-MCP Tool Mapping

| YAML Action | mobile-mcp Tool |
|-------------|-----------------|
| `tap: "X"` | `mobile_list_elements_on_screen` + `mobile_click_on_screen_at_coordinates` |
| `tap: [x,y]` | `mobile_click_on_screen_at_coordinates` |
| `double_tap` | `mobile_double_tap_on_screen` |
| `long_press` | `mobile_long_press_on_screen_at_coordinates` |
| `type` | `mobile_type_keys` |
| `swipe` | `mobile_swipe_on_screen` |
| `press` | `mobile_press_button` |
| `launch_app` | `mobile_launch_app` |
| `terminate_app` | `mobile_terminate_app` |
| `install_app` | `mobile_install_app` |
| `uninstall_app` | `mobile_uninstall_app` |
| `list_apps` | `mobile_list_apps` |
| `set_orientation` | `mobile_set_orientation` |
| `get_orientation` | `mobile_get_orientation` |
| `get_screen_size` | `mobile_get_screen_size` |
| `list_elements` | `mobile_list_elements_on_screen` |
| `open_url` | `mobile_open_url` |
| `screenshot` | `mobile_take_screenshot` |
| `save_screenshot` | `mobile_save_screenshot` |
