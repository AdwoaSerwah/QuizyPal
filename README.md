# QuizyPal

QuizyPal is ...

## Introduction

This project is deployed [here](https://adwoask.pythonanywhere.com/), and you can read the blog post about the project [here](https://medium.com/@lindseylinwood56/take-a-bite-revolutionizing-food-delivery-in-accra-62bf3848529f).

**Project timeline:** August 2, 2024 – September 24, 2024  
**Author:** [Adwoa Serwah](https://www.linkedin.com/in/adwoa-kyei-baffour-892490192)

I worked on both the backend and frontend, focusing on delivering a robust and user-friendly experience. My role involved:
- Building and managing database models using SQLAlchemy
- Developing Flask routes for data handling and payment processing
- Creating dynamic and responsive frontend pages using HTML5, CSS3, and JavaScript (with jQuery).

## Installation

### Prerequisites
- Python 3.10 installed
- MySQL installed and running
- pip (Python package installer)
- Git (for cloning the repository)

### Installation Instructions
Yet to.

## Files

### `models/`

- `base.py`: base of all models of the API - handle serialization to file
- `user.py`: user model

### `api/v1`

- `app.py`: entry point of the API
- `views/index.py`: basic endpoints of the API: `/status` and `/stats`
- `views/users.py`: all users endpoints


## Setup

```
$ pip3 install -r requirements.txt
```


## Run

```
$ API_HOST=0.0.0.0 API_PORT=5000 python3 -m api.v1.app
```


## Routes

- `GET /api/v1/status`: returns the status of the API
- `GET /api/v1/stats`: returns some stats of the API
- `GET /api/v1/users`: returns the list of users
- `GET /api/v1/users/:id`: returns an user based on the ID
- `DELETE /api/v1/users/:id`: deletes an user based on the ID
- `POST /api/v1/users`: creates a new user (JSON parameters: `email`, `password`, `last_name` (optional) and `first_name` (optional))
- `PUT /api/v1/users/:id`: updates an user based on the ID (JSON parameters: `last_name` and `first_name`)
