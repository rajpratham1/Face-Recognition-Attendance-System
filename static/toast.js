/**
 * Toast Notification System
 * Modern, non-intrusive notifications with animations
 */

class ToastNotification {
    constructor() {
        this.container = null;
        this.pendingToasts = [];
        this.initialized = false;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
        
        this.initialized = true;
        
        // Show any pending toasts
        this.pendingToasts.forEach(({ message, type, duration }) => {
            this.show(message, type, duration);
        });
        this.pendingToasts = [];
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (default: 4000)
     */
    show(message, type = 'info', duration = 4000) {
        // If not initialized yet, queue the toast
        if (!this.initialized) {
            this.pendingToasts.push({ message, type, duration });
            return null;
        }
        
        console.log('Creating toast element:', type, message);
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} toast-enter`;
        
        // Icon based on type
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" aria-label="Close">&times;</button>
        `;

        // Add to container
        this.container.appendChild(toast);
        console.log('Toast added to container, element:', toast);
        console.log('Container children:', this.container.children.length);

        // Force reflow to ensure animation triggers
        toast.offsetHeight;

        // Trigger animation
        setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-visible');
            console.log('Toast animation triggered, classes:', toast.className);
        }, 10);

        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.remove(toast);
        });

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }

        return toast;
    }

    remove(toast) {
        toast.classList.remove('toast-visible');
        toast.classList.add('toast-exit');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4500) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }

    /**
     * Show a loading toast (doesn't auto-dismiss)
     */
    loading(message = 'Loading...') {
        // If not initialized yet, return null
        if (!this.initialized) {
            return null;
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast toast-loading toast-enter';
        
        toast.innerHTML = `
            <div class="toast-spinner"></div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-visible');
        }, 10);

        return toast;
    }

    /**
     * Clear all toasts
     */
    clearAll() {
        if (!this.initialized || !this.container) return;
        
        const toasts = this.container.querySelectorAll('.toast');
        toasts.forEach(toast => this.remove(toast));
    }
}

// Create global instance
window.toast = new ToastNotification();

// Helper function for backward compatibility with flash messages
window.showToast = (message, type = 'info') => {
    window.toast.show(message, type);
};
