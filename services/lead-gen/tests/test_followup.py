"""Tests for the follow-up manager."""

from src.outreach.followup import FollowUpManager


class TestFollowUpManager:
    def setup_method(self):
        self.fm = FollowUpManager()

    def test_should_followup_under_max(self):
        assert self.fm.should_followup(0) is True
        assert self.fm.should_followup(1) is True
        assert self.fm.should_followup(2) is True

    def test_should_not_followup_at_max(self):
        assert self.fm.should_followup(3) is False
        assert self.fm.should_followup(5) is False

    def test_fallback_message_first_attempt(self):
        msg = self.fm._fallback_message("Alice", "iPhone", 1)
        assert "Alice" in msg
        assert "iPhone" in msg
        assert "free diagnostic" in msg.lower() or "repair" in msg.lower()

    def test_fallback_message_second_attempt(self):
        msg = self.fm._fallback_message("Bob", "laptop", 2)
        assert "Bob" in msg
        assert "following up" in msg.lower()

    def test_fallback_message_final_attempt(self):
        msg = self.fm._fallback_message(None, None, 3)
        assert "Hi there" in msg
        assert "last" in msg.lower() or "no pressure" in msg.lower()
