/**
 * Attendance Calendar Component
 * Interactive calendar view for attendance visualization
 */

class AttendanceCalendar {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with id "${containerId}" not found`);
            return;
        }

        this.options = {
            attendanceData: options.attendanceData || [],
            onDayClick: options.onDayClick || null,
            showStats: options.showStats !== false,
            showLegend: options.showLegend !== false,
            ...options
        };

        this.currentDate = new Date();
        this.currentMonth = this.currentDate.getMonth();
        this.currentYear = this.currentDate.getFullYear();

        this.init();
    }

    init() {
        this.render();
    }

    render() {
        const html = `
            ${this.options.showStats ? this.renderStats() : ''}
            <div class="calendar-header">
                <h3 class="calendar-title">📅 Attendance Calendar</h3>
                <div class="calendar-nav">
                    <button class="calendar-nav-btn" id="prev-month">
                        ← Previous
                    </button>
                    <div class="calendar-month-year" id="month-year"></div>
                    <button class="calendar-nav-btn" id="next-month">
                        Next →
                    </button>
                </div>
            </div>
            <div class="calendar-grid" id="calendar-grid"></div>
            ${this.options.showLegend ? this.renderLegend() : ''}
        `;

        this.container.innerHTML = html;
        this.updateCalendar();
        this.attachEventListeners();
    }

    renderStats() {
        const stats = this.calculateStats();
        return `
            <div class="calendar-stats">
                <div class="calendar-stat-card present">
                    <div class="calendar-stat-value">${stats.present}</div>
                    <div class="calendar-stat-label">Present</div>
                </div>
                <div class="calendar-stat-card absent">
                    <div class="calendar-stat-value">${stats.absent}</div>
                    <div class="calendar-stat-label">Absent</div>
                </div>
                <div class="calendar-stat-card percentage">
                    <div class="calendar-stat-value">${stats.percentage}%</div>
                    <div class="calendar-stat-label">Attendance</div>
                </div>
            </div>
        `;
    }

    renderLegend() {
        return `
            <div class="calendar-legend">
                <div class="calendar-legend-item">
                    <div class="calendar-legend-dot present"></div>
                    <span>Present</span>
                </div>
                <div class="calendar-legend-item">
                    <div class="calendar-legend-dot absent"></div>
                    <span>Absent</span>
                </div>
                <div class="calendar-legend-item">
                    <div class="calendar-legend-dot today"></div>
                    <span>Today</span>
                </div>
            </div>
        `;
    }

    updateCalendar() {
        const monthYear = document.getElementById('month-year');
        if (monthYear) {
            const monthNames = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            monthYear.textContent = `${monthNames[this.currentMonth]} ${this.currentYear}`;
        }

        const grid = document.getElementById('calendar-grid');
        if (grid) {
            grid.innerHTML = this.renderCalendarGrid();
        }

        // Update stats if shown
        if (this.options.showStats) {
            const statsContainer = this.container.querySelector('.calendar-stats');
            if (statsContainer) {
                statsContainer.outerHTML = this.renderStats();
            }
        }
    }

    renderCalendarGrid() {
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        let html = '';

        // Day headers
        dayHeaders.forEach(day => {
            html += `<div class="calendar-day-header">${day}</div>`;
        });

        // Get first day of month and number of days
        const firstDay = new Date(this.currentYear, this.currentMonth, 1).getDay();
        const daysInMonth = new Date(this.currentYear, this.currentMonth + 1, 0).getDate();
        const daysInPrevMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();

        const today = new Date();
        const isCurrentMonth = today.getMonth() === this.currentMonth && 
                               today.getFullYear() === this.currentYear;

        // Previous month days
        for (let i = firstDay - 1; i >= 0; i--) {
            const day = daysInPrevMonth - i;
            html += this.renderDay(day, true, false);
        }

        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
            const isToday = isCurrentMonth && day === today.getDate();
            const isFuture = this.isFutureDate(day);
            html += this.renderDay(day, false, isToday, isFuture);
        }

        // Next month days to fill grid
        const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
        const remainingCells = totalCells - (firstDay + daysInMonth);
        for (let day = 1; day <= remainingCells; day++) {
            html += this.renderDay(day, true, false);
        }

        return html;
    }

    renderDay(day, isOtherMonth, isToday, isFuture = false) {
        const dateStr = this.getDateString(day, isOtherMonth);
        const attendance = this.getAttendanceForDate(dateStr);
        
        let classes = ['calendar-day'];
        if (isOtherMonth) classes.push('other-month');
        if (isToday) classes.push('today');
        if (isFuture) classes.push('future');
        if (attendance) classes.push(attendance.status);

        const statusDot = attendance && !isFuture ? 
            `<div class="calendar-day-status"></div>` : '';

        return `
            <div class="${classes.join(' ')}" data-date="${dateStr}">
                <div class="calendar-day-number">${day}</div>
                ${statusDot}
            </div>
        `;
    }

    getDateString(day, isOtherMonth) {
        let month = this.currentMonth;
        let year = this.currentYear;

        if (isOtherMonth) {
            if (day > 15) {
                // Previous month
                month = month === 0 ? 11 : month - 1;
                if (month === 11) year--;
            } else {
                // Next month
                month = month === 11 ? 0 : month + 1;
                if (month === 0) year++;
            }
        }

        return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }

    getAttendanceForDate(dateStr) {
        return this.options.attendanceData.find(item => item.date === dateStr);
    }

    isFutureDate(day) {
        const checkDate = new Date(this.currentYear, this.currentMonth, day);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return checkDate > today;
    }

    calculateStats() {
        const currentMonthData = this.options.attendanceData.filter(item => {
            const date = new Date(item.date);
            return date.getMonth() === this.currentMonth && 
                   date.getFullYear() === this.currentYear;
        });

        const present = currentMonthData.filter(item => item.status === 'present').length;
        const total = currentMonthData.length;
        const absent = total - present;
        const percentage = total > 0 ? Math.round((present / total) * 100) : 0;

        return { present, absent, total, percentage };
    }

    attachEventListeners() {
        const prevBtn = document.getElementById('prev-month');
        const nextBtn = document.getElementById('next-month');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousMonth());
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextMonth());
        }

        // Day click events
        const days = this.container.querySelectorAll('.calendar-day:not(.other-month):not(.future)');
        days.forEach(day => {
            day.addEventListener('click', (e) => {
                const dateStr = e.currentTarget.dataset.date;
                const attendance = this.getAttendanceForDate(dateStr);
                if (this.options.onDayClick) {
                    this.options.onDayClick(dateStr, attendance);
                }
            });
        });
    }

    previousMonth() {
        this.currentMonth--;
        if (this.currentMonth < 0) {
            this.currentMonth = 11;
            this.currentYear--;
        }
        this.updateCalendar();
        this.attachEventListeners();
    }

    nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 11) {
            this.currentMonth = 0;
            this.currentYear++;
        }
        this.updateCalendar();
        this.attachEventListeners();
    }

    updateData(newData) {
        this.options.attendanceData = newData;
        this.updateCalendar();
        this.attachEventListeners();
    }

    goToToday() {
        const today = new Date();
        this.currentMonth = today.getMonth();
        this.currentYear = today.getFullYear();
        this.updateCalendar();
        this.attachEventListeners();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AttendanceCalendar;
}
