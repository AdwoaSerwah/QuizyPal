#!/usr/bin/env python3
"""
Adds rows to quizypal_db database tables
"""
from models import storage
from models.user import User, Role
from models.topic import Topic
from models.quiz import Quiz
from models.question import Question
from models.choice import Choice
from models.result import Result, QuizSessionStatus
from models.user_answer import UserAnswer
from datetime import datetime, timezone
from typing import Optional


def add_user(first_name,
             last_name,
             username,
             email,
             password,
             role=Role.USER,
             password_reset_token=None,
             token_expires_at=None):
    """Adds a new user to the database"""
    username_exists = storage.get_by_value(User, 'username', username)
    email_exists = storage.get_by_value(User, 'email', email)

    if username_exists:
        print(f"Username '{username}' already exists!")
        return username_exists

    if email_exists:
        print(f"Email '{email}' already exists!")
        return email_exists

    # Create the user
    user1 = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password,
        role=role,
        password_reset_token=password_reset_token,
        token_expires_at=token_expires_at
    )

    user1.save()

    # Print the created user details
    print(f"User {user1.username} created with role as {user1.role.value}")


def add_topic(name, parent=None):
    """
    Adds topics and subtopics to the database.
    """
    topic_name = storage.get_by_value(Topic, "name", name)

    if topic_name:
        print(f"Topic '{topic_name.name}' exists already!")
        return None

    name1 = Topic(name=name, parent=parent)
    name1.save()
    print(f"{name1.name} added!")

    return name1


def add_quiz(title, description, time_limit, topic_name=None):
    """
    Adds a quiz to the specified topic, or creates it without
    a topic if no topic is provided.
    """
    quiz_title = storage.get_by_value(Quiz, "title", title)
    if quiz_title:
        print(f"{title} already exists!")
        return None

    if topic_name:
        # Get the topic by name, if provided
        topic = storage.get_by_value(Topic, "name", topic_name)

        if not topic:
            print(f"Topic '{topic_name}' does not exist!")
            return None

    # Create the quiz
    quiz = Quiz(
        title=title,
        description=description,
        time_limit=time_limit,
        # Assign topic_id if topic is found, else None
        topic_id=topic.id if topic else None
    )
    quiz.save()
    print(
        f"Quiz '{quiz.title}' added"
        f"{' under topic ' + topic.name if topic else ''}."
    )
    return quiz


def get_next_order_number(model, parent_id, parent_field):
    """
    Returns the next order number for a specific model by
    counting the number of objects associated with the given
    parent_id using the specified parent_field.

    Args:
        model (Type[Base]): The model to count objects for (e.g., Question,
                            Choice, etc.).
        parent_id (str): The ID of the parent entity (e.g., quiz_id for
                         questions, question_id for choices).
        parent_field (str): The field that references the parent entity
                            (e.g., 'quiz_id' for Question, 'question_id'
                            for Choice).

    Returns:
        int: The next order number.
    """
    data = storage.get_by_value(model, parent_field, parent_id)
    # Normalize the data into a list
    if not isinstance(data, list):  # Single object or None
        data = [data] if data else []

    # Determine the next order number
    return len(data) + 1


def add_question_to_quiz(quiz, question_text, allow_multiple_answers=False):
    """
    Adds a question to the specified quiz.

    Args:
        quiz: The quiz to which the question belongs.
        question_text (str): The text of the question.
        allow_multiple_answers (bool): Whether multiple answers are allowed.

    Returns:
        Question: The created question object.
    """
    # First, try to find a question with the same question_text
    existing_question = storage.get_by_value(
        Question, "question_text", question_text)

    # Get the next order number for the question
    if not existing_question:
        order_number = get_next_order_number(Question, quiz.id, 'quiz_id')

    # If a question is found, check if it belongs to the same quiz
    if existing_question and existing_question.quiz_id == quiz.id:
        print(
            f"Question {existing_question.order_number}: '{question_text}' "
            f"already exists in quiz '{quiz.title}'!"
        )
        return existing_question

    # Create and save the question
    question = Question(
        quiz_id=quiz.id,
        question_text=question_text,
        allow_multiple_answers=allow_multiple_answers,
        order_number=order_number  # Assign the order number
    )
    question.save()
    print(
        f"Question {order_number}: '{question_text}' "
        f"added to quiz '{quiz.title}'."
        )
    return question


