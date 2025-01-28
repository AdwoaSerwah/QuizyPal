# QuizyPal

QuizyPal is an interactive quiz application designed to provide an engaging platform for users to test and improve their knowledge. It allows users to take quizzes on various topics, track their progress, and receive feedback based on their performance. The app is built with a focus on providing an intuitive experience for both quiz takers and administrators.

## ACTUAL PRESENTATION AND DEMO VIDEO LINK: [here](https://drive.google.com/file/d/1dhgt9wKVBHR2YfcEM6GWkHNzILnitgg8/view?usp=sharing)
## PRESENTATION SLIDES LINK: [here](https://docs.google.com/presentation/d/1RfYoCvJAB9n9Qrr7CL_uwruBxHJwFKyGB4OTqlhvY1g/edit?usp=sharing)

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

## Features

- **User Registration & Authentication**
  - Register a new user
  - Login, logout, and session management with JWT tokens
  - Forgot password and password reset functionality
  - Managing refresh tokens to create new access tokens

- **Topic and Quiz Management**
  - Assigning quizzes to topics 
  - Create quizzes with titles, descriptions, and time limits
  - Create questions and answers maing sure to validate them
  - Add multiple choice questions and assign topics (if available)
  - REtrieve questions and answers only when quiz begins unless admins
  - Admin-only access to add/edit quiz data

- **Interactive Quiz Experience**
  - Start and stop quizzes
  - Track time taken and show results
  - Provide feedback based on performance

- **Admin Panel**
  - Manage quizzes, topics, questions, choices, results, user roles and answers
  - Restrict access to admin functionalities

- **Database Integration**
  - Store quizzes, user answers, and results in a database

## Tech Stack

- **Backend**: Python (Flask)
- **Database**: MySQL, Redis
- **Authentication**: JWT tokens

## API Documentation:

For more detailed documentation and further tests, visit the Postman collection [here](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24
)

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

## Contribution
Contributions are welcome! If you'd like to contribute to QuizyPal, please fork the repository and submit a pull request with your changes. Ensure that your code follows the project's conventions and passes all tests.

## License
QuizyPal is open-source software licensed under the MIT License. See the LICENSE file for more details
