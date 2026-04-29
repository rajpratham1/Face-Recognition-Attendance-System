/**
 * Liveness Detection Module
 * Prevents photo/video spoofing attacks using multiple detection techniques
 * 
 * Techniques Used:
 * 1. Blink Detection - Detects eye blinks
 * 2. Head Movement - Detects head pose changes
 * 3. Texture Analysis - Detects screen/photo artifacts
 * 4. Face Quality - Ensures good lighting and clarity
 */

class LivenessDetector {
    constructor(options = {}) {
        this.options = {
            requireBlink: options.requireBlink !== false,
            requireHeadMovement: options.requireHeadMovement !== false,
            blinkThreshold: options.blinkThreshold || 0.25,
            movementThreshold: options.movementThreshold || 15,
            qualityThreshold: options.qualityThreshold || 0.6,
            timeoutSeconds: options.timeoutSeconds || 15,
            ...options
        };

        this.state = {
            blinkDetected: false,
            headMovementDetected: false,
            qualityPassed: false,
            startTime: null,
            previousLandmarks: null,
            blinkCount: 0,
            eyeAspectRatios: [],
            headPoses: []
        };

        this.callbacks = {
            onProgress: options.onProgress || (() => {}),
            onSuccess: options.onSuccess || (() => {}),
            onFailure: options.onFailure || (() => {}),
            onTimeout: options.onTimeout || (() => {})
        };
    }

    /**
     * Start liveness detection process
     */
    start() {
        this.reset();
        this.state.startTime = Date.now();
        this._startTimeoutTimer();
        this.callbacks.onProgress({
            message: 'Look at the camera and blink naturally',
            progress: 0
        });
    }

    /**
     * Reset detection state
     */
    reset() {
        this.state = {
            blinkDetected: false,
            headMovementDetected: false,
            qualityPassed: false,
            startTime: null,
            previousLandmarks: null,
            blinkCount: 0,
            eyeAspectRatios: [],
            headPoses: []
        };
    }

    /**
     * Process a single frame for liveness detection
     * @param {Array} detections - face-api.js detection results
     * @param {HTMLVideoElement} video - Video element
     * @returns {Object} Detection results
     */
    async processFrame(detections, video) {
        if (!detections || detections.length === 0) {
            return {
                passed: false,
                reason: 'No face detected',
                instruction: 'Position your face in the frame'
            };
        }

        if (detections.length > 1) {
            return {
                passed: false,
                reason: 'Multiple faces detected',
                instruction: 'Ensure only one person is visible'
            };
        }

        const detection = detections[0];
        const landmarks = detection.landmarks;
        const descriptor = detection.descriptor;

        // Check timeout
        if (this._isTimeout()) {
            this.callbacks.onTimeout();
            return {
                passed: false,
                reason: 'Timeout',
                instruction: 'Liveness check timed out. Please try again.'
            };
        }

        // 1. Face Quality Check
        const qualityResult = this._checkFaceQuality(detection, video);
        if (!qualityResult.passed) {
            return qualityResult;
        }
        this.state.qualityPassed = true;

        // 2. Blink Detection
        if (this.options.requireBlink && !this.state.blinkDetected) {
            const blinkResult = this._detectBlink(landmarks);
            if (blinkResult.blinked) {
                this.state.blinkDetected = true;
                this.state.blinkCount++;
                this.callbacks.onProgress({
                    message: '✓ Blink detected! Now move your head slightly',
                    progress: 50
                });
            }
        }

        // 3. Head Movement Detection
        if (this.options.requireHeadMovement && !this.state.headMovementDetected) {
            const movementResult = this._detectHeadMovement(landmarks);
            if (movementResult.moved) {
                this.state.headMovementDetected = true;
                this.callbacks.onProgress({
                    message: '✓ Movement detected! Hold still...',
                    progress: 75
                });
            }
        }

        // 4. Texture Analysis (anti-spoofing)
        const textureResult = await this._analyzeTexture(video, detection.detection.box);
        if (!textureResult.passed) {
            return textureResult;
        }

        // Check if all checks passed
        const allPassed = this._allChecksPassed();
        if (allPassed) {
            this.callbacks.onSuccess({
                descriptor: Array.from(descriptor),
                blinkCount: this.state.blinkCount,
                timeElapsed: Date.now() - this.state.startTime
            });
            return {
                passed: true,
                reason: 'Liveness verified',
                instruction: 'Verification successful!',
                descriptor: Array.from(descriptor)
            };
        }

        // Return current progress
        return {
            passed: false,
            reason: 'In progress',
            instruction: this._getCurrentInstruction(),
            progress: this._getProgress()
        };
    }

