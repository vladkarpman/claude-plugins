# Preconditions Reference

Preconditions define the required state before a test runs. The test runner automatically sets up the necessary state, making tests autonomous and reproducible.

## Philosophy

**Autonomous Tests:**
```yaml
tests:
  - name: View profile page
    preconditions:
      - user_logged_in
    steps:
      - tap: "Profile"
      - verify_screen: "Profile page with user info"
```

The test runner ensures the user is logged in before running. No manual setup required.

**Manual Setup (Old Way):**
```yaml
tests:
  - name: View profile page
    # Assumes user is already logged in manually
    steps:
      - tap: "Profile"
      - verify_screen: "Profile page with user info"
```

This approach is fragile - tests fail if setup state is wrong.

## Basic Syntax

### Simple Preconditions

```yaml
tests:
  - name: Test name
    preconditions:
      - user_logged_in           # User must be authenticated
      - onboarding_completed     # Onboarding must be finished
      - network: connected       # Network must be available
    steps:
      - tap: "Button"
```

### Explicit Preconditions

```yaml
tests:
  - name: Test name
    preconditions:
      - user_logged_in:
          account: premium_user  # Use specific test account
      - min_photos: 5            # Need at least 5 photos in gallery
      - device_storage:
          min_free_mb: 100       # Need 100MB free space
    steps:
      - tap: "Upload"
```

## Built-in Preconditions

### user_logged_in

Ensures a user is logged in before test runs.

**Simple form:**
```yaml
preconditions:
  - user_logged_in
```

Uses default test account from config.

**Explicit form:**
```yaml
preconditions:
  - user_logged_in:
      account: premium_user
```

Uses specific account defined in test config:

```yaml
config:
  app: com.myapp
  test_accounts:
    default:
      email: test@example.com
      password: test123
    premium_user:
      email: premium@example.com
      password: premium123
```

**How it works:**
1. Check if user is already logged in (via screen analysis)
2. If not, launch app and perform login flow
3. Cache login state to avoid redundant logins

### user_state

Requires user to be in a specific state.

```yaml
preconditions:
  - user_state: logged_out
```

**Supported states:**
- `logged_in` - User authenticated
- `logged_out` - User not authenticated
- `onboarding_pending` - Onboarding not completed

### min_photos

Requires minimum number of photos in app's photo library.

```yaml
preconditions:
  - min_photos: 3
```

**How it works:**
1. Navigate to photo gallery
2. Count available photos
3. If count < minimum, upload placeholder photos from test assets

**Configuration:**
```yaml
config:
  test_data:
    photo_dir: ./test-assets/photos  # Directory with test photos
```

### onboarding_completed

Ensures onboarding flow is completed.

```yaml
preconditions:
  - onboarding_completed
```

**How it works:**
1. Check if onboarding screen is visible
2. If yes, click through onboarding screens to completion
3. Cache completion state

### network

Controls network connectivity state.

```yaml
preconditions:
  - network: connected    # Require internet
  - network: disconnected # Require no internet
  - network: wifi         # Require WiFi connection
```

**How it works:**
- Uses device API to enable/disable network
- Verifies connectivity state before proceeding

### device_storage

Requires minimum free storage space.

```yaml
preconditions:
  - device_storage:
      min_free_mb: 100
```

**How it works:**
1. Check available storage via device API
2. If insufficient, clear app cache/data to free space
3. Fail test if still insufficient after cleanup

## Configuration

Define test accounts and data in `config` section:

```yaml
config:
  app: com.myapp

  test_accounts:
    default:
      email: test@example.com
      password: test123
    premium_user:
      email: premium@example.com
      password: premium123
    admin:
      email: admin@example.com
      password: admin123

  test_data:
    photo_dir: ./test-assets/photos
    video_dir: ./test-assets/videos

  env:
    api_base_url: https://staging.api.example.com
    feature_flags:
      new_ui: true
```

## Failure Handling

Control what happens when precondition setup fails:

```yaml
preconditions:
  - user_logged_in:
      on_failure: skip  # Skip test if login fails

  - min_photos: 5
      on_failure: fail  # Fail test if can't prepare photos

  - network: connected
      on_failure: warn  # Continue with warning if network unavailable
```

**Options:**
- `fail` (default) - Fail the test immediately
- `skip` - Skip test and mark as skipped
- `warn` - Log warning but continue test execution

## Execution Flow