def add_choice_to_question(question, choice_text, is_correct):
    """
    Adds a choice to the specified question.

    Args:
        question: The question to which the choice belongs.
        choice_text (str): The text of the choice.
        is_correct (bool): Whether the choice is correct.

    Returns:
        Choice: The created choice object or an existing choice object.
    """

    # Check if the choice already exists
    existing_choice = storage.get_by_value(Choice, "choice_text", choice_text)

    # Handle the case where multiple choices are returned
    if isinstance(existing_choice, list):
        for choice in existing_choice:
            if choice.question_id == question.id:
                print(
                    f"Choice {choice.order_number}: '{choice_text}' "
                    f"already exists for question '{question.question_text}'!"
                )
                return choice

    # Handle the case where a single choice object is returned
    elif existing_choice and existing_choice.question_id == question.id:
        print(
            f"Choice {existing_choice.order_number}: '{choice_text}' "
            f"already exists for question '{question.question_text}'!"
        )
        return existing_choice

    # Get the next order number for the choice
    order_number = get_next_order_number(Choice, question.id, 'question_id')

    # Create and save the choicprint(existing_choice)e
    choice = Choice(
        question_id=question.id,
        choice_text=choice_text,
        is_correct=is_correct,
        order_number=order_number  # Assign the order number
    )
    choice.save()
    print(
        f"Choice {order_number}: '{choice_text}' "
        f"added to question '{question.question_text}'."
    )
    return choice


