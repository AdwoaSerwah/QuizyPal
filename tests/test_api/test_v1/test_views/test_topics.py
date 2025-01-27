import unittest
from flask import Flask, request, jsonify
from unittest.mock import patch

# Define your Flask app directly here
app = Flask(__name__)

# A simple route to test - Create a topic
@app.route('/create-topic', methods=['POST'])
def create_topic():
    data = request.get_json()
    topic_name = data.get('name')
    if topic_name:
        return jsonify({'message': f'Topic {topic_name} created'}), 200
    return jsonify({'error': 'Topic name is required'}), 400


# Get all topics
@app.route('/topics', methods=['GET'])
def get_topics():
    topics = [{'id': 1, 'name': 'Topic 1'}, {'id': 2, 'name': 'Topic 2'}]
    return jsonify(topics), 200


# Get a specific topic by ID
@app.route('/topics/<int:topic_id>', methods=['GET'])
def get_topic_by_id(topic_id):
    topic = {'id': topic_id, 'name': f'Topic {topic_id}'}
    return jsonify(topic), 200


# Delete a topic
@app.route('/delete-topic/<int:topic_id>', methods=['DELETE'])
def delete_topic(topic_id):
    return jsonify({'message': f'Topic {topic_id} deleted'}), 200


# Update a topic
@app.route('/update-topic/<int:topic_id>', methods=['PUT'])
def update_topic(topic_id):
    data = request.get_json()
    topic_name = data.get('name')
    if topic_name:
        return jsonify({'message': f'Topic {topic_id} updated to {topic_name}'}), 200
    return jsonify({'error': 'Topic name is required'}), 400


# Tests
class TestTopicRoutes(unittest.TestCase):

    def setUp(self):
        """Set up the test client for Flask."""
        self.client = app.test_client()

    def test_create_topic_success(self):
        """Test creating a topic successfully."""
        request_data = {'name': 'New Topic'}
        with app.test_request_context():
            with patch('flask.request.get_json', return_value=request_data):
                response = self.client.post('/create-topic', json=request_data)
                self.assertEqual(response.status_code, 200)
                self.assertIn('Topic New Topic created', response.get_data(as_text=True))

    def test_create_topic_missing_name(self):
        """Test creating a topic without a name."""
        request_data = {}
        with app.test_request_context():
            with patch('flask.request.get_json', return_value=request_data):
                response = self.client.post('/create-topic', json=request_data)
                self.assertEqual(response.status_code, 400)
                self.assertIn('Topic name is required', response.get_data(as_text=True))

    def test_get_topics(self):
        """Test retrieving all topics."""
        with app.test_request_context():
            response = self.client.get('/topics')
            self.assertEqual(response.status_code, 200)
            self.assertIn('Topic 1', response.get_data(as_text=True))
            self.assertIn('Topic 2', response.get_data(as_text=True))

    def test_get_topic_by_id(self):
        """Test retrieving a specific topic by ID."""
        topic_id = 1
        with app.test_request_context():
            response = self.client.get(f'/topics/{topic_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'Topic {topic_id}', response.get_data(as_text=True))

    def test_delete_topic(self):
        """Test deleting a topic."""
        topic_id = 1
        with app.test_request_context():
            response = self.client.delete(f'/delete-topic/{topic_id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'Topic {topic_id} deleted', response.get_data(as_text=True))

    def test_update_topic_success(self):
        """Test updating a topic successfully."""
        topic_id = 1
        request_data = {'name': 'Updated Topic'}
        with app.test_request_context():
            with patch('flask.request.get_json', return_value=request_data):
                response = self.client.put(f'/update-topic/{topic_id}', json=request_data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'Topic {topic_id} updated to Updated Topic', response.get_data(as_text=True))

    def test_update_topic_missing_name(self):
        """Test updating a topic without a name."""
        topic_id = 1
        request_data = {}
        with app.test_request_context():
            with patch('flask.request.get_json', return_value=request_data):
                response = self.client.put(f'/update-topic/{topic_id}', json=request_data)
                self.assertEqual(response.status_code, 400)
                self.assertIn('Topic name is required', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
