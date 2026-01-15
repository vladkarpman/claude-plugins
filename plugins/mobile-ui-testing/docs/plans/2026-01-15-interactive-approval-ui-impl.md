# Interactive Approval UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a browser-based approval UI that replaces the terminal verification interview, allowing users to visually review, edit, and approve recorded test flows before generating YAML.

**Architecture:** Generate standalone HTML file with embedded JSON data during `/stop-recording`. HTML references video file in same folder. Two-panel layout with video scrubber (left) and editable step timeline (right). Claude analyzes before/after frames during generation for smart descriptions.

**Tech Stack:** HTML5, CSS (reused from report.html), vanilla JavaScript, HTML5 Video API, Python for generation script.

---

## Task 1: Create Base Approval HTML Template

**Files:**
- Create: `templates/approval.html`

**Step 1: Create HTML skeleton with CSS variables from report.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Approve Test - {{testName}}</title>
    <style>
        :root {
            --pass-color: #10b981;
            --fail-color: #ef4444;
            --skip-color: #6b7280;
            --bg-primary: #111827;
            --bg-secondary: #1f2937;
            --bg-tertiary: #374151;
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --border-color: #4b5563;
            --accent-color: #3b82f6;
            --action-tap: #f59e0b;
            --action-verify: #8b5cf6;
            --action-type: #06b6d4;
            --action-wait: #6b7280;
            --action-swipe: #ec4899;
            --warning-color: #f59e0b;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            height: 100vh;
            overflow: hidden;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
        }

        .header h1 {
            font-size: 1.25rem;
            font-weight: 500;
        }

        .header-meta {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        .header-actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            border: none;
        }

        .btn-primary {
            background: var(--accent-color);
            color: white;
        }

        .btn-primary:hover {
            background: #2563eb;
        }

        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--border-color);
        }

        .btn-danger {
            background: var(--fail-color);
            color: white;
        }

        /* Main Layout - Two Panels */
        .main {
            display: flex;
            height: calc(100vh - 65px);
        }

        .video-panel {
            width: 45%;
            padding: 24px;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }

        .steps-panel {
            width: 55%;
            overflow-y: auto;
            padding: 24px;
        }

        /* Video Player */
        .video-container {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .video-wrapper {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .video-wrapper video {
            max-width: 100%;
            max-height: 100%;
        }

        .video-controls {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .video-timeline {
            position: relative;
            height: 40px;
            background: var(--bg-secondary);
            border-radius: 4px;
            cursor: pointer;
        }

        .video-progress {
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            background: var(--accent-color);
            opacity: 0.3;
            border-radius: 4px;
        }

        .video-marker {
            position: absolute;
            top: 0;
            width: 3px;
            height: 100%;
            background: var(--action-tap);
            cursor: pointer;
        }

        .video-marker:hover {
            background: var(--warning-color);
        }

        .video-time {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .add-step-buttons {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .add-step-buttons .btn {
            flex: 1;
            font-size: 0.75rem;
            padding: 6px 12px;
        }
    </style>
</head>
<body>
    <header class="header">
        <div>
            <h1>Approve: {{testName}}</h1>
            <div class="header-meta">{{stepCount}} steps recorded</div>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" onclick="discardTest()">Discard</button>
            <button class="btn btn-primary" onclick="exportYAML()">Export YAML</button>
        </div>
    </header>

    <main class="main">
        <div class="video-panel">
            <div class="video-container">
                <div class="video-wrapper">
                    <video id="video" src="{{videoFile}}" controls></video>
                </div>
                <div class="video-controls">
                    <div class="video-timeline" id="timeline" onclick="seekToPosition(event)">
                        <div class="video-progress" id="progress"></div>
                        <!-- Step markers injected by JS -->
                    </div>
                    <div class="video-time">
                        <span id="currentTime">0:00</span>
                        <span id="duration">{{videoDuration}}</span>
                    </div>
                </div>
                <div class="add-step-buttons">
                    <button class="btn btn-secondary" onclick="addStep('verify_screen')">+ verify_screen</button>
                    <button class="btn btn-secondary" onclick="addStep('wait_for')">+ wait_for</button>
                    <button class="btn btn-secondary" onclick="addStep('wait')">+ wait</button>
                </div>
            </div>
        </div>

        <div class="steps-panel" id="stepsPanel">
            <!-- Steps rendered by JS -->
        </div>
    </main>

    <script>
        // Data embedded during generation
        const testData = {{testDataJSON}};

        // Will be populated in Task 3
    </script>
</body>
</html>
```

**Step 2: Verify file created**

Run: `ls -la templates/approval.html`
Expected: File exists with ~200 lines

**Step 3: Commit**

```bash
git add templates/approval.html
git commit -m "feat(mobile-ui-testing): add base approval HTML template"
```

---

## Task 2: Add Step Card CSS and HTML Structure

**Files:**
- Modify: `templates/approval.html`

**Step 1: Add step card CSS after existing styles**

Add before `</style>`:

```css
        /* Step Cards */
        .step-card {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid var(--border-color);
            transition: border-color 0.15s;
        }

        .step-card:hover {
            border-color: var(--text-secondary);
        }

        .step-card.active {
            border-color: var(--accent-color);
        }

        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .step-title {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .step-number {
            width: 28px;
            height: 28px;
            background: var(--bg-tertiary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .step-action {
            font-weight: 500;
        }

        .step-action.tap { color: var(--action-tap); }
        .step-action.verify { color: var(--action-verify); }
        .step-action.wait { color: var(--action-wait); }
        .step-action.type { color: var(--action-type); }

        .step-controls {
            display: flex;
            gap: 4px;
        }

        .step-controls button {
            width: 28px;
            height: 28px;
            border: none;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
        }

        .step-controls button:hover {
            background: var(--border-color);
            color: var(--text-primary);
        }

        .step-controls button.delete:hover {
            background: var(--fail-color);
            color: white;
        }

        /* Frame Display */
        .step-frames {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }

        .frame-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .frame-label {
            font-size: 0.65rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
        }

        .frame-label.before { color: var(--action-wait); }
        .frame-label.action { color: var(--action-tap); }
        .frame-label.after { color: var(--pass-color); }

        .frame-img {
            width: 80px;
            height: 170px;
            object-fit: cover;
            border-radius: 6px;
            border: 2px solid var(--border-color);
            cursor: pointer;
        }

        .frame-container.before .frame-img { border-color: var(--action-wait); }
        .frame-container.action .frame-img { border-color: var(--action-tap); }
        .frame-container.after .frame-img { border-color: var(--pass-color); }

        .frame-arrow {
            color: var(--text-secondary);
            font-size: 1.25rem;
        }

        /* Analysis Section */
        .step-analysis {
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
            font-size: 0.875rem;
        }

        .analysis-row {
            display: flex;
            margin-bottom: 6px;
        }

        .analysis-row:last-child {
            margin-bottom: 0;
        }

        .analysis-label {
            width: 60px;
            color: var(--text-secondary);
            flex-shrink: 0;
        }

        .analysis-value {
            color: var(--text-primary);
        }

        /* Suggested Verification */
        .step-suggestion {
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 12px;
        }

        .suggestion-header {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
            color: var(--action-verify);
            font-size: 0.75rem;
            font-weight: 500;
        }

        .suggestion-text {
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.8rem;
            margin-bottom: 8px;
        }

        .suggestion-actions {
            display: flex;
            gap: 8px;
        }

        .suggestion-actions button {
            padding: 4px 12px;
            font-size: 0.75rem;
        }

        /* Step Editor */
        .step-editor {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        .editor-field {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .editor-field label {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .editor-field input,
        .editor-field select {
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 6px 10px;
            color: var(--text-primary);
            font-size: 0.875rem;
        }

        .editor-field input:focus,
        .editor-field select:focus {
            outline: none;
            border-color: var(--accent-color);
        }

        .editor-field input[type="number"] {
            width: 80px;
        }

        /* Add Step Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.active {
            display: flex;
        }

        .modal {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 24px;
            width: 400px;
            max-width: 90%;
        }

        .modal h2 {
            font-size: 1.125rem;
            margin-bottom: 16px;
        }

        .modal-field {
            margin-bottom: 16px;
        }

        .modal-field label {
            display: block;
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }

        .modal-field input,
        .modal-field textarea {
            width: 100%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 10px;
            color: var(--text-primary);
            font-size: 0.875rem;
        }

        .modal-field textarea {
            height: 80px;
            resize: vertical;
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
        }
```

**Step 2: Verify CSS added**

Run: `grep -c "step-card" templates/approval.html`
Expected: Multiple matches (5+)

**Step 3: Commit**

```bash
git add templates/approval.html
git commit -m "feat(mobile-ui-testing): add step card CSS styles to approval template"
```

---

## Task 3: Add JavaScript for Step Rendering and Video Control

**Files:**
- Modify: `templates/approval.html`

**Step 1: Add JavaScript functions**

Replace the `<script>` section with:

```javascript
    <script>
        // Data embedded during generation
        const testData = {{testDataJSON}};
        let steps = [...testData.steps];
        let activeStepId = null;

        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {
            renderSteps();
            initVideo();
        });

        // Video Control
        function initVideo() {
            const video = document.getElementById('video');
            const timeline = document.getElementById('timeline');
            const progress = document.getElementById('progress');

            video.addEventListener('timeupdate', () => {
                const percent = (video.currentTime / video.duration) * 100;
                progress.style.width = percent + '%';
                document.getElementById('currentTime').textContent = formatTime(video.currentTime);
            });

            video.addEventListener('loadedmetadata', () => {
                document.getElementById('duration').textContent = formatTime(video.duration);
                renderTimelineMarkers();
            });
        }

        function formatTime(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return `${m}:${s.toString().padStart(2, '0')}`;
        }

        function seekToPosition(event) {
            const video = document.getElementById('video');
            const timeline = document.getElementById('timeline');
            const rect = timeline.getBoundingClientRect();
            const percent = (event.clientX - rect.left) / rect.width;
            video.currentTime = percent * video.duration;
        }

        function seekToStep(stepId) {
            const step = steps.find(s => s.id === stepId);
            if (step && step.timestamp !== undefined) {
                document.getElementById('video').currentTime = step.timestamp;
            }
            setActiveStep(stepId);
        }

        function renderTimelineMarkers() {
            const timeline = document.getElementById('timeline');
            const video = document.getElementById('video');

            // Remove existing markers
            timeline.querySelectorAll('.video-marker').forEach(m => m.remove());

            steps.forEach(step => {
                if (step.timestamp !== undefined && step.action !== 'verify_screen' && step.action !== 'wait_for' && step.action !== 'wait') {
                    const marker = document.createElement('div');
                    marker.className = 'video-marker';
                    marker.style.left = (step.timestamp / video.duration * 100) + '%';
                    marker.onclick = (e) => {
                        e.stopPropagation();
                        seekToStep(step.id);
                    };
                    timeline.appendChild(marker);
                }
            });
        }

        // Step Rendering
        function renderSteps() {
            const panel = document.getElementById('stepsPanel');
            panel.innerHTML = steps.map((step, index) => renderStepCard(step, index)).join('');
            renderTimelineMarkers();
        }

        function renderStepCard(step, index) {
            const actionClass = step.action.replace('_', '');
            const isActive = step.id === activeStepId;

            return `
                <div class="step-card ${isActive ? 'active' : ''}" data-id="${step.id}" onclick="seekToStep('${step.id}')">
                    <div class="step-header">
                        <div class="step-title">
                            <span class="step-number">${index + 1}</span>
                            <span class="step-action ${actionClass}">${step.action}: ${getStepTargetDisplay(step)}</span>
                        </div>
                        <div class="step-controls">
                            <button onclick="moveStep('${step.id}', -1); event.stopPropagation();" title="Move up">↑</button>
                            <button onclick="moveStep('${step.id}', 1); event.stopPropagation();" title="Move down">↓</button>
                            <button class="delete" onclick="deleteStep('${step.id}'); event.stopPropagation();" title="Delete">×</button>
                        </div>
                    </div>

                    ${step.frames ? renderFrames(step) : ''}

                    ${step.analysis ? renderAnalysis(step.analysis) : ''}

                    ${step.suggestedVerification && !step.verificationAdded ? renderSuggestion(step) : ''}

                    <div class="step-editor">
                        ${renderStepEditor(step)}
                    </div>
                </div>
            `;
        }

        function getStepTargetDisplay(step) {
            if (step.action === 'tap' || step.action === 'wait_for') {
                return step.target?.text || `(${step.target?.x}, ${step.target?.y})`;
            }
            if (step.action === 'verify_screen') {
                return `"${step.description || ''}"`;
            }
            if (step.action === 'wait') {
                return `${step.duration || 0}ms`;
            }
            return '';
        }

        function renderFrames(step) {
            if (!step.frames) return '';

            const beforeFrame = step.frames.before?.[0] || '';
            const afterFrame = step.frames.after?.[0] || '';
            const actionFrame = step.frames.before?.[step.frames.before.length - 1] || beforeFrame;

            return `
                <div class="step-frames">
                    ${beforeFrame ? `
                        <div class="frame-container before">
                            <span class="frame-label before">Before</span>
                            <img class="frame-img" src="${beforeFrame}" onclick="openModal('${beforeFrame}'); event.stopPropagation();">
                        </div>
                        <span class="frame-arrow">→</span>
                    ` : ''}
                    ${actionFrame && step.action === 'tap' ? `
                        <div class="frame-container action">
                            <span class="frame-label action">Action</span>
                            <img class="frame-img" src="${actionFrame}" onclick="openModal('${actionFrame}'); event.stopPropagation();">
                        </div>
                        <span class="frame-arrow">→</span>
                    ` : ''}
                    ${afterFrame ? `
                        <div class="frame-container after">
                            <span class="frame-label after">After</span>
                            <img class="frame-img" src="${afterFrame}" onclick="openModal('${afterFrame}'); event.stopPropagation();">
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function renderAnalysis(analysis) {
            return `
                <div class="step-analysis">
                    ${analysis.before ? `<div class="analysis-row"><span class="analysis-label">Before:</span><span class="analysis-value">${analysis.before}</span></div>` : ''}
                    ${analysis.action ? `<div class="analysis-row"><span class="analysis-label">Action:</span><span class="analysis-value">${analysis.action}</span></div>` : ''}
                    ${analysis.after ? `<div class="analysis-row"><span class="analysis-label">After:</span><span class="analysis-value">${analysis.after}</span></div>` : ''}
                </div>
            `;
        }

        function renderSuggestion(step) {
            return `
                <div class="step-suggestion">
                    <div class="suggestion-header">💡 Suggested verification</div>
                    <div class="suggestion-text">verify_screen: "${step.suggestedVerification}"</div>
                    <div class="suggestion-actions">
                        <button class="btn btn-primary" onclick="acceptSuggestion('${step.id}'); event.stopPropagation();">+ Add</button>
                        <button class="btn btn-secondary" onclick="editSuggestion('${step.id}'); event.stopPropagation();">Edit</button>
                        <button class="btn btn-secondary" onclick="skipSuggestion('${step.id}'); event.stopPropagation();">Skip</button>
                    </div>
                </div>
            `;
        }

        function renderStepEditor(step) {
            if (step.action === 'tap') {
                return `
                    <div class="editor-field">
                        <label>Target:</label>
                        <input type="text" value="${step.target?.text || ''}" onchange="updateStepTarget('${step.id}', this.value); event.stopPropagation();" placeholder="Element text">
                    </div>
                    <div class="editor-field">
                        <label>Wait after:</label>
                        <input type="number" value="${step.waitAfter || 0}" onchange="updateStepWait('${step.id}', this.value); event.stopPropagation();" min="0" step="100"> ms
                    </div>
                `;
            }
            if (step.action === 'verify_screen') {
                return `
                    <div class="editor-field" style="flex: 1;">
                        <label>Description:</label>
                        <input type="text" value="${step.description || ''}" onchange="updateStepDescription('${step.id}', this.value); event.stopPropagation();" style="width: 300px;">
                    </div>
                `;
            }
            if (step.action === 'wait_for') {
                return `
                    <div class="editor-field">
                        <label>Element:</label>
                        <input type="text" value="${step.target?.text || ''}" onchange="updateStepTarget('${step.id}', this.value); event.stopPropagation();">
                    </div>
                    <div class="editor-field">
                        <label>Timeout:</label>
                        <input type="number" value="${step.timeout || 10}" onchange="updateStepTimeout('${step.id}', this.value); event.stopPropagation();" min="1" max="60"> s
                    </div>
                `;
            }
            if (step.action === 'wait') {
                return `
                    <div class="editor-field">
                        <label>Duration:</label>
                        <input type="number" value="${step.duration || 1000}" onchange="updateStepDuration('${step.id}', this.value); event.stopPropagation();" min="100" step="100"> ms
                    </div>
                `;
            }
            return '';
        }

        function setActiveStep(stepId) {
            activeStepId = stepId;
            document.querySelectorAll('.step-card').forEach(card => {
                card.classList.toggle('active', card.dataset.id === stepId);
            });
        }

        // Step Editing Functions
        function moveStep(stepId, direction) {
            const index = steps.findIndex(s => s.id === stepId);
            const newIndex = index + direction;
            if (newIndex < 0 || newIndex >= steps.length) return;

            [steps[index], steps[newIndex]] = [steps[newIndex], steps[index]];
            renderSteps();
        }

        function deleteStep(stepId) {
            if (!confirm('Delete this step?')) return;
            steps = steps.filter(s => s.id !== stepId);
            renderSteps();
        }

        function updateStepTarget(stepId, value) {
            const step = steps.find(s => s.id === stepId);
            if (step) {
                if (!step.target) step.target = {};
                step.target.text = value;
            }
        }

        function updateStepWait(stepId, value) {
            const step = steps.find(s => s.id === stepId);
            if (step) step.waitAfter = parseInt(value) || 0;
        }

        function updateStepDescription(stepId, value) {
            const step = steps.find(s => s.id === stepId);
            if (step) step.description = value;
        }

        function updateStepTimeout(stepId, value) {
            const step = steps.find(s => s.id === stepId);
            if (step) step.timeout = parseInt(value) || 10;
        }

        function updateStepDuration(stepId, value) {
            const step = steps.find(s => s.id === stepId);
            if (step) step.duration = parseInt(value) || 1000;
        }

        // Suggestion Functions
        function acceptSuggestion(stepId) {
            const stepIndex = steps.findIndex(s => s.id === stepId);
            const step = steps[stepIndex];
            if (!step || !step.suggestedVerification) return;

            const newStep = {
                id: 'verify_' + Date.now(),
                action: 'verify_screen',
                description: step.suggestedVerification,
                timestamp: step.timestamp
            };

            steps.splice(stepIndex + 1, 0, newStep);
            step.verificationAdded = true;
            renderSteps();
        }

        function editSuggestion(stepId) {
            const step = steps.find(s => s.id === stepId);
            if (!step) return;

            const newDesc = prompt('Edit verification:', step.suggestedVerification);
            if (newDesc !== null) {
                step.suggestedVerification = newDesc;
                acceptSuggestion(stepId);
            }
        }

        function skipSuggestion(stepId) {
            const step = steps.find(s => s.id === stepId);
            if (step) {
                step.verificationAdded = true;
                renderSteps();
            }
        }

        // Add Step Functions
        function addStep(type) {
            const video = document.getElementById('video');
            const timestamp = video.currentTime;

            let newStep;
            if (type === 'verify_screen') {
                const desc = prompt('What should the screen show?');
                if (!desc) return;
                newStep = { id: 'verify_' + Date.now(), action: 'verify_screen', description: desc, timestamp };
            } else if (type === 'wait_for') {
                const element = prompt('What element to wait for?');
                if (!element) return;
                newStep = { id: 'wait_for_' + Date.now(), action: 'wait_for', target: { text: element }, timeout: 10, timestamp };
            } else if (type === 'wait') {
                const duration = prompt('Wait duration in milliseconds:', '1000');
                if (!duration) return;
                newStep = { id: 'wait_' + Date.now(), action: 'wait', duration: parseInt(duration), timestamp };
            }

            // Insert at correct position based on timestamp
            const insertIndex = steps.findIndex(s => s.timestamp > timestamp);
            if (insertIndex === -1) {
                steps.push(newStep);
            } else {
                steps.splice(insertIndex, 0, newStep);
            }
            renderSteps();
        }

        // Export Functions
        function exportYAML() {
            const yaml = generateYAML();
            downloadFile(testData.testName + '.yaml', yaml);
        }

        function generateYAML() {
            let yaml = `config:\n  app: ${testData.appPackage}\n\ntests:\n  - name: ${testData.testName}\n    steps:\n`;

            for (const step of steps) {
                yaml += stepToYAML(step);
            }

            return yaml;
        }

        function stepToYAML(step) {
            let yaml = '';

            if (step.action === 'tap') {
                const target = step.target?.text || `[${step.target?.x}, ${step.target?.y}]`;
                yaml = `      - tap: "${target}"\n`;
                if (step.waitAfter > 0) {
                    yaml += `      - wait: ${step.waitAfter}ms\n`;
                }
            } else if (step.action === 'verify_screen') {
                yaml = `      - verify_screen: "${step.description}"\n`;
            } else if (step.action === 'wait_for') {
                yaml = `      - wait_for: "${step.target?.text}"\n`;
            } else if (step.action === 'wait') {
                yaml = `      - wait: ${step.duration}ms\n`;
            }

            return yaml;
        }

        function downloadFile(filename, content) {
            const blob = new Blob([content], { type: 'text/yaml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function discardTest() {
            if (confirm('Discard this test recording? This cannot be undone.')) {
                window.close();
            }
        }

        // Image Modal (simple version)
        function openModal(src) {
            const img = new Image();
            img.src = src;
            img.style.cssText = 'max-width: 90vw; max-height: 90vh; border-radius: 8px;';

            const overlay = document.createElement('div');
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center; z-index: 9999; cursor: pointer;';
            overlay.appendChild(img);
            overlay.onclick = () => overlay.remove();
            document.body.appendChild(overlay);
        }
    </script>
```

**Step 2: Verify JavaScript added**

Run: `grep -c "function renderSteps" templates/approval.html`
Expected: 1

**Step 3: Commit**

```bash
git add templates/approval.html
git commit -m "feat(mobile-ui-testing): add JavaScript for step rendering and editing"
```

---

## Task 4: Create Python Generation Script

**Files:**
- Create: `scripts/generate-approval.py`

**Step 1: Create the generation script**

```python
#!/usr/bin/env python3
"""
Generate approval HTML from recording data.

Usage:
    python3 generate-approval.py <recording_folder> [--output <html_path>]

Examples:
    python3 generate-approval.py tests/mytest/recording
    python3 generate-approval.py tests/mytest/recording --output tests/mytest/approval.html
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_template_path() -> Path:
    """Get path to HTML template."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        return Path(plugin_root) / "templates" / "approval.html"
    return Path(__file__).parent.parent / "templates" / "approval.html"


def load_template() -> str:
    """Load HTML template file."""
    template_path = get_template_path()
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def load_touch_events(recording_folder: Path) -> List[Dict[str, Any]]:
    """Load touch events from recording."""
    touch_file = recording_folder / "touch_events.json"
    if not touch_file.exists():
        return []
    with open(touch_file) as f:
        data = json.load(f)
    return data.get("events", data) if isinstance(data, dict) else data


def load_analysis(recording_folder: Path) -> Dict[str, Any]:
    """Load Claude's analysis if it exists."""
    analysis_file = recording_folder / "analysis.json"
    if not analysis_file.exists():
        return {}
    with open(analysis_file) as f:
        return json.load(f)


def find_screenshots(recording_folder: Path) -> Dict[str, List[str]]:
    """Find screenshot files organized by step."""
    screenshots_dir = recording_folder / "screenshots"
    if not screenshots_dir.exists():
        return {}

    screenshots = {}
    for f in sorted(screenshots_dir.iterdir()):
        if not f.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            continue

        # Parse filename: step_001_before_1.png
        match = re.match(r'step_(\d+)_(before|after)_(\d+)', f.name)
        if match:
            step_num = match.group(1)
            frame_type = match.group(2)

            if step_num not in screenshots:
                screenshots[step_num] = {'before': [], 'after': []}

            # Use relative path from approval.html location
            rel_path = f"recording/screenshots/{f.name}"
            screenshots[step_num][frame_type].append(rel_path)

    return screenshots


def build_steps(touch_events: List, screenshots: Dict, analysis: Dict) -> List[Dict]:
    """Build step objects from touch events."""
    steps = []

    for i, event in enumerate(touch_events):
        step_num = f"{i+1:03d}"
        step_id = f"step_{step_num}"

        step = {
            "id": step_id,
            "timestamp": event.get("timestamp", 0),
            "action": "tap",
            "target": {
                "x": event.get("x"),
                "y": event.get("y"),
                "text": event.get("element_text", "")
            },
            "waitAfter": 0
        }

        # Add screenshots if available
        if step_num in screenshots:
            step["frames"] = screenshots[step_num]

        # Add analysis if available
        step_analysis = analysis.get(step_id, {})
        if step_analysis:
            step["analysis"] = step_analysis.get("analysis", {})
            step["suggestedVerification"] = step_analysis.get("suggestedVerification", "")

        steps.append(step)

    return steps


def generate_html(template: str, data: Dict[str, Any]) -> str:
    """Generate HTML from template and data."""
    # Simple placeholder replacement
    html = template
    html = html.replace("{{testName}}", data.get("testName", "test"))
    html = html.replace("{{stepCount}}", str(len(data.get("steps", []))))
    html = html.replace("{{videoFile}}", data.get("videoFile", "recording.mp4"))
    html = html.replace("{{videoDuration}}", data.get("videoDuration", "0:00"))
    html = html.replace("{{testDataJSON}}", json.dumps(data, indent=2))

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate approval HTML from recording")
    parser.add_argument("recording_folder", help="Path to recording folder")
    parser.add_argument("--output", "-o", help="Output HTML path")
    parser.add_argument("--test-name", help="Test name (default: folder name)")
    parser.add_argument("--app-package", help="App package name")
    args = parser.parse_args()

    recording_folder = Path(args.recording_folder)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = recording_folder.parent / "approval.html"

    # Determine test name
    test_name = args.test_name or recording_folder.parent.name

    try:
        # Load data
        template = load_template()
        touch_events = load_touch_events(recording_folder)
        screenshots = find_screenshots(recording_folder)
        analysis = load_analysis(recording_folder)

        # Build test data
        data = {
            "testName": test_name,
            "appPackage": args.app_package or "com.example.app",
            "videoFile": "recording/recording.mp4",
            "videoDuration": "0:30",
            "steps": build_steps(touch_events, screenshots, analysis)
        }

        # Generate HTML
        html = generate_html(template, data)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)

        print(f"Approval UI generated: {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

Run: `chmod +x scripts/generate-approval.py`

**Step 3: Verify script**

Run: `python3 scripts/generate-approval.py --help`
Expected: Shows usage help

**Step 4: Commit**

```bash
git add scripts/generate-approval.py
git commit -m "feat(mobile-ui-testing): add approval HTML generation script"
```

---

## Task 5: Update stop-recording.md to Use Approval UI

**Files:**
- Modify: `commands/stop-recording.md`

**Step 1: Read current stop-recording.md structure**

Run: `head -50 commands/stop-recording.md`

Review current steps to understand where to integrate approval UI generation.

**Step 2: Replace verification interview section**

After Step 8 (frame extraction), replace the typing interview and checkpoint interview sections (Steps 8.4 and 8.5) with approval UI generation:

Find the section starting with `#### Step 8.4: Typing Interview` and replace everything up to `### Step 9: Generate YAML` with:

```markdown
#### Step 8.4: Analyze Steps (Before/After Diff)

For each touch event, analyze the before and after frames to provide smart descriptions.

**For each step {N}:**

1. **View before frame:**
   **Tool:** `Read` file `{TEST_FOLDER}/recording/screenshots/step_{N:03d}_before_3.png`

2. **View after frame:**
   **Tool:** `Read` file `{TEST_FOLDER}/recording/screenshots/step_{N:03d}_after_3.png`

3. **Analyze and describe:**
   - Before: Describe the screen state before the tap
   - Action: Identify what element was tapped
   - After: Describe what changed after the tap
   - Suggested verification: Propose a verify_screen based on the change

4. **Store analysis** in memory for approval generation

**Example analysis output:**
```json
{
  "step_001": {
    "analysis": {
      "before": "Calculator app with empty display",
      "action": "Tapped '5' button on number pad",
      "after": "Display now shows '5'"
    },
    "suggestedVerification": "Display shows 5"
  }
}
```

#### Step 8.5: Generate Approval UI

**Tool:** `Write` to `{TEST_FOLDER}/recording/analysis.json`

Write the analysis data collected in Step 8.4.

**Tool:** `Bash`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate-approval.py" \
    "{TEST_FOLDER}/recording" \
    --test-name "{TEST_NAME}" \
    --app-package "{APP_PACKAGE}" \
    --output "{TEST_FOLDER}/approval.html"
```

#### Step 8.6: Open Approval UI

**Tool:** `Bash`
```bash
open "{TEST_FOLDER}/approval.html"
```

**Display to user:**
```
✓ Approval UI opened in browser

Review your recorded test:
1. Check each step's before/after frames
2. Accept or skip suggested verifications
3. Edit tap targets or add wait times if needed
4. Add new steps using video scrubber
5. Click "Export YAML" when done

The YAML file will be downloaded to your Downloads folder.
Move it to: {TEST_FOLDER}/test.yaml
```

### Step 9: Update Recording State

**Tool:** `Write` to `.claude/recording-state.json`

```json
{
  "status": "approval_pending",
  "testName": "{TEST_NAME}",
  "testFolder": "{TEST_FOLDER}",
  "approvalFile": "{TEST_FOLDER}/approval.html"
}
```

**Recording complete.** User will use browser UI to finalize and export YAML.
```

**Step 3: Remove old YAML generation step**

The old Step 9 (Generate YAML) is no longer needed since the browser UI handles export. Remove or comment out the old YAML generation logic.

**Step 4: Commit**

```bash
git add commands/stop-recording.md
git commit -m "feat(mobile-ui-testing): replace verification interview with approval UI"
```

---

## Task 6: Test End-to-End Flow

**Files:**
- None (testing only)

**Step 1: Create test recording folder structure**

```bash
mkdir -p tests/approval-test/recording/screenshots
```

**Step 2: Create mock touch_events.json**

```bash
cat > tests/approval-test/recording/touch_events.json << 'EOF'
[
  {"timestamp": 2.5, "x": 406, "y": 1645, "element_text": "5"},
  {"timestamp": 4.1, "x": 940, "y": 1905, "element_text": "+"},
  {"timestamp": 5.8, "x": 673, "y": 1905, "element_text": "3"},
  {"timestamp": 7.2, "x": 940, "y": 2165, "element_text": "="}
]
EOF
```

**Step 3: Create mock analysis.json**

```bash
cat > tests/approval-test/recording/analysis.json << 'EOF'
{
  "step_001": {
    "analysis": {
      "before": "Calculator with empty display",
      "action": "Tapped '5' button",
      "after": "Display shows 5"
    },
    "suggestedVerification": "Display shows 5"
  },
  "step_002": {
    "analysis": {
      "before": "Display shows 5",
      "action": "Tapped '+' button",
      "after": "Display shows 5+"
    },
    "suggestedVerification": "Display shows 5+"
  }
}
EOF
```

**Step 4: Generate approval HTML**

```bash
python3 scripts/generate-approval.py tests/approval-test/recording \
    --test-name "calculator-test" \
    --app-package "com.google.android.calculator"
```

Expected: `Approval UI generated: tests/approval-test/approval.html`

**Step 5: Open and verify UI**

```bash
open tests/approval-test/approval.html
```

**Verify:**
- [ ] Two-panel layout displays correctly
- [ ] Steps show in right panel
- [ ] Video panel shows (will be empty without video file)
- [ ] Step cards render with analysis
- [ ] Suggested verifications appear
- [ ] Export YAML button works
- [ ] Delete/reorder buttons work

**Step 6: Clean up test files**

```bash
rm -rf tests/approval-test
```

**Step 7: Commit any fixes**

```bash
git add -A
git commit -m "fix(mobile-ui-testing): approval UI fixes from testing"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add approval UI section to CLAUDE.md**

Add after the "Recording Pipeline" section:

```markdown
## Approval UI

After recording, an interactive browser-based approval UI opens instead of terminal Q&A.

**Flow:**
1. `/stop-recording` extracts frames and analyzes each step
2. `approval.html` generated with embedded data
3. Browser opens automatically
4. User reviews Before → Action → After for each step
5. User accepts/edits suggested verifications
6. User clicks "Export YAML" to download test file

**Features:**
- Video scrubber with step markers
- Before/Action/After frame display per step
- Claude-generated analysis (what changed)
- One-click verification suggestions
- Reorder, delete, edit steps
- Add new steps at any video timestamp
- YAML export via download

**Files:**
- `templates/approval.html` - Interactive approval UI template
- `scripts/generate-approval.py` - Generates HTML from recording data
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mobile-ui-testing): add approval UI documentation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Base HTML template with layout | `templates/approval.html` |
| 2 | Step card CSS styles | `templates/approval.html` |
| 3 | JavaScript for rendering/editing | `templates/approval.html` |
| 4 | Python generation script | `scripts/generate-approval.py` |
| 5 | Update stop-recording command | `commands/stop-recording.md` |
| 6 | End-to-end testing | (none) |
| 7 | Documentation | `CLAUDE.md` |

**Total estimated steps:** ~25 discrete actions across 7 tasks.