```
Test Start
    ↓
Check Preconditions
    ↓
┌─────────────────────┐
│ user_logged_in      │
│  ├─ Check state     │
│  ├─ Login if needed │
│  └─ Verify success  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ min_photos: 3       │
│  ├─ Count photos    │
│  ├─ Upload if < 3   │
│  └─ Verify count    │
└─────────────────────┘
    ↓
All Preconditions Met
    ↓
Run Test Steps
```

## Advanced Examples

### Multiple Test Accounts

```yaml
config:
  app: com.chat.app
  test_accounts:
    user_a:
      email: alice@example.com
      password: alice123
    user_b:
      email: bob@example.com
      password: bob123

tests:
  - name: Send message between users
    preconditions:
      - user_logged_in:
          account: user_a
    steps:
      - tap: "Contacts"
      - tap: "Bob"
      - type: "Hello Bob!"
      - tap: "Send"

  - name: Receive message
    preconditions:
      - user_logged_in:
          account: user_b
    steps:
      - verify_screen: "New message from Alice"
```

### Conditional Preconditions

```yaml
tests:
  - name: Upload photo (online only)
    preconditions:
      - user_logged_in
      - network: connected
      - min_photos: 1
    steps:
      - tap: "Upload"
      - tap: "Select Photo"
      - verify_screen: "Upload successful"

  - name: View cached photos (offline)
    preconditions:
      - user_logged_in
      - network: disconnected
      - min_photos: 3
    steps:
      - tap: "Gallery"
      - verify_screen: "3 photos visible"
```

### Data Preparation

```yaml
config:
  test_data:
    photo_dir: ./test-assets/photos
    profiles:
      complete:
        name: "John Doe"
        bio: "Test user"
        avatar: profile.jpg

tests:
  - name: Edit profile with photo
    preconditions:
      - user_logged_in
      - min_photos: 1
      - user_profile: complete
    steps:
      - tap: "Edit Profile"
      - verify_screen: "Profile form with photo"
```

## Best Practices

### DO:

✅ **Use preconditions for test independence**
```yaml
tests:
  - name: Each test sets its own preconditions
    preconditions:
      - user_logged_in
      - min_photos: 3
```

✅ **Define reusable test accounts**
```yaml
config:
  test_accounts:
    default: { email: test@example.com, password: test123 }
    premium: { email: premium@example.com, password: premium123 }
```

✅ **Use specific preconditions**
```yaml
preconditions:
  - user_logged_in:
      account: premium_user
  - min_photos: 5
```

✅ **Handle failures appropriately**
```yaml
preconditions:
  - network: connected
    on_failure: skip  # Skip test if no network
```

### DON'T:

❌ **Don't rely on manual setup**
```yaml
# BAD: Assumes user is already logged in
tests:
  - name: View profile
    steps:
      - tap: "Profile"
```

❌ **Don't duplicate setup in every test**
```yaml
# BAD: Login steps repeated in each test
tests:
  - name: Test 1
    steps:
      - tap: "Login"
      - type: "test@example.com"
      - tap: "Submit"
      - tap: "Feature 1"

  - name: Test 2
    steps:
      - tap: "Login"
      - type: "test@example.com"
      - tap: "Submit"
      - tap: "Feature 2"
```

Use preconditions instead:
```yaml
# GOOD: Precondition handles login
tests:
  - name: Test 1
    preconditions:
      - user_logged_in
    steps:
      - tap: "Feature 1"

  - name: Test 2
    preconditions:
      - user_logged_in
    steps:
      - tap: "Feature 2"
```

❌ **Don't use preconditions for test steps**
```yaml
# BAD: This is a test action, not a precondition
preconditions:
  - navigate_to_settings
```

Preconditions set up state, not perform test actions.

❌ **Don't hardcode credentials in steps**
```yaml
# BAD: Credentials in test steps
steps:
  - tap: "Email"
  - type: "test@example.com"
  - tap: "Password"
  - type: "test123"
```

Use preconditions:
```yaml
# GOOD: Credentials in config
config:
  test_accounts:
    default:
      email: test@example.com
      password: test123

tests:
  - name: Test
    preconditions:
      - user_logged_in
```

## Implementation Status

### Phase 1: Core Preconditions (Planned)

- `user_logged_in` - Basic login support
- `user_state` - Login state control
- `onboarding_completed` - Onboarding flow completion

### Phase 2: Data Preconditions (Planned)

- `min_photos` - Photo gallery preparation
- `min_contacts` - Contact list preparation
- `device_storage` - Storage management

### Phase 3: Environment Preconditions (Planned)

- `network` - Network state control
- `location` - GPS/location mocking
- `permissions` - App permission grants

**Current Status:** Design complete, implementation not yet started.

See `docs/verification-interview-design.md` for full implementation plan.
