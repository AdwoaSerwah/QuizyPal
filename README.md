# QuizyPal

QuizyPal is an interactive quiz application designed to provide an engaging platform for users to test and improve their knowledge. It allows users to take quizzes on various topics, track their progress, and receive feedback based on their performance. The app is built with a focus on providing an intuitive experience for both quiz takers and administrators.

## ACTUAL PRESENTATION AND DEMO VIDEO LINK: [here](https://drive.google.com/file/d/1dhgt9wKVBHR2YfcEM6GWkHNzILnitgg8/view?usp=sharing)
## PRESENTATION SLIDES LINK: [here](https://docs.google.com/presentation/d/1RfYoCvJAB9n9Qrr7CL_uwruBxHJwFKyGB4OTqlhvY1g/edit?usp=sharing)

## Features

- **User Registration & Authentication**
  - Register a new user
  - Login, logout, and session management with JWT tokens
  - Password reset functionality

- **Quiz Management**
  - Create quizzes with titles, descriptions, and time limits
  - Add multiple choice questions and assign topics (if available)
  - Admin-only access to add/edit quiz data

- **Interactive Quiz Experience**
  - Start and stop quizzes
  - Track time taken and show results
  - Provide feedback based on performance

- **Admin Panel**
  - Manage quizzes, topics, and user roles
  - Restrict access to admin functionalities

- **Database Integration**
  - Store quizzes, user answers, and results in a database

## Tech Stack

- **Backend**: Python (Flask)
- **Database**: MySQL
- **Authentication**: JWT tokens

## API Documentation

The backend of QuizyPal exposes a set of RESTful APIs for interacting with the platform. Key endpoints include:

### User Authentication
- `POST /api/v1/users`: Create a new user
- `POST /api/v1/login`: Log in and receive a JWT token
- `POST /api/v1/logout`: Log out and invalidate the JWT token
- `POST /api/v1/forgot-password`: Request a password reset
- `POST /api/v1/reset-password`: Reset the password

### Quiz Management
- `GET /api/v1/quizzes`: List all available quizzes
- `POST /api/v1/quizzes`: Create a new quiz (admin only)
- `GET /api/v1/quizzes/{quiz_id}`: Get details of a specific quiz
- `PUT /api/v1/quizzes/{quiz_id}`: Edit quiz details (admin only)
- `DELETE /api/v1/quizzes/{quiz_id}`: Delete a quiz (admin only)

### Topic Management
- `GET /api/v1/topics`: List all available topics
- `POST /api/v1/topics`: Create a new topic (admin only)

### Quiz Participation
- `POST /api/v1/start-quiz`: Start a quiz
- `POST /api/v1/stop-quiz`: Stop a quiz and view results

### Results and Feedback
- `GET api/v1/results/{quiz_id}`: View quiz results and feedback

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quizypal.git

## Contribution
Contributions are welcome! If you'd like to contribute to QuizyPal, please fork the repository and submit a pull request with your changes. Ensure that your code follows the project's conventions and passes all tests.

## License
QuizyPal is open-source software licensed under the MIT License. See the LICENSE file for more details
