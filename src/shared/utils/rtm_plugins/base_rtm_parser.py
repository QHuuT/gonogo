"""
Base RTM Parser Plugin

Abstract base class for RTM parsers.
Provides interface for parsing different RTM formats.

Related Issue: US-00017 - Comprehensive testing and extensibility framework
Epic: EP-00005 - RTM Automation
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from . import RTMPlugin


class BaseRTMParser(RTMPlugin):
    """Base class for RTM parsers."""

    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """
        Determine if this parser can handle the content format.

        Args:
            content: Raw RTM file content

        Returns:
            True if this parser can handle the format
        """
        pass

    @abstractmethod
    def parse_requirements(self, content: str) -> List[Dict]:
        """
        Parse requirements from RTM content.

        Args:
            content: Raw RTM file content

        Returns:
            List of requirement dictionaries
        """
        pass

    def parse_epics(self, content: str) -> Dict[str, Dict]:
        """
        Parse epic definitions from RTM content.

        Args:
            content: Raw RTM file content

        Returns:
            Dictionary mapping epic IDs to epic information
        """
        return {}  # Default: no epic parsing

    def parse_user_stories(self, content: str) -> List[Dict]:
        """
        Parse user stories from RTM content.

        Args:
            content: Raw RTM file content

        Returns:
            List of user story dictionaries
        """
        return []  # Default: no user story parsing

    def parse_metadata(self, content: str) -> Dict:
        """
        Parse RTM metadata (title, version, dates, etc.).

        Args:
            content: Raw RTM file content

        Returns:
            Metadata dictionary
        """
        return {}  # Default: no metadata parsing

    def get_parser_priority(self) -> int:
        """
        Get parser priority (higher = checked first).

        Returns:
            Priority value (0-100)
        """
        return 50  # Default priority


class StandardMarkdownParser(BaseRTMParser):
    """Standard markdown RTM parser."""

    @property
    def name(self) -> str:
        return "standard_markdown"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Parse standard markdown RTM format"

    def can_parse(self, content: str) -> bool:
        """Check for standard RTM markers."""
        return (
            "Requirements Traceability Matrix" in content and
            "| Epic | User Story |" in content
        )

    def parse_requirements(self, content: str) -> List[Dict]:
        """Parse requirements from markdown table."""
        requirements = []
        lines = content.split('\n')

        in_table = False
        headers = []

        for line in lines:
            line = line.strip()

            # Find table start
            if '| Epic | User Story |' in line:
                in_table = True
                headers = self._parse_table_headers(line)
                continue

            # Skip separator line
            if in_table and line.startswith('|--'):
                continue

            # End of table
            if in_table and not line.startswith('|'):
                in_table = False
                continue

            # Parse table row
            if in_table and line.startswith('|'):
                row_data = self._parse_table_row(line, headers)
                if row_data:
                    requirements.append(row_data)

        return requirements

    def parse_epics(self, content: str) -> Dict[str, Dict]:
        """Parse epic sections."""
        epics = {}
        lines = content.split('\n')

        current_epic = None
        for line in lines:
            line = line.strip()

            # Find epic headers
            if line.startswith('## Epic '):
                # Extract epic info from header
                epic_info = self._parse_epic_header(line)
                if epic_info:
                    current_epic = epic_info['id']
                    epics[current_epic] = epic_info

        return epics

    def parse_metadata(self, content: str) -> Dict:
        """Parse RTM metadata from header."""
        metadata = {}
        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            # Parse metadata fields
            if line.startswith('**Project**:'):
                metadata['project'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Version**:'):
                metadata['version'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Last Updated**:'):
                metadata['last_updated'] = line.split(':', 1)[1].strip()
            elif line.startswith('**Maintained By**:'):
                metadata['maintained_by'] = line.split(':', 1)[1].strip()

        return metadata

    def _parse_table_headers(self, header_line: str) -> List[str]:
        """Parse table headers from markdown table."""
        headers = []
        parts = header_line.split('|')

        for part in parts:
            part = part.strip()
            if part:
                headers.append(part.lower().replace(' ', '_'))

        return headers

    def _parse_table_row(self, row_line: str, headers: List[str]) -> Dict:
        """Parse single table row."""
        parts = row_line.split('|')
        row_data = {}

        for i, part in enumerate(parts):
            part = part.strip()
            if i < len(headers) and headers[i] and part:
                # Extract text from markdown links
                if part.startswith('[') and '](' in part:
                    # Extract link text
                    link_text = part.split('[')[1].split(']')[0]
                    link_text = link_text.replace('**', '')  # Remove bold
                    row_data[headers[i]] = link_text
                else:
                    row_data[headers[i]] = part

        return row_data if row_data else None

    def _parse_epic_header(self, header_line: str) -> Dict:
        """Parse epic header line."""
        # Example: "## Epic 1: Authentication System"
        if ':' in header_line:
            parts = header_line.split(':', 1)
            epic_part = parts[0].replace('##', '').strip()
            title = parts[1].strip()

            # Extract epic number/ID if present
            epic_words = epic_part.split()
            if len(epic_words) >= 2:
                epic_id = epic_words[-1]
                return {
                    'id': f'EP-{epic_id.zfill(5)}' if epic_id.isdigit() else epic_id,
                    'title': title,
                    'number': epic_id
                }

        return None

    def get_parser_priority(self) -> int:
        """Standard parser has default priority."""
        return 50