    /**
     * Check face quality (lighting, clarity, size)
     */
    _checkFaceQuality(detection, video) {
        const box = detection.detection.box;
        const score = detection.detection.score;

        // Check detection confidence
        if (score < this.options.qualityThreshold) {
            return {
                passed: false,
                reason: 'Poor face quality',
                instruction: 'Move to better lighting'
            };
        }

        // Check face size (should be at least 20% of frame)
        const faceArea = box.width * box.height;
        const frameArea = video.videoWidth * video.videoHeight;
        const faceRatio = faceArea / frameArea;

        if (faceRatio < 0.08) {
            return {
                passed: false,
                reason: 'Face too small',
                instruction: 'Move closer to the camera'
            };
        }

        if (faceRatio > 0.6) {
            return {
                passed: false,
                reason: 'Face too large',
                instruction: 'Move back from the camera'
            };
        }

        // Check if face is centered
        const faceCenterX = box.x + box.width / 2;
        const faceCenterY = box.y + box.height / 2;
        const frameCenterX = video.videoWidth / 2;
        const frameCenterY = video.videoHeight / 2;

        const offsetX = Math.abs(faceCenterX - frameCenterX);
        const offsetY = Math.abs(faceCenterY - frameCenterY);

        if (offsetX > video.videoWidth * 0.3 || offsetY > video.videoHeight * 0.3) {
            return {
                passed: false,
                reason: 'Face not centered',
                instruction: 'Center your face in the frame'
            };
        }

        return { passed: true };
    }

    /**
     * Detect eye blinks using Eye Aspect Ratio (EAR)
     */
    _detectBlink(landmarks) {
        const leftEye = this._getEyeLandmarks(landmarks, 'left');
        const rightEye = this._getEyeLandmarks(landmarks, 'right');

        const leftEAR = this._calculateEAR(leftEye);
        const rightEAR = this._calculateEAR(rightEye);
        const avgEAR = (leftEAR + rightEAR) / 2;

        this.state.eyeAspectRatios.push(avgEAR);

        // Keep only last 10 frames
        if (this.state.eyeAspectRatios.length > 10) {
            this.state.eyeAspectRatios.shift();
        }

        // Detect blink: EAR drops below threshold then rises back
        if (this.state.eyeAspectRatios.length >= 3) {
            const recent = this.state.eyeAspectRatios.slice(-3);
            const wasClosed = recent[1] < this.options.blinkThreshold;
            const wasOpen = recent[0] > this.options.blinkThreshold && recent[2] > this.options.blinkThreshold;

            if (wasClosed && wasOpen) {
                return { blinked: true, ear: avgEAR };
            }
        }

        return { blinked: false, ear: avgEAR };
    }

    /**
     * Get eye landmarks from face landmarks
     */
    _getEyeLandmarks(landmarks, eye) {
        const positions = landmarks.positions;
        if (eye === 'left') {
            // Left eye landmarks (indices 36-41)
            return positions.slice(36, 42);
        } else {
            // Right eye landmarks (indices 42-47)
            return positions.slice(42, 48);
        }
    }

    /**
     * Calculate Eye Aspect Ratio (EAR)
     */
    _calculateEAR(eyeLandmarks) {
        if (eyeLandmarks.length < 6) return 0;

        // Vertical distances
        const v1 = this._euclideanDistance(eyeLandmarks[1], eyeLandmarks[5]);
        const v2 = this._euclideanDistance(eyeLandmarks[2], eyeLandmarks[4]);

        // Horizontal distance
        const h = this._euclideanDistance(eyeLandmarks[0], eyeLandmarks[3]);

        // EAR formula
        const ear = (v1 + v2) / (2.0 * h);
        return ear;
    }

