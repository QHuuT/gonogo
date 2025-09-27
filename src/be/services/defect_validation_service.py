"""
Defect Validation Service

Provides ongoing validation for defect-user story relationships in the RTM system.
Ensures relationship consistency and supports automated monitoring.

Related Issue: US-00011 - Fix Defect-User Story Relationship Links
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.traceability.defect import Defect
from ..models.traceability.user_story import UserStory

logger = logging.getLogger(__name__)


class DefectValidationService:
    """Service for validating defect-user story relationship consistency."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize with optional database session."""
        self.session = session or SessionLocal()
        self._should_close_session = session is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with session cleanup."""
        if self._should_close_session:
            self.session.close()

    def validate_all_relationships(self) -> Dict[str, any]:
        """
        Validate all defect-user story relationships.

        Returns:
            Dict with validation results and statistics
        """
        logger.info("Starting comprehensive defect relationship validation")

        results = {
    
            "validation_status": "success",
            "total_defects": 0,
            "linked_defects": 0,
            "valid_links": 0,
            "broken_links": 0,
            "orphaned_defects": 0,
            "broken_link_details": [],
            "orphaned_defect_details": [],
            "validation_errors": [],
        
}

        try:
            # Get total defect count
            results["total_defects"] = self.session.query(Defect).count()

            # Validate linked defects
            linked_defects = (
                self.session.query(Defect)
                .filter(Defect.github_user_story_number.isnot(None))
                .all()
            )
            results["linked_defects"] = len(linked_defects)

            # Check each linked defect
            for defect in linked_defects:
                user_story = (
                    self.session.query(UserStory)
                    .filter(
                        UserStory.github_issue_number == defect.github_user_story_number
                    )
                    .first()
                )

                if user_story:
                    results["valid_links"] += 1
                    logger.debug(
                        f"Valid link: {defect.defect_id} -> {user_story.user_story_id}"
                    )
                else:
                    results["broken_links"] += 1
                    broken_detail = {
    
                        "defect_id": defect.defect_id,
                        "defect_title": defect.title,
                        "broken_reference": defect.github_user_story_number,
                        "github_issue_number": defect.github_issue_number,
                    
}
                    results["broken_link_details"].append(broken_detail)
                    logger.warning(
                        (
    f"Broken link: {defect.defect_id} -> "
    f"US #{defect.github_user_story_number} (NOT FOUND)"
)
                    )

            # Check orphaned defects
            orphaned_defects = (
                self.session.query(Defect)
                .filter(Defect.github_user_story_number.is_(None))
                .all()
            )
            results["orphaned_defects"] = len(orphaned_defects)

            # Analyze orphaned defects for potential references
            for defect in orphaned_defects:
                potential_refs = self._find_potential_user_story_references(defect)
                if potential_refs:
                    orphaned_detail = {
    
                        "defect_id": defect.defect_id,
                        "defect_title": defect.title,
                        "potential_references": potential_refs,
                        "github_issue_number": defect.github_issue_number,
                    
}
                    results["orphaned_defect_details"].append(orphaned_detail)

            # Log summary
            logger.info(
                f"Validation complete: {results['valid_links']} valid, "
                f"{results['broken_links']} broken, "
                f"{results['orphaned_defects']} orphaned"
            )

        except Exception as e:
            results["validation_status"] = "error"
            results["validation_errors"].append(str(e))
            logger.error(f"Error during validation: {e}")

        return results

    def validate_defect_relationship(self, defect_id: str) -> Dict[str, any]:
        """
        Validate a specific defect's user story relationship.

        Args:
            defect_id: The defect ID to validate

        Returns:
            Dict with validation results for the specific defect
        """
        logger.debug(f"Validating relationship for defect: {defect_id}")

        result = {
    
            "defect_id": defect_id,
            "validation_status": "success",
            "has_user_story_link": False,
            "link_is_valid": False,
            "user_story_id": None,
            "potential_references": [],
            "validation_errors": [],
        
}

        try:
            defect = (
                self.session.query(Defect).filter(Defect.defect_id == defect_id).first()
            )

            if not defect:
                result["validation_status"] = "error"
                result["validation_errors"].append(f"Defect {defect_id} not found")
                return result

            # Check if defect has user story link
            if defect.github_user_story_number:
                result["has_user_story_link"] = True

                # Validate the link
                user_story = (
                    self.session.query(UserStory)
                    .filter(
                        UserStory.github_issue_number == defect.github_user_story_number
                    )
                    .first()
                )

                if user_story:
                    result["link_is_valid"] = True
                    result["user_story_id"] = user_story.user_story_id
                    logger.debug(
                        f"Valid link: {defect_id} -> {user_story.user_story_id}"
                    )
                else:
                    result["validation_errors"].append(
                        f"Broken link: references non-existent US #{defect.github_user_story_number}"
                    )
                    logger.warning(
                        f"Broken link: {defect_id} -> US #{defect.github_user_story_number}"
                    )
            else:
                # Look for potential references
                result["potential_references"] = (
                    self._find_potential_user_story_references(defect)
                )

        except Exception as e:
            result["validation_status"] = "error"
            result["validation_errors"].append(str(e))
            logger.error(f"Error validating defect {defect_id}: {e}")

        return result

    def get_relationship_health_metrics(self) -> Dict[str, any]:
        """
        Get overall health metrics for defect-user story relationships.

        Returns:
            Dict with health metrics and percentages
        """
        logger.debug("Calculating relationship health metrics")

        try:
            total_defects = self.session.query(Defect).count()

            if total_defects == 0:
                return {
    
                    "total_defects": 0,
                    "relationship_health_score": 100.0,
                    "linked_percentage": 0.0,
                    "valid_link_percentage": 0.0,
                    "broken_link_percentage": 0.0,
                    "orphaned_percentage": 0.0,
                
}

            linked_defects = (
                self.session.query(Defect)
                .filter(Defect.github_user_story_number.isnot(None))
                .count()
            )

            # Count valid links
            valid_links = 0
            broken_links = 0

            for defect in (
                self.session.query(Defect)
                .filter(Defect.github_user_story_number.isnot(None))
                .all()
            ):
                user_story = (
                    self.session.query(UserStory)
                    .filter(
                        UserStory.github_issue_number == defect.github_user_story_number
                    )
                    .first()
                )

                if user_story:
                    valid_links += 1
                else:
                    broken_links += 1

            orphaned_defects = total_defects - linked_defects

            # Calculate percentages
            linked_percentage = (linked_defects / total_defects) * 100
            valid_link_percentage = (valid_links / total_defects) * 100
            broken_link_percentage = (broken_links / total_defects) * 100
            orphaned_percentage = (orphaned_defects / total_defects) * 100

            # Calculate health score (valid links are good, broken links are bad)
            health_score = valid_link_percentage - (
                broken_link_percentage * 2
            )  # Broken links penalized more
            health_score = max(0.0, min(100.0, health_score))  # Clamp to 0-100

            return {
    
                "total_defects": total_defects,
                "linked_defects": linked_defects,
                "valid_links": valid_links,
                "broken_links": broken_links,
                "orphaned_defects": orphaned_defects,
                "relationship_health_score": round(health_score,
    2),
                "linked_percentage": round(linked_percentage,
    2),
                "valid_link_percentage": round(valid_link_percentage,
    2),
                "broken_link_percentage": round(broken_link_percentage,
    2),
                "orphaned_percentage": round(orphaned_percentage,
    2),
            
}

        except Exception as e:
            logger.error(f"Error calculating health metrics: {e}")
            return {"error": str(e), "relationship_health_score": 0.0}

    def _find_potential_user_story_references(self, defect: Defect) -> List[str]:
        """
        Find potential user story references in defect title and description.

        Args:
            defect: The defect to analyze

        Returns:
            List of potential user story references found
        """
        import re

        references = []
        title = defect.title or ""
        description = defect.description or ""
        combined_text = f"{title} {description}"

        # Find US-XXXXX format references
        us_matches = re.findall(r"US-(\d{5})", combined_text, re.IGNORECASE)
        references.extend([f"US-{match}" for match in us_matches])

        # Find #issue-number format references
        issue_matches = re.findall(r"(?<!v)(?<!V)#(\d{1,5})(?!\.\d)", combined_text)
        references.extend(
            [f"#{match}" for match in issue_matches if 1 <= int(match) <= 99999]
        )

        return references

    def generate_validation_report(self) -> str:
        """
        Generate a human-readable validation report.

        Returns:
            Formatted validation report as string
        """
        validation_results = self.validate_all_relationships()
        health_metrics = self.get_relationship_health_metrics()

        report = []
        report.append("=== Defect-User Story Relationship Validation Report ===")
        report.append("")

        # Health metrics
        report.append("Overall Health Metrics:")
        report.append(
    (
    f"  Relationship Health Score: "
    f"{health_metrics.get('relationship_health_score',
    0
):.1f}%"
)
        )
        report.append(
            f"  Valid Links: {health_metrics.get('valid_link_percentage', 0):.1f}%"
        )
        report.append(
            f"  Broken Links: {health_metrics.get('broken_link_percentage', 0):.1f}%"
        )
        report.append(
            f"  Orphaned Defects: {health_metrics.get('orphaned_percentage', 0):.1f}%"
        )
        report.append("")

        # Detailed statistics
        report.append("Detailed Statistics:")
        report.append(f"  Total Defects: {validation_results['total_defects']}")
        report.append(f"  Linked Defects: {validation_results['linked_defects']}")
        report.append(f"  Valid Links: {validation_results['valid_links']}")
        report.append(f"  Broken Links: {validation_results['broken_links']}")
        report.append(f"  Orphaned Defects: {validation_results['orphaned_defects']}")
        report.append("")

        # Broken links details
        if validation_results["broken_link_details"]:
            report.append("Broken Links (Require Attention):")
            for broken in validation_results["broken_link_details"]:
                report.append(
                    f"  {broken['defect_id']}: {broken['defect_title'][:50]}..."
                )
                report.append(
                    f"    -> Broken reference to US #{broken['broken_reference']}"
                )
            report.append("")

        # Orphaned defects with potential references
        orphaned_with_refs = [
            d
            for d in validation_results["orphaned_defect_details"]
            if d["potential_references"]
        ]
        if orphaned_with_refs:
            report.append(
                "Orphaned Defects with Potential References (Could be linked):"
            )
            for orphaned in orphaned_with_refs:
                report.append(
                    f"  {orphaned['defect_id']}: {orphaned['defect_title'][:50]}..."
                )
                report.append(
                    f"    -> Potential references: {', '.join(orphaned['potential_references'])}"
                )
            report.append("")

        # Validation status
        if validation_results["validation_status"] == "error":
            report.append("Validation Errors:")
            for error in validation_results["validation_errors"]:
                report.append(f"  ERROR: {error}")
            report.append("")

        report.append("=== End of Report ===")

        return "\n".join(report)


# Convenience functions for direct use


def validate_all_defect_relationships() -> Dict[str, any]:
    """Convenience function to validate all defect relationships."""
    with DefectValidationService() as validator:
        return validator.validate_all_relationships()


def validate_defect_relationship(defect_id: str) -> Dict[str, any]:
    """Convenience function to validate a specific defect relationship."""
    with DefectValidationService() as validator:
        return validator.validate_defect_relationship(defect_id)


def get_defect_relationship_health() -> Dict[str, any]:
    """Convenience function to get relationship health metrics."""
    with DefectValidationService() as validator:
        return validator.get_relationship_health_metrics()


def generate_defect_validation_report() -> str:
    """Convenience function to generate a validation report."""
    with DefectValidationService() as validator:
        return validator.generate_validation_report()
