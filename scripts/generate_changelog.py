#!/usr/bin/env python3
"""
Automatic CHANGELOG Generator from Git Commits

Parses Conventional Commits and updates CHANGELOG.md [Unreleased] section.
Preserves "Next Session Plan" and "Known Issues" sections.

Usage:
    python scripts/generate_changelog.py

Requirements:
    - Git repository
    - Conventional Commits format in git log
    - CHANGELOG.md exists in project root

Author: AI Agent
Version: 1.0.0
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ChangelogGenerator:
    """Generate CHANGELOG.md from Conventional Commits."""

    COMMIT_PATTERN = re.compile(
        r'^(?P<type>feat|fix|docs|refactor|test|chore|style|perf)'
        r'(?:\((?P<scope>[^)]+)\))?'
        r': (?P<description>.+)$'
    )

    TYPE_MAPPING = {
        'feat': 'Added',
        'fix': 'Fixed',
        'docs': 'Documentation',
        'refactor': 'Changed',
        'perf': 'Changed',
        'test': 'Testing',
        'chore': 'Internal',
        'style': 'Changed'
    }

    def __init__(self, repo_path: Path = Path('.')):
        self.repo_path = repo_path
        self.changelog_path = repo_path / 'CHANGELOG.md'

    def get_commits_since_last_release(self) -> List[str]:
        """Get all commits since last version tag."""
        try:
            # Get last tag
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            last_tag = result.stdout.strip() if result.returncode == 0 else None

            # Get commits since last tag (or all if no tags)
            if last_tag:
                cmd = ['git', 'log', f'{last_tag}..HEAD', '--oneline', '--no-merges']
            else:
                cmd = ['git', 'log', '--oneline', '--no-merges', '-20']  # Last 20 commits

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                return []

            return [line.strip() for line in result.stdout.split('\n') if line.strip()]

        except Exception as e:
            print(f"Error getting commits: {e}")
            return []

    def parse_commits(self, commits: List[str]) -> Dict[str, List[str]]:
        """Parse commits into changelog sections."""
        sections = {
            'Added': [],
            'Fixed': [],
            'Changed': [],
            'Documentation': [],
            'Testing': [],
            'Internal': []
        }

        for commit in commits:
            # Remove commit hash (first 7 chars)
            if len(commit) > 8:
                commit_msg = commit[8:].strip()
            else:
                continue

            match = self.COMMIT_PATTERN.match(commit_msg)
            if match:
                commit_type = match.group('type')
                scope = match.group('scope')
                description = match.group('description')

                # Format entry
                if scope:
                    entry = f"**{scope.title()}**: {description}"
                else:
                    entry = description

                # Add to appropriate section
                section = self.TYPE_MAPPING.get(commit_type, 'Internal')
                if section in sections:
                    sections[section].append(entry)

        # Remove empty sections
        return {k: v for k, v in sections.items() if v}

    def extract_unreleased_metadata(self) -> Dict[str, str]:
        """Extract Next Session Plan and Known Issues from current CHANGELOG."""
        if not self.changelog_path.exists():
            return {'next_session': '', 'known_issues': ''}

        content = self.changelog_path.read_text(encoding='utf-8')

        # Extract Next Session Plan
        next_session_match = re.search(
            r'### Next Session Plan\n(.*?)(?=\n###|\n##|\Z)',
            content,
            re.DOTALL
        )
        next_session = next_session_match.group(1).strip() if next_session_match else ''

        # Extract Known Issues
        known_issues_match = re.search(
            r'### Known Issues.*?\n(.*?)(?=\n###|\n##|\Z)',
            content,
            re.DOTALL
        )
        known_issues = known_issues_match.group(1).strip() if known_issues_match else ''

        return {
            'next_session': next_session,
            'known_issues': known_issues
        }

    def generate_unreleased_section(self, sections: Dict[str, List[str]],
                                   metadata: Dict[str, str]) -> str:
        """Generate [Unreleased] section with new commits."""
        lines = ['## [Unreleased]', '']

        # Add Next Session Plan (preserved from existing CHANGELOG)
        if metadata['next_session']:
            lines.append('### Next Session Plan')
            lines.append(metadata['next_session'])
            lines.append('')

        # Add changelog sections
        for section_name, entries in sections.items():
            if entries:
                lines.append(f'### {section_name}')
                for entry in entries:
                    lines.append(f'- {entry}')
                lines.append('')

        # Add Known Issues (preserved from existing CHANGELOG)
        if metadata['known_issues']:
            lines.append('### Known Issues')
            lines.append(metadata['known_issues'])
            lines.append('')

        return '\n'.join(lines)

    def update_changelog(self) -> bool:
        """Update CHANGELOG.md with new commits."""
        # Get commits
        commits = self.get_commits_since_last_release()
        if not commits:
            print("No new commits found.")
            return False

        # Parse commits
        sections = self.parse_commits(commits)
        if not sections:
            print("No valid Conventional Commits found.")
            return False

        # Extract existing metadata
        metadata = self.extract_unreleased_metadata()

        # Generate new [Unreleased] section
        new_unreleased = self.generate_unreleased_section(sections, metadata)

        # Read existing CHANGELOG
        if self.changelog_path.exists():
            content = self.changelog_path.read_text(encoding='utf-8')

            # Remove old [Unreleased] section
            content = re.sub(
                r'## \[Unreleased\].*?(?=\n## \[|\Z)',
                '',
                content,
                flags=re.DOTALL
            )

            # Find where to insert (after header, before first version)
            header_end = content.find('## [')
            if header_end == -1:
                # No versions yet, append to end
                new_content = content.rstrip() + '\n\n' + new_unreleased + '\n'
            else:
                # Insert before first version
                new_content = content[:header_end] + new_unreleased + '\n' + content[header_end:]
        else:
            # Create new CHANGELOG
            new_content = (
                '# Changelog\n\n'
                '**RULES: Follow [Keep a Changelog](https://keepachangelog.com/) standard strictly.**\n\n'
                + new_unreleased + '\n'
            )

        # Write updated CHANGELOG
        self.changelog_path.write_text(new_content, encoding='utf-8')
        print(f"[SUCCESS] CHANGELOG.md updated with {len(commits)} commits")
        return True


def main():
    """Run changelog generator."""
    print("Generating CHANGELOG from git commits...")

    generator = ChangelogGenerator()
    success = generator.update_changelog()

    if success:
        print("\n[DONE] CHANGELOG.md has been updated!")
        print("Review changes with: git diff CHANGELOG.md")
    else:
        print("\n[WARNING] No changes made to CHANGELOG.md")


if __name__ == '__main__':
    main()