    /**
     * Detect head movement by tracking nose position
     */
    _detectHeadMovement(landmarks) {
        const nose = landmarks.getNose()[0]; // Nose tip
        const currentPose = { x: nose.x, y: nose.y };

        this.state.headPoses.push(currentPose);

        // Keep only last 30 frames (about 1 second at 30fps)
        if (this.state.headPoses.length > 30) {
            this.state.headPoses.shift();
        }

        if (this.state.headPoses.length < 10) {
            return { moved: false };
        }

        // Calculate movement range
        const xPositions = this.state.headPoses.map(p => p.x);
        const yPositions = this.state.headPoses.map(p => p.y);

        const xRange = Math.max(...xPositions) - Math.min(...xPositions);
        const yRange = Math.max(...yPositions) - Math.min(...yPositions);

        const totalMovement = Math.sqrt(xRange * xRange + yRange * yRange);

        if (totalMovement > this.options.movementThreshold) {
            return { moved: true, movement: totalMovement };
        }

        return { moved: false, movement: totalMovement };
    }

    /**
     * Analyze texture to detect screen/photo artifacts
     */
    async _analyzeTexture(video, faceBox) {
        try {
            // Create canvas to extract face region
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = faceBox.width;
            canvas.height = faceBox.height;
            
            ctx.drawImage(
                video,
                faceBox.x, faceBox.y, faceBox.width, faceBox.height,
                0, 0, faceBox.width, faceBox.height
            );

            // Get image data
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            // Calculate texture variance (simple anti-spoofing)
            let variance = 0;
            let mean = 0;
            const sampleSize = Math.min(1000, data.length / 4);

            // Calculate mean
            for (let i = 0; i < sampleSize; i++) {
                const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
                const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                mean += gray;
            }
            mean /= sampleSize;

            // Calculate variance
            for (let i = 0; i < sampleSize; i++) {
                const idx = Math.floor(Math.random() * (data.length / 4)) * 4;
                const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                variance += Math.pow(gray - mean, 2);
            }
            variance /= sampleSize;

            // Low variance indicates flat image (possible photo/screen)
            if (variance < 100) {
                return {
                    passed: false,
                    reason: 'Possible spoofing detected',
                    instruction: 'Please use live camera, not a photo'
                };
            }

            return { passed: true, variance };
        } catch (error) {
            console.warn('Texture analysis failed:', error);
            return { passed: true }; // Don't block on analysis failure
        }
    }

    /**
     * Calculate Euclidean distance between two points
     */
    _euclideanDistance(p1, p2) {
        return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
    }

    /**
     * Check if all required checks have passed
     */
    _allChecksPassed() {
        const blinkPassed = !this.options.requireBlink || this.state.blinkDetected;
        const movementPassed = !this.options.requireHeadMovement || this.state.headMovementDetected;
        const qualityPassed = this.state.qualityPassed;

        return blinkPassed && movementPassed && qualityPassed;
    }

    /**
     * Get current instruction for user
     */
    _getCurrentInstruction() {
        if (!this.state.qualityPassed) {
            return 'Position your face clearly in the frame';
        }
        if (this.options.requireBlink && !this.state.blinkDetected) {
            return 'Blink naturally';
        }
        if (this.options.requireHeadMovement && !this.state.headMovementDetected) {
            return 'Move your head slightly';
        }
        return 'Hold still...';
    }

    /**
     * Get current progress percentage
     */
    _getProgress() {
        let progress = 0;
        const steps = [];

        if (this.options.requireBlink) steps.push('blink');
        if (this.options.requireHeadMovement) steps.push('movement');
        steps.push('quality');

        const totalSteps = steps.length;
        let completedSteps = 0;

        if (this.state.qualityPassed) completedSteps++;
        if (!this.options.requireBlink || this.state.blinkDetected) completedSteps++;
        if (!this.options.requireHeadMovement || this.state.headMovementDetected) completedSteps++;

        progress = (completedSteps / totalSteps) * 100;
        return Math.round(progress);
    }

    /**
     * Check if timeout has occurred
     */
    _isTimeout() {
        if (!this.state.startTime) return false;
        const elapsed = (Date.now() - this.state.startTime) / 1000;
        return elapsed > this.options.timeoutSeconds;
    }

    /**
     * Start timeout timer
     */
    _startTimeoutTimer() {
        setTimeout(() => {
            if (!this._allChecksPassed()) {
                this.callbacks.onTimeout();
            }
        }, this.options.timeoutSeconds * 1000);
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LivenessDetector;
}
