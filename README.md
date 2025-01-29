# QuizyPal

QuizyPal is an interactive quiz application designed to provide an engaging platform for users to test and improve their knowledge. It allows users to take quizzes on various topics, track their progress, and receive feedback based on their performance. The app is built with a focus on providing an intuitive experience for both quiz takers and administrators.

### ACTUAL PRESENTATION AND DEMO VIDEO LINK: [here](https://drive.google.com/file/d/1dhgt9wKVBHR2YfcEM6GWkHNzILnitgg8/view?usp=sharing)

### PRESENTATION SLIDES LINK: [here](https://docs.google.com/presentation/d/1RfYoCvJAB9n9Qrr7CL_uwruBxHJwFKyGB4OTqlhvY1g/edit?usp=sharing)

## Installation
**Note:** These instructions assume you are using a Unix-like environment (Linux, macOS, etc.) where bash is available. If you're on Windows, you may need to use Git Bash or Windows Subsystem for Linux (WSL).

To get a local copy up and running, follow these steps:

**Clone the repository**:
   ```bash
   git clone https://github.com/AdwoaSerwah/QuizyPal.git
   ```

**Navigate to the project directory**:

   ```bash
   cd QuizyPal
   ```

### Environment Variables

**Create a `.env` file in the root directory of your project and populate it with the following variables**:

```plaintext
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_DATABASE=your_database_name
DATABASE_PORT=3306
DATABASE_URL=mysql+mysqlconnector://your_mysql_user:your_mysql_password@your_database_host:3306/your_database_name
DATABASE_TEST_URL=mysql+mysqlconnector://your_mysql_user:your_mysql_password@your_database_host:3306/your_test_database_name

FLASK_APP=api/v1/app.py
FLASK_ENV=development

REDIS_HOST=quizypal_redis
REDIS_PORT=6379
REDIS_URL=redis://quizypal_redis:6379/0  # Matches the 'redis' service in docker-compose

PYTHONPATH=/app

# STORAGE_TYPE=db
API_HOST=0.0.0.0
API_PORT=5000

SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

MAIL_USERNAME=your_email_address
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email_address
```

#### Generating SECRET_KEY and JWT_SECRET_KEY
To generate a random secret key for your application, run the following command:
```bash
./secret_key_generator.py
```
This will output a secret key that you should copy and paste into your .env file as the value for SECRET_KEY.
Now run the same script again to generate another secret_key for the JWT_SECRET_KEY

#### Email Configuration
Gmail’s SMTP server is what is being used.

**Note:** If you have two-step verification enabled for your Google account, you will need to generate an App Password to use as the MAIL_PASSWORD.


### Docker and docker-compose setup
**Install docker engine**:
```bash
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce
```

**Verify that Docker was installed correctly**:
```bash
sudo docker --version
```

**Install Docker Compose**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Verify Docker Compose is installed**
```bash
docker-compose --version
```

**Start Docker after installation**
```bash
sudo systemctl start docker
```

**Enable Docker to start on boot**:
If you want Docker to start automatically when your system boots
```bash
sudo systemctl enable docker
```

**Build the services (app and db) as per the configurations and start the containers for your app and MySQL database.**

**Option 1: you have to use sudo every time**:
```bash
sudo docker-compose up --build
```

**Option 2: Allows you to run Docker commands without sudo**:

**Add your user to the Docker group:**
```bash
sudo usermod -aG docker $USER
```
Then log out and log back in (or restart your terminal session) for the changes to take effect
*OR*
Run this to apply immediately (no logout or restart needed). 
```bash
newgrp docker
```
**If you have MySQL installed locally and it's running, you can either stop it to free up the port (option 1):**
```bash
sudo systemctl stop mysql
```
**Then run this again**
```bash
docker-compose up --build
```
*OR*

