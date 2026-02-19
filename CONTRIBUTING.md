# Contributing to Face Recognition Attendance System

Thank you for your interest in contributing to our project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic knowledge of Flask and SQLAlchemy
- Understanding of face recognition concepts (helpful but not required)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
   cd Face-Recognition-Attendance-System
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/rajpratham1/Face-Recognition-Attendance-System.git
   ```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install in editable mode for development
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Setup Development Database

```bash
# Create .env for development
cp .env.example .env.dev

# Initialize database
flask --app manage.py db upgrade
python create_admin.py
```

### 4. Run in Development Mode

```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows

python app.py
```

## How to Contribute

### Types of Contributions

We welcome many types of contributions:

1. **Bug Fixes** - Fix issues reported in GitHub Issues
2. **New Features** - Implement features from the roadmap or propose new ones
3. **Documentation** - Improve README, docstrings, or create tutorials
4. **Testing** - Add test cases to improve coverage
5. **Code Review** - Review open pull requests
6. **Translations** - Translate UI to other languages
7. **UI/UX Improvements** - Enhance user interface and experience

### Contribution Workflow

1. **Check existing issues** - Look for open issues or create a new one
2. **Discuss the change** - Comment on the issue to discuss your approach
3. **Create a branch** - Use descriptive branch names
   ```bash
   git checkout -b feature/add-report-generation
   git checkout -b fix/geofencing-bug
   git checkout -b docs/update-api-docs
   ```
4. **Make your changes** - Follow coding standards
5. **Write tests** - Add tests for new functionality
6. **Update documentation** - Update relevant docs
7. **Commit changes** - Use clear commit messages
8. **Push to your fork** - Push your branch
9. **Submit a pull request** - Open a PR to the main repository

## Coding Standards

### Python Style Guide

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these specifics:

#### Naming Conventions

```python
# Classes: PascalCase
class SessionAttendance(db.Model):
    pass

# Functions/Methods: snake_case
def mark_attendance(session_id, student_id):
    pass

# Constants: UPPER_SNAKE_CASE
FACE_MATCH_THRESHOLD = 0.6

# Private methods: _leading_underscore
def _validate_session(self, session_id):
    pass
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Optional, List, Dict

def get_active_sessions(student_id: int) -> List[ClassSession]:
    """Get all active sessions for a student.
    
    Args:
        student_id: The ID of the student
        
    Returns:
        List of active ClassSession objects
    """
    return ClassSession.query.filter(...).all()

def calculate_distance(known: np.ndarray, unknown: np.ndarray) -> float:
    """Calculate Euclidean distance between face descriptors."""
    return float(np.linalg.norm(known - unknown))
```

#### Docstrings

Use Google-style docstrings:

```python
def record_attendance_attempt(
    session_id: int,
    student_id: int,
    success: bool,
    reason: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None
) -> AttendanceAttempt:
    """Record an attendance attempt for audit purposes.
    
    This function creates an audit log entry for every attendance
    marking attempt, whether successful or failed. Used for
    fraud detection and security monitoring.
    
    Args:
        session_id: ID of the class session
        student_id: ID of the student attempting attendance
        success: Whether the attempt was successful
        reason: Human-readable reason for success/failure
        lat: Optional latitude coordinate
        lng: Optional longitude coordinate
        
    Returns:
        The created AttendanceAttempt object
        
    Raises:
        ValueError: If session_id or student_id is invalid
        
    Example:
        >>> record_attendance_attempt(
        ...     session_id=1,
        ...     student_id=42,
        ...     success=False,
        ...     reason="Outside campus"
        ... )
    """
    pass
```

#### Error Handling

```python
# Good: Specific exception handling
try:
    session = ClassSession.query.get(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
except SQLAlchemyError as e:
    db.session.rollback()
    app.logger.error(f"Database error: {e}")
    return jsonify({"success": False, "message": "Database error"}), 500

# Bad: Bare except
try:
    do_something()
except:  # Never do this
    pass
```

### JavaScript Style Guide

#### ES6+ Standards

```javascript
// Use const/let, not var
const sessionId = document.getElementById('session-id').value;
let faceDescriptor = null;

// Arrow functions for callbacks
sessions.forEach(session => {
    console.log(session.title);
});

// Async/await instead of callbacks
async function markAttendance() {
    try {
        const detections = await faceapi.detectSingleFace(video)
            .withFaceLandmarks()
            .withFaceDescriptor();
            
        if (!detections) {
            throw new Error('No face detected');
        }
        
        const response = await fetch('/api/session_attendance/mark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                descriptor: Array.from(detections.descriptor)
            })
        });
        
        const result = await response.json();
        console.log('Success:', result);
    } catch (error) {
        console.error('Error:', error);
    }
}
```

#### JSDoc Comments

```javascript
/**
 * Validate face detection results
 * @param {Array<Object>} detections - Face detection results from face-api.js
 * @returns {boolean} True if exactly one face detected
 * @throws {Error} If multiple faces or no faces detected
 */
function validateFaceDetection(detections) {
    if (!detections || detections.length === 0) {
        throw new Error('No face detected');
    }
    if (detections.length > 1) {
        throw new Error('Multiple faces detected');
    }
    return true;
}
```

### HTML/CSS Standards

#### Template Structure

```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <div class="row">
        <div class="col-md-6">
            <!-- Content here -->
        </div>
    </div>