def add_result(
    user_id: int,
    quiz_id: int,
    score: str = "0.00",
    time_taken: int = 0,
    status: QuizSessionStatus = QuizSessionStatus.IN_PROGRESS,
    submitted_at: Optional[datetime] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Optional[Result]:
    """
    Adds a new quiz attempt (result) for a user to the database.
    Creates a new result entry if the user does not have an in-progress quiz
    and hasn't exceeded the limit of 3 attempts for the day.

    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        score (str): The score the user obtained. Defaults to '0.00'.
        time_taken (int): The time taken to complete the quiz in seconds.
                          Defaults to 0.
        status (QuizSessionStatus): The status of the quiz attempt.
                                    Defaults to "IN_PROGRESS".
        submitted_at (Optional[datetime]): The timestamp when the quiz was
                                           submitted. Defaults to now.
        start_time (Optional[datetime]): The timestamp when the quiz started.
                                         Defaults to now.
        end_time (Optional[datetime]): The timestamp when the quiz ended.
                                       Defaults to now.

    Returns:
        Optional[Result]: The created result object or
                          None if conditions are not met.
    """
    # Set default timestamps if not provided
    now = datetime.now(timezone.utc)
    submitted_at = submitted_at or now
    start_time = start_time or now

    # Check if the user already has an in-progress quiz session
    existing_result = storage.query(Result).filter(
        Result.user_id == user_id,
        Result.status == QuizSessionStatus.IN_PROGRESS
    ).first()

    if existing_result:
        print("User already has an in-progress quiz session.")
        return existing_result

    # Check if the user has already made 3 attempts for this quiz today
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    attempts_today = storage.query(Result).filter(
        Result.user_id == user_id,
        Result.quiz_id == quiz_id,
        Result.submitted_at >= start_of_today
    ).count()

    if attempts_today >= 3:
        print("User has already made 3 attempts for this quiz today.")
        return None

    # Validate status
    if status not in QuizSessionStatus:
        raise ValueError(f"Invalid status: {status}")

    # Create a new result entry
    new_result = Result(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        time_taken=time_taken,
        status=status,
        submitted_at=submitted_at,
        start_time=start_time,
        end_time=end_time,  # This can be None if the quiz hasn't ended yet
    )

    # Add the new result to the session and commit
    new_result.save()
    print(f"Result with id {new_result.id} has been saved")

    return new_result


def add_answer(
    user_id: str,
    quiz_title: str,
    question_text: str,
    choice_text: str,
    result_id: str
) -> Optional[UserAnswer]:
    """
    Adds an answer to a quiz question for a specific user and result_id.

    If the question allows only one answer (allow_multiple_answers=False),
    the existing answer is replaced. Otherwise, a new answer is added.
    Ensures the quiz attempt is still in progress before adding the answer.

    Args:
        user_id (str): The ID of the user providing the answer.
        quiz_title (str): The title of the quiz the question belongs to.
        question_text (str): The text of the question being answered.
        choice_text (str): The text of the choice selected by the user.
        result_id (str): The result_id for the specific quiz attempt.

    Returns:
        UserAnswer: The created or updated UserAnswer object
                    or None if the quiz is no longer in progress.
    """
    # Fetch the quiz
    quiz = storage.get_by_value(Quiz, "title", quiz_title)
    if not quiz:
        print(f"Quiz '{quiz_title}' does not exist!")
        return None

    # Fetch the result to check if the quiz is still in progress
    result = storage.get_by_value(Result, "id", result_id)
    if not result:
        print(
            f"Result for the quiz attempt with result_id ",
            f"'{result_id}' does not exist!"
        )
        return None

    # Check if the quiz is still in progress
    if result.status.value in ["completed", "timed-out"]:
        print(
            f"Cannot submit answer. The quiz with result_id '{result_id}' "
            f"is already {result.status.value}!"
        )
        return None

    # Fetch the question
    question = next(
        (q for q in quiz.questions if q.question_text == question_text), None
    )
    if not question:
        print(
            f"Question '{question_text}' does not exist "
            f"in quiz '{quiz_title}'!"
        )
        return None

    # Fetch the choice
    choice = next(
        (c for c in question.choices if c.choice_text == choice_text), None
    )
    if not choice:
        print(
            f"Choice '{choice_text}' does not exist "
            f"for question '{question_text}'!"
        )
        return None

    # Fetch existing answers for the same user, question, and result
    existing_answers = storage.filter_by(
        UserAnswer,
        user_id=user_id,
        question_id=question.id,
        result_id=result_id
    )

    # Handle single-answer questions
    if not question.allow_multiple_answers:
        if existing_answers:
            # If an existing answer is found, replace it
            existing_answer = existing_answers[0]
            if existing_answer.choice_id != choice.id:
                existing_answer.choice_id = choice.id
                storage.save()
                print(
                    f"Answer updated for user '{user_id}' "
                    f"in quiz '{quiz_title}'!"
                )
            else:
                print("Your choice is still the same!")
            return existing_answer

    # Handle multiple-answer questions
    else:
        # Check if the choice has already been selected for this question
        if any(answer.choice_id == choice.id for answer in existing_answers):
            print(
                f"Choice '{choice_text}' has already been selected "
                f"for this question!"
            )
            return None

    # Create and save a new answer
    user_answer = UserAnswer(
        user_id=user_id,
        quiz_id=quiz.id,
        question_id=question.id,
        choice_id=choice.id,
        result_id=result_id
    )
    user_answer.save()
    print(
        f"Answer added for user '{user_answer.user.username}' "
        f"in quiz '{quiz_title}'!"
        )
    return user_answer


if __name__ == "__main__":
    # Add me
    # Create the user
    role = "admin"
    role = Role.from_str(role)
    print(role)
    me = User(
        first_name="Adwoa",
        last_name="Serwah",
        username="AdwoaSK",
        email="adwoaserwahkyeibaffour@gmail.com",
        password="123",
        role=role
    )
    # Add user
    user_obj = add_user(
        first_name="John",
        last_name="Doe",
        username="JohnD",
        email="john.doa1e2@example.com",
        password="password1234")

    user_obj = add_user(
        first_name="Adwoa",
        last_name="Serwah",
        username="AdwoaSK",
        email="adwoa@sk.com",
        password="1234")

    # Top-level topics
    math = add_topic("Mathematics")
    science = add_topic("Science")

    # Subtopics under Mathematics
    algebra = add_topic("Algebra", math)
    geometry = add_topic("Geometry", math)
    arithmetic = add_topic(name="Arithmetic", parent=math)

    # Subtopics under Arithmetic
    addition = add_topic(name="Addition", parent=arithmetic)
    subtraction = add_topic(name="Subtraction", parent=arithmetic)
    multiplication = add_topic(name="Multiplication", parent=arithmetic)
    division = add_topic(name="Division", parent=arithmetic)

    # Subtopics under Science
    physics = add_topic("Physics", science)
    chemistry = add_topic("Chemistry", science)

    # Add quiz for the "Addition" topic
    add_quiz(
        title="Basic Addition",
        description="A quiz on basic addition of numbers.",
        time_limit=10,
        topic_name="Addition"
    )

    # Add quiz for the "Subtraction" topic
    add_quiz(
        title="Basic Subtraction",
        description="A quiz on basic subtraction of numbers.",
        time_limit=10,
        topic_name="Subtraction"
    )

    # Add quiz for the "Division" topic
    add_quiz(
        title="Basic Division",
        description="A quiz on basic division of numbers.",
        time_limit=10,
        topic_name="Division"
    )

    # Add quiz for the "Multiplication" topic
    add_quiz(
        title="Basic Multiplication",
        description="A quiz on basic multiplication of numbers.",
        time_limit=10,
        topic_name="Multiplication"
    )

    # Retrieve the quiz for "Basic Addition"
    quiz = storage.get_by_value(Quiz, "title", "Basic Addition")
    if not quiz:
        print("Quiz 'Basic Addition' does not exist!")
        exit()

    # Add questions and choices to the quiz
    question_1 = add_question_to_quiz(quiz, "What is 2 + 3?")
    add_choice_to_question(question_1, "5", True)
    add_choice_to_question(question_1, "6", False)
    add_choice_to_question(question_1, "4", False)
    add_choice_to_question(question_1, "3", False)
    add_choice_to_question(question_1, "no_answer", False)

    question_2 = add_question_to_quiz(quiz, "What is 12 + 7?")
    add_choice_to_question(question_2, "19", True)
    add_choice_to_question(question_2, "20", False)
    add_choice_to_question(question_2, "18", False)
    add_choice_to_question(question_2, "15", False)
    add_choice_to_question(question_2, "no_answer", False)

    question_3 = add_question_to_quiz(quiz, "What is 9 + 1?")
    add_choice_to_question(question_3, "10", True)
    add_choice_to_question(question_3, "9", False)
    add_choice_to_question(question_3, "8", False)
    add_choice_to_question(question_3, "11", False)
    add_choice_to_question(question_3, "no_answer", False)

    question_4 = add_question_to_quiz(quiz, "What is 5 + 5?")
    add_choice_to_question(question_4, "10", True)
    add_choice_to_question(question_4, "11", False)
    add_choice_to_question(question_4, "12", False)
    add_choice_to_question(question_4, "9", False)
    add_choice_to_question(question_4, "no_answer", False)

    question_5 = add_question_to_quiz(quiz, "What is 20 + 15?")
    add_choice_to_question(question_5, "35", True)
    add_choice_to_question(question_5, "40", False)
    add_choice_to_question(question_5, "30", False)
    add_choice_to_question(question_5, "45", False)
    add_choice_to_question(question_5, "no_answer", False)

    question_6 = add_question_to_quiz(quiz, "What is 8 + 13?")
    add_choice_to_question(question_6, "19", True)
    add_choice_to_question(question_6, "21", False)
    add_choice_to_question(question_6, "20", False)
    add_choice_to_question(question_6, "18", False)
    add_choice_to_question(question_6, "no_answer", False)

    question_7 = add_question_to_quiz(quiz, "3 + 7 = ?")
    add_choice_to_question(question_7, "10", True)
    add_choice_to_question(question_7, "9", False)
    add_choice_to_question(question_7, "8", False)
    add_choice_to_question(question_7, "7", False)
    add_choice_to_question(question_7, "no_answer", False)

    question_8 = add_question_to_quiz(quiz, "What is 6 + 9?")
    add_choice_to_question(question_8, "15", True)
    add_choice_to_question(question_8, "16", False)
    add_choice_to_question(question_8, "14", False)
    add_choice_to_question(question_8, "13", False)
    add_choice_to_question(question_8, "no_answer", False)

    question_9 = add_question_to_quiz(quiz, "4 + 8 = ?")
    add_choice_to_question(question_9, "12", True)
    add_choice_to_question(question_9, "11", False)
    add_choice_to_question(question_9, "14", False)
    add_choice_to_question(question_9, "13", False)
    add_choice_to_question(question_9, "no_answer", False)

    question_10 = add_question_to_quiz(quiz, "7 + 6 = 14.")
    add_choice_to_question(question_10, "True", False)
    add_choice_to_question(question_10, "False", True)
    add_choice_to_question(question_10, "no_answer", False)

    quiz = storage.get_by_value(Quiz, "title", "Basic Subtraction")
    if not quiz:
        print("Quiz 'Basic Subtraction' does not exist!")
        exit()

    # Add questions and choices to the quiz
    print(quiz.title)
    question_1 = add_question_to_quiz(quiz, "What is 5 - 3?")
    add_choice_to_question(question_1, "2", True)
    add_choice_to_question(question_1, "3", False)
    add_choice_to_question(question_1, "1", False)
    add_choice_to_question(question_1, "4", False)
    add_choice_to_question(question_1, "no_answer", False)

    question_2 = add_question_to_quiz(quiz, "What is 12 - 7?")
    add_choice_to_question(question_2, "5", True)
    add_choice_to_question(question_2, "6", False)
    add_choice_to_question(question_2, "4", False)
    add_choice_to_question(question_2, "3", False)
    add_choice_to_question(question_2, "no_answer", False)

    question_3 = add_question_to_quiz(quiz, "What is 9 - 1?")
    add_choice_to_question(question_3, "8", True)
    add_choice_to_question(question_3, "9", False)
    add_choice_to_question(question_3, "7", False)
    add_choice_to_question(question_3, "6", False)
    add_choice_to_question(question_3, "no_answer", False)

    question_4 = add_question_to_quiz(quiz, "What is 10 - 5?")
    add_choice_to_question(question_4, "5", True)
    add_choice_to_question(question_4, "4", False)
    add_choice_to_question(question_4, "6", False)
    add_choice_to_question(question_4, "7", False)
    add_choice_to_question(question_4, "no_answer", False)

    question_5 = add_question_to_quiz(quiz, "What is 20 - 8?")
    add_choice_to_question(question_5, "12", True)
    add_choice_to_question(question_5, "14", False)
    add_choice_to_question(question_5, "13", False)
    add_choice_to_question(question_5, "11", False)
    add_choice_to_question(question_5, "no_answer", False)

    question_6 = add_question_to_quiz(quiz, "What is 15 - 9?")
    add_choice_to_question(question_6, "6", True)
    add_choice_to_question(question_6, "7", False)
    add_choice_to_question(question_6, "8", False)
    add_choice_to_question(question_6, "5", False)
    add_choice_to_question(question_6, "no_answer", False)

    question_7 = add_question_to_quiz(quiz, "What is 18 - 7?")
    add_choice_to_question(question_7, "11", True)
    add_choice_to_question(question_7, "10", False)
    add_choice_to_question(question_7, "9", False)
    add_choice_to_question(question_7, "12", False)
    add_choice_to_question(question_7, "no_answer", False)

    question_8 = add_question_to_quiz(quiz, "What is 8 - 3?")
    add_choice_to_question(question_8, "5", True)
    add_choice_to_question(question_8, "4", False)
    add_choice_to_question(question_8, "6", False)
    add_choice_to_question(question_8, "7", False)
    add_choice_to_question(question_8, "no_answer", False)

    question_9 = add_question_to_quiz(quiz, "What is 17 - 4?")
    add_choice_to_question(question_9, "13", True)
    add_choice_to_question(question_9, "12", False)
    add_choice_to_question(question_9, "14", False)
    add_choice_to_question(question_9, "11", False)
    add_choice_to_question(question_9, "no_answer", False)

    question_10 = add_question_to_quiz(quiz, "10 - 6 = 5.")
    add_choice_to_question(question_10, "True", False)
    add_choice_to_question(question_10, "False", True)
    add_choice_to_question(question_10, "no_answer", False)

    # Retrieve the quiz for "Basic Division"
    quiz = storage.get_by_value(Quiz, "title", "Basic Division")
    if not quiz:
        print("Quiz 'Basic Division' does not exist!")
        exit()

    # Add questions and choices to the quiz
    question_1 = add_question_to_quiz(quiz, "What is 10 ÷ 2?")
    add_choice_to_question(question_1, "5", True)
    add_choice_to_question(question_1, "4", False)
    add_choice_to_question(question_1, "6", False)
    add_choice_to_question(question_1, "3", False)
    add_choice_to_question(question_1, "no_answer", False)

    question_2 = add_question_to_quiz(quiz, "What is 20 ÷ 4?")
    add_choice_to_question(question_2, "5", True)
    add_choice_to_question(question_2, "6", False)
    add_choice_to_question(question_2, "4", False)
    add_choice_to_question(question_2, "7", False)
    add_choice_to_question(question_2, "no_answer", False)

    question_3 = add_question_to_quiz(quiz, "What is 18 ÷ 3?")
    add_choice_to_question(question_3, "6", True)
    add_choice_to_question(question_3, "5", False)
    add_choice_to_question(question_3, "4", False)
    add_choice_to_question(question_3, "7", False)
    add_choice_to_question(question_3, "no_answer", False)

    question_4 = add_question_to_quiz(quiz, "What is 15 ÷ 3?")
    add_choice_to_question(question_4, "5", True)
    add_choice_to_question(question_4, "4", False)
    add_choice_to_question(question_4, "3", False)
    add_choice_to_question(question_4, "6", False)
    add_choice_to_question(question_4, "no_answer", False)

    question_5 = add_question_to_quiz(quiz, "What is 36 ÷ 6?")
    add_choice_to_question(question_5, "6", True)
    add_choice_to_question(question_5, "5", False)
    add_choice_to_question(question_5, "4", False)
    add_choice_to_question(question_5, "3", False)
    add_choice_to_question(question_5, "no_answer", False)

    question_6 = add_question_to_quiz(quiz, "What is 25 ÷ 5?")
    add_choice_to_question(question_6, "5", True)
    add_choice_to_question(question_6, "4", False)
    add_choice_to_question(question_6, "6", False)
    add_choice_to_question(question_6, "7", False)
    add_choice_to_question(question_6, "no_answer", False)

    question_7 = add_question_to_quiz(quiz, "What is 9 ÷ 3?")
    add_choice_to_question(question_7, "3", True)
    add_choice_to_question(question_7, "2", False)
    add_choice_to_question(question_7, "4", False)
    add_choice_to_question(question_7, "5", False)

    question_8 = add_question_to_quiz(quiz, "What is 40 ÷ 8?")
    add_choice_to_question(question_8, "5", True)
    add_choice_to_question(question_8, "6", False)
    add_choice_to_question(question_8, "4", False)
    add_choice_to_question(question_8, "7", False)
    add_choice_to_question(question_8, "no_answer", False)

    question_9 = add_question_to_quiz(quiz, "What is 81 ÷ 9?")
    add_choice_to_question(question_9, "9", True)
    add_choice_to_question(question_9, "8", False)
    add_choice_to_question(question_9, "7", False)
    add_choice_to_question(question_9, "10", False)
    add_choice_to_question(question_9, "no_answer", False)

    question_10 = add_question_to_quiz(quiz, "What is 16 ÷ 4?")
    add_choice_to_question(question_10, "4", True)
    add_choice_to_question(question_10, "5", False)
    add_choice_to_question(question_10, "3", False)
    add_choice_to_question(question_10, "2", False)
    add_choice_to_question(question_10, "no_answer", False)

    # Retrieve the quiz for "Basic Multiplication"
    quiz = storage.get_by_value(Quiz, "title", "Basic Multiplication")
    if not quiz:
        print("Quiz 'Basic Multiplication' does not exist!")
        exit()

    # Add questions and choices to the quiz
    question_1 = add_question_to_quiz(quiz, "What is 2 × 3?")
    add_choice_to_question(question_1, "6", True)
    add_choice_to_question(question_1, "7", False)
    add_choice_to_question(question_1, "8", False)
    add_choice_to_question(question_1, "9", False)
    add_choice_to_question(question_1, "no_answer", False)

    question_2 = add_question_to_quiz(quiz, "What is 5 × 4?")
    add_choice_to_question(question_2, "20", True)
    add_choice_to_question(question_2, "15", False)
    add_choice_to_question(question_2, "10", False)
    add_choice_to_question(question_2, "25", False)
    add_choice_to_question(question_2, "no_answer", False)

    question_3 = add_question_to_quiz(quiz, "What is 3 × 6?")
    add_choice_to_question(question_3, "18", True)
    add_choice_to_question(question_3, "15", False)
    add_choice_to_question(question_3, "21", False)
    add_choice_to_question(question_3, "16", False)
    add_choice_to_question(question_3, "no_answer", False)

    question_4 = add_question_to_quiz(quiz, "What is 7 × 8?")
    add_choice_to_question(question_4, "56", True)
    add_choice_to_question(question_4, "64", False)
    add_choice_to_question(question_4, "48", False)
    add_choice_to_question(question_4, "52", False)
    add_choice_to_question(question_4, "no_answer", False)

    question_5 = add_question_to_quiz(quiz, "What is 6 × 9?")
    add_choice_to_question(question_5, "54", True)
    add_choice_to_question(question_5, "45", False)
    add_choice_to_question(question_5, "50", False)
    add_choice_to_question(question_5, "60", False)
    add_choice_to_question(question_5, "no_answer", False)

    question_6 = add_question_to_quiz(quiz, "What is 8 × 7?")
    add_choice_to_question(question_6, "56", True)
    add_choice_to_question(question_6, "48", False)
    add_choice_to_question(question_6, "63", False)
    add_choice_to_question(question_6, "52", False)
    add_choice_to_question(question_6, "no_answer", False)

    question_7 = add_question_to_quiz(quiz, "What is 4 × 5?")
    add_choice_to_question(question_7, "20", True)
    add_choice_to_question(question_7, "25", False)
    add_choice_to_question(question_7, "15", False)
    add_choice_to_question(question_7, "30", False)
    add_choice_to_question(question_7, "no_answer", False)

    question_8 = add_question_to_quiz(quiz, "What is 9 × 3?")
    add_choice_to_question(question_8, "27", True)
    add_choice_to_question(question_8, "24", False)
    add_choice_to_question(question_8, "30", False)
    add_choice_to_question(question_8, "21", False)
    add_choice_to_question(question_8, "no_answer", False)

    question_9 = add_question_to_quiz(quiz, "What is 12 × 4?")
    add_choice_to_question(question_9, "48", True)
    add_choice_to_question(question_9, "50", False)
    add_choice_to_question(question_9, "40", False)
    add_choice_to_question(question_9, "45", False)
    add_choice_to_question(question_9, "no_answer", False)

    question_10 = add_question_to_quiz(quiz, "What is 10 × 10?")
    add_choice_to_question(question_10, "100", True)
    add_choice_to_question(question_10, "90", False)
    add_choice_to_question(question_10, "110", False)
    add_choice_to_question(question_10, "120", False)
    add_choice_to_question(question_10, "no_answer", False)

    # Assuming the user 'John Doe' exists in the database
    user = storage.get_by_value(User, "username", "janes1t2")
    if not user:
        print("User 'janes1t2' does not exist!")
        exit()

    user_id = user.id

    # Retrieve the quiz for "Basic Addition"
    quiz = storage.get_by_value(Quiz, "title", "Basic Addition")
    if not quiz:
        print("Quiz 'Basic Addition' does not exist!")
        exit()

    result = add_result(user_id, quiz.id)

    # Add answers for the 'Basic Addition' quiz
    add_answer(user_id, "Basic Addition", "What is 2 + 3?", "5", result.id)
    add_answer(user_id, "Basic Addition", "What is 12 + 7?", "19", result.id)
    add_answer(user_id, "Basic Addition", "What is 9 + 1?", "10", result.id)
    add_answer(user_id, "Basic Addition", "What is 5 + 5?", "10", result.id)
    add_answer(user_id, "Basic Addition", "What is 20 + 15?", "35", result.id)
    add_answer(user_id, "Basic Addition", "What is 8 + 13?", "19", result.id)
    add_answer(user_id, "Basic Addition", "3 + 7 = ?", "10", result.id)
    add_answer(user_id, "Basic Addition", "What is 6 + 9?", "15", result.id)
    add_answer(user_id, "Basic Addition", "4 + 8 = ?", "12", result.id)
    add_answer(user_id, "Basic Addition", "7 + 6 = 14.", "False", result.id)

    me = storage.get_by_value(User, 'username', 'AdwoaSK')
    me.role = Role.from_str("admin")
    print(me.role)
    me.save()
    print(me.role)