**If you want to keep your local MySQL service running and avoid port conflicts, you can change the MySQL port in the docker-compose.yml file. For example, change the 3306 port to a different port (e.g., 3307) in the db service:**
```plaintext
db:
  image: mysql:5.7
  container_name: quizypal_db
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_DATABASE: ${MYSQL_DATABASE}
    MYSQL_USER: ${MYSQL_USER}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}
  ports:
    - "3307:3306"  # Change this line to use a different local port (e.g. I have changed it from 3306 to 3307)
  volumes:
    - quizypal_db_data:/var/lib/mysql
```

**Then run this again**
```bash
docker-compose up --build
```

#### Other Useful Commands: ####

**To stop and remove containers, networks, and possibly volumes and images:**
```bash
docker-compose down
```

**Temporarily stop the running containers:**
```bash
docker-compose stop
```

**Start already created containers that were previously stopped**
```bash
docker-compose start
```

**Restart the application service:**
```bash
docker-compose restart app
```

**Verify the Containers are Running**
```bash
docker ps
```

**Verify that Redis is working correctly:**
```bash
docker exec -it quizypal_redis redis-cli
```

### Database Setup
The data base will be set up with the docker. The init-scripts/grant_privileges.sh has been added to the docker-compose.yml to grant all privileges to the user created during the docker setup.

**You can run the grant_privileges.sh again if it has not been set up automatically by:**
```bash
./grant_privileges.sh
```

### Database Population
To add data to your database tables follow the steps below.
**Access the running container where your application and its dependencies are installed:**
```bash
docker exec -it quizypal_app bash
```

**Then run the insert_data.py**:
```bash
./insert_data.py
```
**Note:**  You can change or add more to the insert_data.py but make sure at least one user's role is set to "admin" so you can send requests in the admin only routes.

**You can access the MySQL database from within the container using to verify and query the data inserted**:
```bash
docker exec -it quizypal_db mysql -u root -p
```

## Usage

### Base URL
The base URL for the API is `http://localhost:5000/api/v1`.

### Authentication
Most routes require JWT token-based authentication. Include the JWT token in the `Authorization` header as follows:

Authorization: Bearer &lt;your-token&gt;

### Making Requests
You can interact with the API using tools like Postman or `curl`.

Here’s an example of making a `GET` request using `curl`:

```bash
curl -X GET http://localhost:5000/api/v1/topics
```

