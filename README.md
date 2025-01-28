# QuizyPal

QuizyPal is an interactive quiz application designed to provide an engaging platform for users to test and improve their knowledge. It allows users to take quizzes on various topics, track their progress, and receive feedback based on their performance. The app is built with a focus on providing an intuitive experience for both quiz takers and administrators.

## ACTUAL PRESENTATION AND DEMO VIDEO LINK: [here](https://drive.google.com/file/d/1dhgt9wKVBHR2YfcEM6GWkHNzILnitgg8/view?usp=sharing)
## PRESENTATION SLIDES LINK: [here](https://docs.google.com/presentation/d/1RfYoCvJAB9n9Qrr7CL_uwruBxHJwFKyGB4OTqlhvY1g/edit?usp=sharing)

### Installation Instructions


To get a local copy up and running, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AdwoaSerwah/QuizyPal.git
   ```

2. **Navigate to the project directory**:

   ```bash
   cd QuizyPal
   ```

3. **Install docker engine**:
   ```bash
    sudo apt update
    sudo apt install apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt update
    sudo apt install docker-ce
    ```

4. **Verify that Docker was installed correctly**:
   ```bash
   sudo docker --version
   ```

5. **Install Docker Compose**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

6. **Verify Docker Compose is installed**
```bash
docker-compose --version
```

7. **Start Docker after installation**
```bash
sudo systemctl start docker
```

8. **Enable Docker to start on boot**:
   If you want Docker to start automatically when your system boots
   ```bash
   sudo systemctl enable docker
   ```

9. **Set the MySQL credentials in docker-compose.yml file**
   Store the actual credentials in .env to protect sensitive info:

**In docker-compose.yml file:**
environment:
  MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
  MYSQL_DATABASE: ${MYSQL_DATABASE}
  MYSQL_USER: ${MYSQL_USER}
  MYSQL_PASSWORD: ${MYSQL_PASSWORD}

10. **In .env set the actual values**:
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=database_name # Example: quizypal_db
MYSQL_USER=user
MYSQL_PASSWORD=user_password

***Build the services (app and db) as per the configurations and start the containers for your app and MySQL database.***

**Option 1: you have to use sudo every time**:
```bash
sudo docker-compose up --build
```

**Option 2: Allows you to run Docker commands without sudo**:

**Add your user to the Docker group:**
```bash
sudo usermod -aG docker $USER
```

- Then log out and log back in (or restart your terminal session) for the changes to take effect OR
- run this to apply immediately (no logout or restart needed). 
```bash
newgrp docker
```
If you have MySQL installed locally and it's running,
you can stop it to free up the port or use another port.
```bash
sudo systemctl stop mysql
```

**Then run this again**
docker-compose up --build

OR If you want to keep your local MySQL service running and
avoid port conflicts, you can change the MySQL port in the
# docker-compose.yml file.
# For example, change the 3306 port to a different port (e.g., 3307)
# in the db service:

db:
  image: mysql:5.7
  container_name: quizypal_db
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_DATABASE: ${MYSQL_DATABASE}
    MYSQL_USER: ${MYSQL_USER}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}
  ports:
    - "3307:3306"  # Change this line to use a different local port (e.g., 3307)
  volumes:
    - quizypal_db_data:/var/lib/mysql

**Then run this again**
````bash
docker-compose up --build
```

**OR build the container**

```bash
   docker-compose build
```

**Then start the container**
```bash
docker-compose up
```

# To start the container and ensure everything is set up (including
# rebuilding images if necessary)
```bash
  docker-compose up
```

# To stop and remove containers, networks, and possibly volumes and
# images. (in case you need to rebuild or something)
docker-compose down

# Temporarily stops the running containers but does not remove/delete them
docker-compose stop

# Starts already created containers that were previously stopped
# without rebuilding or changing anything.
docker-compose start

# Restart the application service
docker-compose restart app

# Verify the Containers are Running
docker ps

**You can access the MySQL database from within the container using**:
```bash
docker exec -it quizypal_db mysql -u root -p
```

**Verify that Redis is working correctly:**
```bash
docker exec -it quizypal_redis redis-cli
```

**Monitor the logs for any errors or issues:**
```bash
docker logs quizypal_app
```

# Enter the Application Container
# Access the running container where your application and its
# dependencies are installed:
```bash
docker exec -it quizypal_app bash
```



## Database Setup

To set up the MySQL database for the Take-A-Bite project, follow these steps:

1. **Install MySQL**: Make sure you have MySQL installed on your machine. If you haven't installed it yet, refer to the [MySQL Installation Guide](https://dev.mysql.com/doc/refman/8.0/en/installing.html).

