#!/usr/bin/env python3
"""
Unit tests for the Topic model.
"""

import unittest
from unittest.mock import MagicMock
from models.topic import Topic


class TestTopicModel(unittest.TestCase):
    """Test suite for the Topic model."""

    def setUp(self):
        """Set up mock data for tests."""
        self.topic_data = {
            'id': '123',
            'name': 'Science',
            'parent_id': None
        }
        self.topic = Topic(**self.topic_data)

    def test_topic_initialization(self):
        """Test that a Topic instance is initialized correctly."""
        self.assertEqual(self.topic.id, self.topic_data['id'])
        self.assertEqual(self.topic.name, self.topic_data['name'])
        self.assertEqual(self.topic.parent_id, self.topic_data['parent_id'])

    def test_str_representation(self):
        """Test the string representation of a Topic instance."""
        expected_str = "[Topic] (123) Name: Science, Parent ID: None"
        self.assertEqual(str(self.topic), expected_str)

    def test_repr_representation(self):
        """Test the detailed string representation (__repr__)."""
        expected_repr = (
            "Topic(id=123, name=Science, parent_id=None, "
            "created_at=None, updated_at=None)"
        )
        self.assertEqual(repr(self.topic), expected_repr)

    def test_relationships(self):
        """Test relationships (quizzes and parent)."""
        # Mock quizzes relationship
        mock_quizzes = [MagicMock()]
        self.topic.quizzes = mock_quizzes

        # Mock parent relationship
        mock_parent = MagicMock()
        self.topic.parent = mock_parent

        self.assertEqual(self.topic.quizzes, mock_quizzes)
        self.assertEqual(self.topic.parent, mock_parent)

    def test_hierarchy(self):
        """Test hierarchical structure with parent and subtopics."""
        parent_topic = Topic(id='456', name='Math', parent_id=None)
        child_topic = Topic(id='789', name='Algebra', parent_id='456')

        # Mock subtopics relationship
        parent_topic.subtopics = [child_topic]

        self.assertEqual(parent_topic.subtopics[0].name, 'Algebra')
        self.assertEqual(child_topic.parent_id, '456')


if __name__ == '__main__':
    unittest.main()
