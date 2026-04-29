"""
Unit tests for liveness detection configuration and integration
"""
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config import Config


class TestLivenessConfiguration:
    """Test liveness detection configuration"""

    def test_liveness_config_defaults(self):
        """Test that liveness detection has proper default values"""
        assert hasattr(Config, 'LIVENESS_DETECTION_ENABLED')
        assert hasattr(Config, 'LIVENESS_REQUIRE_BLINK')
        assert hasattr(Config, 'LIVENESS_REQUIRE_HEAD_MOVEMENT')
        assert hasattr(Config, 'LIVENESS_TIMEOUT_SECONDS')
        assert hasattr(Config, 'LIVENESS_BLINK_THRESHOLD')
        assert hasattr(Config, 'LIVENESS_MOVEMENT_THRESHOLD')
        assert hasattr(Config, 'LIVENESS_QUALITY_THRESHOLD')

    def test_liveness_enabled_by_default(self):
        """Test that liveness detection is enabled by default"""
        assert Config.LIVENESS_DETECTION_ENABLED is True

    def test_liveness_timeout_is_positive(self):
        """Test that timeout is a positive integer"""
        assert isinstance(Config.LIVENESS_TIMEOUT_SECONDS, int)
        assert Config.LIVENESS_TIMEOUT_SECONDS > 0

    def test_liveness_thresholds_in_valid_range(self):
        """Test that thresholds are in valid ranges"""
        assert 0.0 <= Config.LIVENESS_BLINK_THRESHOLD <= 1.0
        assert Config.LIVENESS_MOVEMENT_THRESHOLD > 0
        assert 0.0 <= Config.LIVENESS_QUALITY_THRESHOLD <= 1.0


class TestLivenessTemplateContext:
    """Test liveness configuration in template context"""

    def test_liveness_config_in_context(self):
        """Test that liveness config is available in template context"""
        with app.app_context():
            with app.test_request_context():
                # Get template context
                context_processor = app.context_processor(lambda: {})
                for func in app.template_context_processors[None]:
                    context = func()
                    if 'liveness_config' in context:
                        liveness_config = context['liveness_config']
                        assert 'enabled' in liveness_config
                        assert 'requireBlink' in liveness_config
                        assert 'requireHeadMovement' in liveness_config
                        assert 'timeoutSeconds' in liveness_config
                        assert 'blinkThreshold' in liveness_config
                        assert 'movementThreshold' in liveness_config
                        assert 'qualityThreshold' in liveness_config
                        break
                else:
                    pytest.fail("liveness_config not found in template context")

    def test_liveness_config_values_match_app_config(self):
        """Test that template context values match app config"""
        with app.app_context():
            with app.test_request_context():
                for func in app.template_context_processors[None]:
                    context = func()
                    if 'liveness_config' in context:
                        liveness_config = context['liveness_config']
                        assert liveness_config['enabled'] == app.config.get('LIVENESS_DETECTION_ENABLED', True)
                        assert liveness_config['requireBlink'] == app.config.get('LIVENESS_REQUIRE_BLINK', True)
                        assert liveness_config['requireHeadMovement'] == app.config.get('LIVENESS_REQUIRE_HEAD_MOVEMENT', True)
                        assert liveness_config['timeoutSeconds'] == app.config.get('LIVENESS_TIMEOUT_SECONDS', 15)
                        break


class TestLivenessStaticFiles:
    """Test that liveness detection static files exist"""

    def test_liveness_js_exists(self):
        """Test that liveness.js file exists"""
        import os
        liveness_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static',
            'liveness.js'
        )
        assert os.path.exists(liveness_js_path), "liveness.js file not found"

    def test_liveness_js_has_class(self):
        """Test that liveness.js contains LivenessDetector class"""
        import os
        liveness_js_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static',
            'liveness.js'
        )
        with open(liveness_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'class LivenessDetector' in content
            assert 'processFrame' in content
            assert '_detectBlink' in content
            assert '_detectHeadMovement' in content
            assert '_analyzeTexture' in content


class TestLivenessDocumentation:
    """Test that liveness detection documentation exists"""

    def test_liveness_documentation_exists(self):
        """Test that LIVENESS_DETECTION.md file exists"""
        import os
        doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'LIVENESS_DETECTION.md'
        )
        assert os.path.exists(doc_path), "LIVENESS_DETECTION.md file not found"

    def test_liveness_documentation_has_sections(self):
        """Test that documentation has required sections"""
        import os
        doc_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'LIVENESS_DETECTION.md'
        )
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '## Overview' in content
            assert 'Features' in content
            assert 'Configuration' in content
            assert 'Security Benefits' in content
            assert 'Troubleshooting' in content


class TestLivenessIntegration:
    """Test liveness detection integration in templates"""

    def test_register_face_has_liveness_script(self):
        """Test that register_face.html includes liveness.js"""
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates',
            'register_face.html'
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'liveness.js' in content
            assert 'LivenessDetector' in content
            assert 'liveness_verified' in content

    def test_student_attendance_has_liveness_script(self):
        """Test that student_mark_attendance.html includes liveness.js"""
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates',
            'student_mark_attendance.html'
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'liveness.js' in content
            assert 'LivenessDetector' in content
            assert 'liveness_verified' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
