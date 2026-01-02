"""Comment service for comment management operations.

Provides operations for:
- Adding comments to issues
- Listing comments for an issue
- Deleting comments
- Multi-line comment editing support

Source reference: /home/thomas/Workspace/glorious/src/glorious_agents/skills/issues/
"""

import logging

from dot_issues.adapters import UnitOfWork
from dot_issues.domain.entities import (
    Clock,
    Comment,
    IdentifierService,
)

logger = logging.getLogger(__name__)


class CommentService:
    """Service for comment management operations.

    Coordinates between repositories and enforces business rules.
    All operations use UnitOfWork for transaction management.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        id_service: IdentifierService,
        clock: Clock,
    ) -> None:
        """Initialize comment service.

        Args:
            uow: Unit of work for transaction management
            id_service: Service for generating unique identifiers
            clock: Time provider for timestamps
        """
        self.uow = uow
        self.id_service = id_service
        self.clock = clock

    def add_comment(
        self,
        issue_id: str,
        author: str,
        text: str,
    ) -> Comment | None:
        """Add a comment to an issue.

        Args:
            issue_id: Issue identifier
            author: Comment author username
            text: Comment text content

        Returns:
            Created comment if issue exists, None otherwise
        """
        logger.debug("Adding comment to issue: issue_id=%s, author=%s", issue_id, author)

        # Verify issue exists
        issue = self.uow.issues.get(issue_id)
        if not issue:
            logger.warning("Cannot add comment: issue not found: id=%s", issue_id)
            return None

        comment_id = self.id_service.generate("comment")
        now = self.clock.now()

        comment = Comment(
            id=comment_id,
            issue_id=issue_id,
            author=author,
            text=text,
            created_at=now,
            updated_at=now,
        )

        saved_comment = self.uow.comments.save(comment)
        logger.info(
            "Comment added: id=%s, issue_id=%s, author=%s",
            saved_comment.id,
            issue_id,
            author,
        )
        return saved_comment

    def list_comments(self, issue_id: str) -> list[Comment]:
        """List all comments for an issue.

        Args:
            issue_id: Issue identifier

        Returns:
            List of comments ordered by creation time
        """
        logger.debug("Listing comments for issue: issue_id=%s", issue_id)
        comments = self.uow.comments.list_by_issue(issue_id)
        logger.info("Found %d comments for issue: %s", len(comments), issue_id)
        return comments

    def get_comment(self, comment_id: str) -> Comment | None:
        """Get a comment by ID.

        Args:
            comment_id: Comment identifier

        Returns:
            Comment if found, None otherwise
        """
        logger.debug("Getting comment: id=%s", comment_id)
        return self.uow.comments.get(comment_id)

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment.

        Args:
            comment_id: Comment identifier

        Returns:
            True if deleted, False if not found
        """
        logger.debug("Deleting comment: id=%s", comment_id)

        # Get the comment to verify it exists and get issue_id
        comment = self.uow.comments.get(comment_id)
        if not comment:
            logger.warning("Comment not found for deletion: id=%s", comment_id)
            return False

        result = self.uow.comments.delete(comment_id)
        if result:
            logger.info("Comment deleted: id=%s, issue_id=%s", comment_id, comment.issue_id)
        return result

    def list_comments_by_author(self, author: str) -> list[Comment]:
        """List all comments by an author.

        Args:
            author: Author username

        Returns:
            List of comments by the author
        """
        logger.debug("Listing comments by author: author=%s", author)
        comments = self.uow.comments.list_by_author(author)
        logger.info("Found %d comments by author: %s", len(comments), author)
        return comments


__all__ = ["CommentService"]