For more details on the available routes, refer to the [API Endpoints](#api-endpoints) section.

## Features

- **User Registration & Authentication**
  - Register a new user
  - Login, logout, and session management with JWT tokens
  - Forgot password and password reset functionality
  - Managing refresh tokens to create new access tokens

- **Topic and Quiz Management**
  - Assigning quizzes to topics 
  - Create quizzes with titles, descriptions, and time limits
  - Add multiple choice questions and assign topics (if available)
  - Retrieve topics, quizzes and quizzes under topics specified
  - Retrieve questions and answers only when quiz begins unless admins
  - Admin-only access to add/edit quiz data

- **Interactive Quiz Experience**
  - Start and stop quizzes
  - Track time taken and show results
  - Provide feedback based on performance

- **Admin Panel**
  - Manage quizzes, topics, questions, choices, results, user roles and answers
  - Restrict access to admin functionalities

- **Database Integration**
  - Store users, refresh tokens, topics, quizzes, questions, choices, user answers, and results in a database

## API Endpoints

For a more detailed documentation and to test out the routes, visit the Postman collection [here](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24
)
**Note:** All routes are prefixed with `/api/v1`. Please ensure to include this prefix in your requests. For example, to log in, the route will be `/api/v1/login`.

### Authentication
- **POST /login**: Authenticates a user, generates access and refresh tokens, and stores the refresh token in the database and Redis.
- **POST /logout**: Logs out a user by invalidating the refresh token, blacklisting it in Redis, and marking it as expired in the database.

### Password Management
- **POST /forgot-password**: Sends a password reset token to the user's email if the email exists in the system.
- **POST /reset-password/<token>**: Resets the user's password using a valid reset token.

### User Management

- **GET /users**: Retrieves all users, with optional pagination (`page` and `page_size`).
    - **Query Parameters**:
        - `page`: The page number for pagination (default: 1).
        - `page_size`: The number of users per page (default: 10).
    - **Response**: A JSON array of all user objects.

- **GET /users/:id**: Retrieves a specific user by their `user_id`.
    - **Parameters**:
        - `user_id`: The unique identifier for the user.
    - **Response**: A JSON object representing the user, or a 404 error if the user is not found.

- **GET /users/:id/results**: Retrieves all results for a specific user or quiz results if `quiz_id` is provided.
    - **Parameters**:
        - `user_id`: The unique identifier for the user.
        - `quiz_id` (optional): The unique identifier for the quiz to filter results by.
    - **Response**: A JSON array of results for the user.

- **GET /users/:id/user-answers**: Retrieves all user answers for a specific user or user answers for a specific result if `result_id` is provided.
    - **Parameters**:
        - `user_id`: The unique identifier for the user.
        - `result_id` (optional): The unique identifier for the result to filter answers by.
        - `quiz_id` (optional): The unique identifier for the quiz to filter answers by.
    - **Response**: A JSON array of user answers.

- **DELETE /users/:id**: Deletes a user by their `user_id`.
    - **Parameters**:
        - `user_id`: The unique identifier for the user to be deleted.
    - **Response**: A JSON message confirming the deletion, or an error message if the user cannot be deleted.

- **POST /users**: Creates a new user.
    - **Request Body**:
        - `first_name`: The user's first name.
        - `last_name`: The user's last name.
        - `username`: The user's username.
        - `email`: The user's email address.
        - `password`: The user's password.
        - `role` (optional): The user's role (default: `user`).
    - **Response**: A JSON message with the created user object.

- **PUT /users/:id**: Updates a user's information.
    - **Parameters**:
        - `user_id`: The unique identifier for the user to be updated.
    - **Request Body** (optional fields):
        - `first_name`
        - `last_name`
        - `username`
        - `email`
        - `password`
        - `role` (only for admins)
    - **Response**: A JSON message with the updated user object or an error message.

### Refresh Tokens Management

- **GET /api/v1/refresh-tokens**:  
  Retrieves all refresh tokens with pagination.  
  - **Query Parameters**:
    - `page`: The page number for pagination (default: `1`).
    - `page_size`: The number of refresh tokens per page (default: `10`).
  - **Response**: A JSON array of refresh token objects.

- **GET /api/v1/refresh-tokens/:id**:  
  Retrieves a specific refresh token by its `refresh_token_id`.  
  - **Parameters**:
    - `refresh_token_id`: The unique identifier for the refresh token.
  - **Response**: A JSON object representing the refresh token, or a 404 error if the token is not found.

- **DELETE /api/v1/refresh-tokens/:id**:  
  Deletes the specified refresh token, invalidates it in Redis, and removes it from the database.  
  - **Parameters**:
    - `refresh_token_id`: The unique identifier for the refresh token.
  - **Response**: A JSON message confirming the deletion.

- **POST /api/v1/refresh-tokens**:  
  Refreshes the access token and the refresh token, and rotates them.  
  - **Request Body**:
    - `token_id`: The unique identifier for the refresh token to refresh.
  - **Response**: A JSON object containing the new access token and refresh token.

- **PUT /api/v1/refresh-tokens/:id**:  
  Updates the status of the specified refresh token (reverses revocation/expiration).  
  - **Parameters**:
    - `refresh_token_id`: The unique identifier for the refresh token.
  - **Request Body**:
    - `is_revoked`: Boolean value to indicate whether the refresh token should be revoked.
  - **Response**: A JSON message confirming the update, with the updated refresh token object.

### Topic Management

- **GET /topics**: Retrieves all topics with optional pagination.
    - **Query Parameters**:
        - `page`: The page number for pagination (default: 1).
        - `page_size`: The number of topics per page (default: 10).
    - **Response**: A JSON array of all topic objects.

- **GET /topics/:id**: Retrieves a specific topic by its `topic_id`.
    - **Parameters**:
        - `topic_id`: The unique identifier for the topic.
    - **Response**: A JSON object representing the topic, or a 404 error if the topic is not found.

- **GET /topics/name/:topic_name**: Retrieves a specific topic by its name.
    - **Parameters**:
        - `topic_name`: The name of the topic.
    - **Response**: A JSON object representing the topic, or a 404 error if the topic is not found.

- **GET /topics/:id/quizzes**: Retrieves all quizzes associated with a specific topic.
    - **Parameters**:
        - `topic_id`: The unique identifier for the topic.
    - **Response**: A JSON array of quizzes associated with the topic, or a 404 error if the topic is not found.

- **POST /topics**: Creates a new topic.
    - **Request Body**:
        - `name`: The name of the topic.
        - `parent_id` (optional): The ID of the parent topic.
    - **Response**: A JSON message with the created topic object.

- **PUT /topics/:id**: Updates an existing topic.
    - **Parameters**:
        - `topic_id`: The unique identifier for the topic.
    - **Request Body** (optional fields):
        - `name`: The name of the topic.
        - `parent_id`: The ID of the parent topic.
    - **Response**: A JSON message with the updated topic object.

- **DELETE /topics/:id**: Deletes a topic by its `topic_id`.
    - **Parameters**:
        - `topic_id`: The unique identifier for the topic to be deleted.
    - **Response**: A JSON message confirming the deletion, or an error message if the topic cannot be deleted.

### Quiz Management

- **GET /quizzes**: Retrieves all quizzes with optional pagination.
    - **Query Parameters**:
        - `page`: The page number for pagination (default: 1).
        - `page_size`: The number of quizzes per page (default: 10).
    - **Response**:
        - `page`: Current page number.
        - `page_size`: Number of items per page.
        - `quizzes`: List of quizzes for the current page.
        - `next_page`: Next page number, if available.
        - `prev_page`: Previous page number, if available.
        - `total_pages`: Total number of pages.

- **GET /quizzes/:id**: Retrieves a specific quiz by its `quiz_id`.
    - **Parameters**:
        - `quiz_id`: The unique identifier for the quiz.
    - **Response**: A JSON object representing the quiz, or a 404 error if the quiz is not found.

- **GET /quizzes/title**: Error handler for missing quiz title.
    - **Response**: 400 error with message "Quiz title is required."

- **GET /quizzes/title/:quiz_title**: Retrieves a specific quiz by its title.
    - **Parameters**:
        - `quiz_title`: The title of the quiz.
    - **Response**: A JSON object representing the quiz, or a 404 error if the quiz is not found.

- **GET /quizzes/:id/questions**: Retrieves all questions for a specific quiz, or a specific question if `question_id` is provided.
    - **Parameters**:
        - `quiz_id`: The unique identifier for the quiz.
        - `question_id` (optional): The unique identifier for a specific question.
    - **Response**: A JSON object containing a list of questions or a specific question, if found.

- **GET /quizzes/:id/questions-and-choices**: Retrieves all questions and their choices for a specific quiz, or a specific question and its choices if `question_id` is provided.
    - **Parameters**:
        - `quiz_id`: The unique identifier for the quiz.
        - `question_id` (optional): The unique identifier for a specific question.
    - **Response**: A JSON object containing a list of questions and their choices, or a specific question with choices.

- **DELETE /quizzes/:id**: Deletes a specific quiz by its `quiz_id`.
    - **Parameters**:
        - `quiz_id`: The unique identifier for the quiz to be deleted.
    - **Response**: A JSON message confirming the deletion, or a 404 error if the quiz is not found.

- **POST /quizzes**: Creates a new quiz.
    - **Request Body**:
        - `title`: The title of the quiz (must be unique).
        - `description` (optional): A brief description of the quiz.
        - `time_limit`: The time limit for the quiz in seconds.
        - `topic_id` (optional): The ID of the topic associated with the quiz.
    - **Response**: A JSON object representing the created quiz.

- **PUT /quizzes/:id**: Updates an existing quiz.
    - **Parameters**:
        - `quiz_id`: The unique identifier for the quiz to update.
    - **Request Body** (optional fields):
        - `title`: The new title of the quiz.
        - `description`: The new description of the quiz.
        - `time_limit`: The new time limit for the quiz in seconds.
        - `topic_id`: The new topic ID associated with the quiz.
    - **Response**: A JSON object representing the updated quiz.

- **POST /quizzes/complete**: Creates a complete quiz with optional topic, quiz details, questions, and choices.
    - **Request Body**:
        - `topic`: (optional) Topic details, such as `name` and `parent_id`.
        - `quiz`: Quiz details such as `title`, `description`, and `time_limit`.
        - `questions`: List of questions with their details like `question_text`, `allow_multiple_answers`, and `choices`.
    - **Response**: A JSON object representing the created quiz.

- **POST /start-quiz**: Starts a quiz attempt for a user.
    - **Request Body**:
        - `quiz_id`: The ID of the quiz to start.
    - **Response**: A JSON object representing the quiz attempt.

- **POST /stop-quiz**: Ends the quiz, updates the necessary result details (minus score calculations).
    - **Request Body**:
        - `result_id`: The ID of the quiz result to stop.
    - **Response**: A JSON object indicating the quiz has been stopped.

### Question Management

- **GET /questions**: Get all questions with pagination.
    - **Query Parameters**:
        - `page` (int, optional): The page number (default is 1).
        - `page_size` (int, optional): The number of items per page (default is 10).
    - **Response**: A JSON object containing:
        - `page`: Current page number.
        - `page_size`: Number of items in the current page.
        - `questions`: List of questions for the current page.
        - `next_page`: Next page number, if available.
        - `prev_page`: Previous page number, if available.
        - `total_pages`: Total number of pages.

- **GET /questions/:id**: Get a specific question by their question_id.
    - **Parameters**:
        - `question_id`: The unique identifier for the question.
    - **Response**: A JSON object representing the question if found, or a 404 error if not.

- **GET /questions/:id/choices**: Get all choices for a specific question.
    - **Parameters**:
        - `question_id`: The unique identifier for the question whose choices are to be retrieved.
    - **Response**: A JSON object containing a list of choices for the specified question.

- **DELETE /questions/:id**: Delete a specific question by their question_id.
    - **Parameters**:
        - `question_id`: The unique identifier of the question to be deleted.
    - **Response**: A JSON object indicating whether the deletion was successful or an error message if the question does not exist or the user is unauthorized.

- **POST /questions**: Create a new question.
    - **Request Body**:
        - `title`: The title of the question.
        - `description`: A brief description of the question.
        - `quiz_id`: The ID of the quiz to which the question belongs.
        - `choices`: List of choices associated with the question.
    - **Response**: A JSON object representing the created question.

- **PUT /questions/:id**: Update an existing question.
    - **Parameters**:
        - `question_id`: The unique identifier of the question to update.
    - **Request Body** (optional fields):
        - `title`: The new title of the question.
        - `description`: The new description of the question.
        - `quiz_id`: The new quiz ID to which the question should belong.
        - `choices`: Updated list of choices for the question.
    - **Response**: A JSON object representing the updated question.

### Choice Management

- **GET /choices**: Retrieves all choices with pagination.
    - **Query Parameters**:
        - `page`: The page number (default is 1).
        - `page_size`: The number of items per page (default is 10).
    - **Response**: A JSON object containing:
        - `page`: Current page number.
        - `page_size`: Number of items in the current page.
        - `choices`: List of choices for the current page.
        - `next_page`: Next page number, if available.
        - `prev_page`: Previous page number, if available.
        - `total_pages`: Total number of pages.

- **GET /choices/:id**: Retrieves a specific choice by its ID.
    - **Parameters**:
        - `choice_id`: The unique identifier for the choice.
    - **Response**: A JSON object representing the choice if found. If not found, a 404 error is returned.

- **DELETE /choices/:id**: Deletes a specific choice by its ID.
    - **Parameters**:
        - `choice_id`: The unique identifier for the choice.
    - **Response**: A JSON object indicating whether the deletion was successful. Returns an error if the choice does not exist or is unauthorized.

- **POST /choices**: Creates new choices.
    - **Request Body**:
        - `choices`: A list of choices to be created, where each choice is represented as a dictionary.
    - **Response**: A JSON object representing the created choices or error messages for invalid input.

- **PUT /choices/:id**: Updates an existing choice.
    - **Parameters**:
        - `choice_id`: The unique identifier of the choice to update.
    - **Request Body**:
        - The choice data to be updated.
    - **Response**: A JSON object representing the updated choice or error messages for invalid input.

### User Answer Management

- **GET /user-answers**: Retrieves all user answers with pagination.
    - **Query Parameters**:
        - `page`: The page number (default is 1).
        - `page_size`: The number of items per page (default is 10).
    - **Response**: A JSON object containing:
        - `page`: Current page number.
        - `page_size`: Number of items in the current page.
        - `user_answers`: List of user answers for the current page.
        - `next_page`: Next page number, if available.
        - `prev_page`: Previous page number, if available.
        - `total_pages`: Total number of pages.

- **GET /user-answers/:id**: Retrieves a specific user answer by its ID.
    - **Parameters**:
        - `user_answer_id`: The unique identifier for the user answer.
    - **Response**: A JSON object representing the user answer if found. If not found, a 404 error is returned.

- **DELETE /user-answers/:id**: Deletes a specific user answer by its ID.
    - **Parameters**:
        - `user_answer_id`: The unique identifier for the user answer.
    - **Response**: A JSON object indicating whether the deletion was successful. If the user answer does not exist, a 404 error is returned.

- **POST /user-answers**: Creates new user answers.
    - **Request Body**:
        - The data for the user answer(s).
    - **Response**: A JSON object representing the created user answer(s) or error messages for invalid input.

- **PUT /user-answers/:id**: Updates an existing user answer.
    - **Parameters**:
        - `user_answer_id`: The unique identifier of the user answer to update.
    - **Request Body**:
        - The updated data for the user answer.
    - **Response**: A JSON object representing the updated user answer or error messages for invalid input.

### Results and Feedback Management

- **GET /results**: Retrieves all results with pagination.
    - **Query Parameters**:
        - `page`: The page number (default is 1).
        - `page_size`: The number of items per page (default is 10).
    - **Response**: A JSON object containing:
        - `page`: Current page number.
        - `page_size`: Number of items in the current page.
        - `results`: List of results for the current page.
        - `next_page`: Next page number, if available.
        - `prev_page`: Previous page number, if available.
        - `total_pages`: Total number of pages.

- **GET /results/:id**: Retrieves a specific result by its ID.
    - **Parameters**:
        - `result_id`: The unique identifier for the result.
    - **Response**: A JSON object representing the result if found. If not found, a 404 error is returned.

- **DELETE /results/:id**: Deletes a specific result by its ID.
    - **Parameters**:
        - `result_id`: The unique identifier for the result.
    - **Response**: A JSON object indicating whether the deletion was successful. If the result does not exist, a 404 error is returned.

- **POST /results**: Creates a new result.
    - **Request Body**:
        - The data for the result.
    - **Response**: A JSON object representing the created result or error messages for invalid input.

- **PUT /results/:id**: Updates an existing result.
    - **Parameters**:
        - `result_id`: The unique identifier of the result to update.
    - **Request Body**:
        - The updated data for the result.
    - **Response**: A JSON object representing the updated result or error messages for invalid input.

- **GET /results/:result_id/feedback**: Retrieves feedback for a completed quiz based on the user's answers and overall performance.
    - **Parameters**:
        - `result_id`: The unique identifier of the result (quiz attempt).
    - **Response**: A JSON object containing the quiz feedback, including:
        - `quiz_title`: The title of the quiz.
        - `feedback`: The feedback based on the quiz performance.
        - `date`: The date the result was created.
        - `completion_time`: Time taken to complete the quiz.
        - `time_limit`: Time limit for the quiz.
        - `status`: The status of the quiz (e.g., completed, timed-out).
        - `correct_answers`: Number of correct answers.
        - `incorrect_answers`: Number of incorrect answers.
        - `no_answers`: Number of unanswered questions.
        - `total_questions`: Total number of questions.
        - `percentage`: The score percentage.
        - `answers`: A list of detailed answers, including question text, user choice, and correct choice.

## Postman Collection Instructions

- **For Documentation Only**: If you're only interested in **reading the documentation** for the API routes, you can directly view the collection [here](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24).

- **For Testing the Routes**: If you want to **send API requests test the routes** using Postman, read the setup instructions below before clicking the link:
---
### Setup Instructions for Testing with Postman  

#### 1. Follow the Installation Guide  
Before testing the routes in Postman, make sure to **complete the steps in the [**Installation**](#installation) section** and **start the backend** using `docker-compose up`. This ensures the API is running locally and ready for requests.

#### 2. Fork the Collection  
- Open the [Postman collection link](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24).
- **Log in to your Postman account** if you haven’t already.  
- **Fork** to copy the collection into your own workspace.

**Note:** You may need to use the **Postman Desktop App** instead of the web version. You can download it from [Postman’s official website](https://www.postman.com/downloads/).

#### 3. Set Up the Environment  
- Go to **Manage Environments** in Postman (gear icon in the top-right corner).
- Create a **new environment** in Postman named **"QuizyPal API"**.
- Add the `base_url` variable: Set this to your running API base URL (e.g., `http://localhost:5000/`).

After logging in with the `/login` route, add the following variables:
  - `access_token`: Stores your authentication token.
  - `refresh_token`: Stores the refresh token for token renewal.
  - `token_id`: Stores the token ID, which is also needed for token renewal.

- **Make sure to save and select the "QuizyPal API" environment (set it to active) before running requests**.

**Note**: For some routes, you may encounter placeholders like `{{email}}` in the request. You can either:
- Add `email` to your environment variables and set its value there, or
- Replace `{{email}}` in the request with the actual email address you want to use.

#### 4. Accessing Routes

Once your environment is set up, you can start running requests in the collection. Remember to set your QuizyPal API environment to active before sending requests.

##### ✅ Routes That Do Not Require Authorization  
You can send requests to public routes like:  
- `GET /topics`  
- `GET /quizzes`  
- `GET /quiz/:id`  

##### 🔑 Routes That Require Authentication
You need to be logged in to access user-specific routes like:
- `PUT /users/:id`  
- `POST /user-answers`  

##### 🛑 Admin-Controlled Routes  
- To access routes that require **admin privileges**, you must log in as the admin user created after running `insert-data.py`during the **[installation](#installation) process**. 
- These routes **will return error** unless you log in as the admin.
- The admin-only routes include `DELETE /quizzes/:id` and `PUT /quizzes/:id`

**Notes**
- For routes that require **IDs** (such as `quiz_id`, `user_id`, `topic_id`, etc.), you must use a **valid ID** from the database.

- Send a **GET request** to retrieve all records of that model (e.g., to get a valid user id, send a request to `GET /users` to retrieve all users and copy one of the IDs returned to use as the `user_id`).

Now, your Postman setup is complete, and you can start testing the API! 🚀

- **[QuizyPal API Postman Collection](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24)**.

## Tech Stack  

- **Backend**: Python (Flask, Flask-SQLAlchemy)  
- **Database**: MySQL (Flask-SQLAlchemy as ORM), Redis (for caching)  
- **Authentication**: JWT (Flask-JWT-Extended)  
- **Email Service**: Flask-Mail  
- **Testing & Debugging**: Postman  
- **Version Control**: Git & GitHub  

## Contribution

Contributions are welcome! If you'd like to contribute to QuizyPal, please fork the repository and submit a pull request with your changes. Ensure that your code follows the project's conventions and passes all tests.

## License

QuizyPal is open-source software licensed under the MIT License. See the LICENSE file for more details
