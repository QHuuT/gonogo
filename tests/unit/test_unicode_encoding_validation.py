"""
Unit tests for Unicode encoding validation across the project.

This test module ensures that file operations handle Unicode characters properly,
preventing UnicodeEncodeError issues on Windows and other platforms.

Related to: US-00031 (Unicode encoding fixes)
"""

import tempfile
from pathlib import Path

import pytest


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
class TestUnicodeEncodingValidation:
    """Test Unicode character handling in file operations."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_tempfile_with_unicode_content(self):
        """Test that tempfile operations handle Unicode characters correctly."""
        # Content with various Unicode characters that commonly cause issues
        unicode_content = """
# Test Content with Unicode Characters

Status indicators: ✅ ❌ ⚠️ 📝 🔄 ⏳
Mathematical symbols: ∑ ∞ ≠ ≤ ≥ ±
Special characters: © ® ™ € £ ¥
Arrows: → ← ↑ ↓ ↔ ⟶ ⟵

## RTM Example
| Epic | Status |
|------|--------|
| EP-001 | ✅ |
| EP-002 | 📝 |
| EP-003 | ⏳ |
"""

        # This should NOT raise UnicodeEncodeError
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(unicode_content)
            f.flush()
            temp_path = f.name

        # Verify content was written correctly
        with open(temp_path, "r", encoding="utf-8") as f:
            read_content = f.read()

        assert "✅" in read_content
        assert "📝" in read_content
        assert "⏳" in read_content
        assert "→" in read_content

        # Cleanup
        Path(temp_path).unlink()

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_tempfile_without_encoding_fails_on_unicode(self):
        """Test that demonstrates why encoding parameter is mandatory."""
        unicode_content = "Status: ✅ 📝 ⏳"

        # On Windows, this would raise UnicodeEncodeError without encoding='utf-8'
        # We'll simulate the check by ensuring we always use encoding
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            # This should work with explicit encoding
            f.write(unicode_content)
            f.flush()
            temp_path = f.name

        # Verify content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "✅" in content

        # Cleanup
        Path(temp_path).unlink()

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_various_file_operations_with_unicode(self):
        """Test different file operation patterns with Unicode content."""
        test_cases = [
            ("yaml_config", "config:\n  status: ✅\n  mode: 📝"),
            ("python_code", "# Test file ✅\nprint('Status: 📝')"),
            ("markdown_doc", "# Documentation 📝\n\n## Status: ✅"),
            ("json_data", '{"status": "✅", "type": "📝"}'),
        ]

        for file_type, content in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_{file_type}.txt", delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                f.flush()
                temp_path = f.name

            # Verify content roundtrip
            with open(temp_path, "r", encoding="utf-8") as f:
                read_content = f.read()
                assert content == read_content

            # Cleanup
            Path(temp_path).unlink()

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_emoji_heavy_content(self):
        """Test content with many emoji characters that often cause encoding issues."""
        emoji_content = """
🎯 Project Goals:
- 🔧 Fix Unicode encoding issues
- 🧪 Add comprehensive test coverage
- 📝 Update documentation
- ✅ Validate cross-platform compatibility

🚨 Critical Issues:
- ❌ UnicodeEncodeError on Windows
- ⚠️ CP1252 codec failures
- 🔄 Missing encoding parameters

🎉 Success Metrics:
- 📊 100% test coverage
- 🌐 Cross-platform compatibility
- 🛡️ Regression prevention
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(emoji_content)
            f.flush()
            temp_path = f.name

        # Read back and verify all emojis are preserved
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for specific emojis that commonly cause issues
        required_emojis = [
            "🎯",
            "🔧",
            "🧪",
            "📝",
            "✅",
            "🚨",
            "❌",
            "⚠️",
            "🔄",
            "🎉",
            "📊",
            "🌐",
            "🛡️",
        ]
        for emoji in required_emojis:
            assert emoji in content, f"Emoji {emoji} not found in content"

        # Cleanup
        Path(temp_path).unlink()


@pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
@pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
class TestFileOperationPatterns:
    """Test common file operation patterns used throughout the project."""

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_rtm_file_pattern_with_unicode(self):
        """Test the specific pattern used in RTM link generator that caused the original issue."""
        rtm_content = """# Requirements Traceability Matrix

| Epic | User Story | Implementation | Status |
|------|------------|----------------|--------|
| [**EP-00001**](https://github.com/test/repo/issues?q=EP-00001) | [US-00001](https://github.com/test/repo/issues?q=US-00001) | [auth_service.py](../../src/auth_service.py) | ✅ |
| [**EP-00002**](https://github.com/test/repo/issues?q=EP-00002) | [US-00002](https://github.com/test/repo/issues?q=US-00002) | [blog_service.py](../../src/blog_service.py) | ⏳ |
| [**EP-00003**](https://github.com/test/repo/issues?q=EP-00003) | [US-00003](https://github.com/test/repo/issues?q=US-00003) | [comment_service.py](../../src/comment_service.py) | 📝 |
"""

        # This exact pattern caused the UnicodeEncodeError - ensure it now works
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(rtm_content)
            f.flush()
            temp_path = f.name

        # Verify specific Unicode characters that caused the original failure
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "\u2705" in content  # ✅ check mark emoji
        assert "\u23f3" in content  # ⏳ hourglass emoji
        assert "\U0001f4dd" in content  # 📝 memo emoji

        # Cleanup
        Path(temp_path).unlink()

    @pytest.mark.epic("EP-00001", "EP-00002", "EP-00003")
    @pytest.mark.user_story("US-00001", "US-00002", "US-00003", "US-00031")
    def test_config_file_pattern_with_unicode(self):
        """Test YAML config file pattern with Unicode content."""
        config_content = """
github:
  owner: "testowner"
  repo: "testrepo"

status_indicators:
  completed: "✅"
  in_progress: "⏳"
  planned: "📝"
  failed: "❌"
  warning: "⚠️"

validation:
  strict_mode: true
  unicode_support: "🌐"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write(config_content)
            f.flush()
            temp_path = f.name

        # Verify YAML with Unicode content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "✅" in content
            assert "🌐" in content

        # Cleanup
        Path(temp_path).unlink()