</div>
{% endblock %}
```

#### CSS Classes

- Use Bootstrap utility classes when possible
- Custom classes should be descriptive and lowercase with hyphens
- Avoid inline styles

```html
<!-- Good -->
<div class="glass-card mb-4">
    <h4 class="section-title">Active Sessions</h4>
    <div class="session-grid">
        <!-- ... -->
    </div>
</div>

<!-- Bad -->
<div style="margin-bottom: 20px; background: white;">
    <h4>Active Sessions</h4>
</div>
```

### SQL and Database

#### Use SQLAlchemy ORM

```python
# Good: ORM usage
users = User.query.filter_by(role='student').all()
session = ClassSession.query.get(session_id)

# Good: Complex queries with joins
students = (
    User.query
    .join(Enrollment, Enrollment.student_id == User.id)
    .join(Course, Course.id == Enrollment.course_id)
    .filter(Course.teacher_id == teacher_id)
    .distinct()
    .all()
)

# Bad: Raw SQL (avoid unless absolutely necessary)
db.session.execute("SELECT * FROM users WHERE role = 'student'")
```

#### Database Migrations

Always use Flask-Migrate for schema changes:

```bash
# After modifying models.py
flask --app manage.py db migrate -m "Add device_hash column to session_attendance"
flask --app manage.py db upgrade

# Review the generated migration file before committing!
```

## Testing Guidelines

### Writing Tests

All new features must include tests. Tests should cover:

1. **Happy path** - Normal successful execution
2. **Edge cases** - Boundary conditions
3. **Error cases** - Expected failures
4. **Security** - Authorization, validation

#### Test Structure

```python
import pytest
from app import app, db, User, ClassSession

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def auth_student(client):
    """Create and authenticate a student user"""
    user = User(
        name='Test Student',
        email='student@test.com',
        department='CS',
        role='student',
        password_hash=generate_password_hash('password'),
        face_registered=True,
        face_encoding=json.dumps([0.1] * 128)
    )
    db.session.add(user)
    db.session.commit()
    
    client.post('/login', data={
        'email': 'student@test.com',
        'password': 'password'
    })
    
    return user

def test_mark_attendance_success(client, auth_student):
    """Test successful attendance marking"""
    # Arrange
    session = create_test_session()
    enroll_student_in_course(auth_student, session.course_id)
    
    # Act
    response = client.post('/api/session_attendance/mark', json={
        'session_id': session.id,
        'descriptor': [0.1] * 128,
        'lat': 28.325764684367748,
        'lng': 79.46097110207619
    })
    
    # Assert
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # Verify database record created
    attendance = SessionAttendance.query.filter_by(
        session_id=session.id,
        student_id=auth_student.id
    ).first()
    assert attendance is not None

def test_mark_attendance_outside_campus(client, auth_student):
    """Test attendance fails when outside campus"""
    session = create_test_session()
    
    response = client.post('/api/session_attendance/mark', json={
        'session_id': session.id,
        'descriptor': [0.1] * 128,
        'lat': 0.0,  # Not in Invertis
        'lng': 0.0
    })
    
    assert response.status_code == 400
    assert 'campus' in response.json['message'].lower()
```

### Test Coverage

- Aim for **80%+ code coverage**
- Critical paths must have 100% coverage:
  - Authentication
  - Attendance marking
  - Face verification
  - Geofencing

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Pull Request Process

### Before Submitting

1. **Update from upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Check code style**
   ```bash
   flake8 app.py models.py
   black --check app.py models.py
   ```

4. **Update documentation** if needed

### PR Title Format

Use conventional commit format:

```
feat: Add attendance report generation
fix: Correct geofencing distance calculation
docs: Update API documentation
test: Add tests for session management
refactor: Simplify face verification logic
perf: Optimize database queries
style: Format code with black
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

### Review Process

1. Maintainers will review your PR within **3-5 business days**
2. Address review feedback promptly
3. Maintainers may request changes
4. Once approved, maintainers will merge
5. Your contribution will be credited in release notes

## Issue Guidelines

### Before Creating an Issue

1. **Search existing issues** - Your issue might already exist
2. **Check FAQ and documentation**
3. **Try latest version** - Bug might be fixed

### Issue Templates

#### Bug Report

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10, Ubuntu 20.04]
 - Browser: [e.g. Chrome 98, Firefox 97]
 - Python Version: [e.g. 3.9.7]
 - Flask Version: [e.g. 3.0.0]

**Additional context**
Add any other context about the problem here.
```

#### Feature Request

```markdown
**Is your feature request related to a problem?**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions.

**Additional context**
Add any other context or screenshots about the feature request.
```

### Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `question` - Further information is requested
- `wontfix` - This will not be worked on
- `duplicate` - This issue or pull request already exists

## Development Tips

### Debugging

```python
# Enable SQL query logging
app.config['SQLALCHEMY_ECHO'] = True

# Use Flask debugger
import pdb; pdb.set_trace()

# Better error pages
app.config['DEBUG'] = True
```

### Testing Locally

```bash
# Run specific test
pytest tests/test_attendance.py::test_mark_attendance_success -v

# Run with print statements
pytest -s

# Run failed tests only
pytest --lf
```

### Database Tips

```bash
# View current schema
flask --app manage.py db current

# View migration history
flask --app manage.py db history

# Rollback one migration
flask --app manage.py db downgrade

# Reset database completely
rm instance/attendance.db
flask --app manage.py db upgrade
```

## Questions?

- **Email**: support@invertis.org
- **GitHub Discussions**: Use for questions and discussions
- **GitHub Issues**: Use only for bugs and feature requests

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project website (coming soon)

Thank you for contributing! 🎉