2. **Create the database and user** by running the following command in your terminal:

   You can either run the SQL commands directly or use the setup file:

   - **Option 1: Run the SQL commands directly**:

     ```bash
     mysql -u root -p  # Log into MySQL
     ```

     Then execute the following SQL commands:

     ```sql
     CREATE DATABASE IF NOT EXISTS take_a_bite_db;
     CREATE USER IF NOT EXISTS 'your_username'@'localhost' IDENTIFIED BY 'your_password';
     GRANT ALL PRIVILEGES ON `take_a_bite_db`.* TO 'your_username'@'localhost';
     FLUSH PRIVILEGES;
     ```

   - **Option 2: Use the setup file**:

     If you have a `setup_mysql_dev.sql` file, first, open the file in a text editor and modify the default values for the username and password:

     ```sql
     CREATE DATABASE IF NOT EXISTS take_a_bite_db;
     CREATE USER IF NOT EXISTS 'your_username'@'localhost' IDENTIFIED BY 'your_password';
     GRANT ALL PRIVILEGES ON `take_a_bite_db`.* TO 'your_username'@'localhost';
     FLUSH PRIVILEGES;
     ```

     After making the changes, you can execute the file directly:

     ```bash
     mysql -u root -p < setup_mysql_dev.sql
     ```

    **Or if you need to use sudo:**

     ```bash
     sudo mysql < setup_mysql_dev.sql
     ```

### Database Population

To populate the database with initial data, follow these steps:

1. **Run the Categories Script**:
   Open `categories.sh` and replace the placeholders (`your_username`, `your_password`) with your actual MySQL credentials. Then run the script:

   ```bash
   chmod +x categories.sh
   ./categories.sh

2. **Update the Menu Items Script**:
   Similarly, open menu_items.sh and replace the placeholders with your actual credentials. Before running the script, also replace the category ID placeholders (example, CATEGORY_ID_BREAKFAST) with the actual IDs created in the previous step.

3. **Run the Menu Items Script**:
   After updating the menu_items.sh, run the script:

   ```bash
   chmod +x menu_items.sh
   ./menu_items.sh
   ```

4. **Run the Locations Script**:
   Finally, open locations.sh, update it with your credentials, and run it:

   ```bash
   chmod +x locations.sh
   ./locations.sh
   ```

Notes
Make sure to replace your_username, your_password, and other placeholders with the actual details you created during the setup process.

Bash Environment: These instructions assume you are using a Unix-like environment (Linux, macOS, etc.) where bash is available. If you're on Windows, you may need to use Git Bash or Windows Subsystem for Linux (WSL).


## Environment Variables

**Create a `.env` file in the root directory of your project and populate it with the following variables**:

```plaintext
HBNB_ENV=dev
HBNB_MYSQL_USER=your_username_here
HBNB_MYSQL_PWD=your_password_here
HBNB_MYSQL_HOST=localhost
HBNB_MYSQL_DB=take_a_bite_db
HBNB_TYPE_STORAGE=db
DATABASE_URL=mysql+mysqldb://your_username_here:your_password_here@localhost/take_a_bite_db
HBNB_API_HOST=0.0.0.0
HBNB_API_PORT=5005

SECRET_KEY=your_secret_key_here

MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=your_default_email

PAYSTACK_SECRET_KEY=your_paystack_secret_key
```

**Generate the SECRET_KEY**
To generate a random secret key for your application, run the following command:

```bash
python secret_key.py
```
This will output a secret key that you should copy and paste into your .env file as the value for SECRET_KEY.

**Email Configuration**
Gmail’s SMTP server is what is being used.

Note: If you have two-step verification enabled for your Google account, you will need to generate an App Password to use as the MAIL_PASSWORD.

**Obtain Paystack API Keys**
1. Go to the Paystack website and sign up for an account if you
don't have one. Follow the instructions to obtain your public and secret keys.

2. Replace the placeholder your_paystack_secret_key in the .env file with your actual Paystack secret key.

3. In your static JavaScript file static/scripts/checkout.js, replace the following line with your actual Paystack public key:

```javascript
key: 'pk_test_3172601967078640096a6f10075e6537df112f15',
```

Important: Do not use your Paystack secret key in your client-side code (JavaScript). Only use the public key in the client-side code for security reasons.

Notes
The Paystack public key is safe to use in client-side code. The secret key should remain confidential and only be used in your server-side code (e.g., in API calls to Paystack).

### Run the Application:
Start your application using:
```bash
python3 -m api.v1.app
```

This will start the Flask application, and you can access it in your browser at http://127.0.0.1:5005.


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

For more detailed documentation and further tests, visit my postman collection [here](https://www.postman.com/research-geoscientist-64388512/my-workspace/collection/40764868-5a04296f-1ad7-45c7-8f32-69141777f7be?action=share&creator=40764868&active-environment=40764868-0a1a0347-6843-48c3-a938-74598e18dd24
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
