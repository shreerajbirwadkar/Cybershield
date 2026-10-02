from flask import Flask, send_file, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable is not set.")

    return psycopg2.connect(DATABASE_URL)


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Visitors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            student_status TEXT,
            education_level TEXT,
            year TEXT,
            branch TEXT,
            sub_branch TEXT,
            occupation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Quiz attempts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id SERIAL PRIMARY KEY,
            visitor_id INTEGER,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(visitor_id) REFERENCES visitors(id)
        )
    """)

    # Feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            visitor_id INTEGER,
            rating INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(visitor_id) REFERENCES visitors(id)
        )
    """)

    # Admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def home():
    return send_file(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    )


# ----------------------------------------
# DATABASE TEST
# ----------------------------------------

@app.route("/api/database-test", methods=["GET"])
def database_test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1")
        cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "PostgreSQL database is connected!"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# REGISTER VISITOR
# ----------------------------------------

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No registration data received."
            }), 400

        name = str(data.get("name", "")).strip()
        age = data.get("age")
        student_status = str(
            data.get("student_status", "")
        ).strip()

        education_level = str(
            data.get("education_level", "")
        ).strip()

        year = str(
            data.get("year", "")
        ).strip()

        branch = str(
            data.get("branch", "")
        ).strip()

        sub_branch = str(
            data.get("sub_branch", "")
        ).strip()

        occupation = str(
            data.get("occupation", "")
        ).strip()

        # Name validation
        if not name:
            return jsonify({
                "success": False,
                "message": "Full name is required."
            }), 400

        # Age validation
        if age is None or age == "":
            return jsonify({
                "success": False,
                "message": "Age is required."
            }), 400

        try:
            age = int(age)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Age must be a valid number."
            }), 400

        if age < 10 or age > 100:
            return jsonify({
                "success": False,
                "message": "Age must be between 10 and 100."
            }), 400

        # Student status
        if student_status not in ["Yes", "No"]:
            return jsonify({
                "success": False,
                "message": "Please select whether you are a student."
            }), 400

        # Student
        if student_status == "Yes":

            if not education_level:
                return jsonify({
                    "success": False,
                    "message": "Please select your education level."
                }), 400

            if not year:
                return jsonify({
                    "success": False,
                    "message": "Please select your year."
                }), 400

            if not branch:
                return jsonify({
                    "success": False,
                    "message": "Please select your branch/course."
                }), 400

        # Non-student
        if student_status == "No":

            if not occupation:
                return jsonify({
                    "success": False,
                    "message": "Please select your occupation."
                }), 400

            education_level = ""
            year = ""
            branch = ""
            sub_branch = ""

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO visitors
            (
                name,
                age,
                student_status,
                education_level,
                year,
                branch,
                sub_branch,
                occupation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            name,
            age,
            student_status,
            education_level,
            year,
            branch,
            sub_branch,
            occupation
        ))

        visitor_id = cursor.fetchone()[0]

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Registration successful! Data saved to PostgreSQL.",
            "visitor_id": visitor_id
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }), 500


# ----------------------------------------
# GET VISITORS
# ----------------------------------------

@app.route("/api/visitors", methods=["GET"])
def get_visitors():

    try:

        conn = get_db_connection()

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id,
                name,
                age,
                student_status,
                education_level,
                year,
                branch,
                sub_branch,
                occupation,
                created_at
            FROM visitors
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "visitors": rows
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# VISITOR COUNT
# ----------------------------------------

@app.route("/api/visitors/count", methods=["GET"])
def visitor_count():

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM visitors
        """)

        total = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "total": total
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# SAVE QUIZ
# ----------------------------------------

@app.route("/api/quiz-attempt", methods=["POST"])
def save_quiz_attempt():

    try:

        data = request.get_json(silent=True) or {}

        visitor_id = data.get("visitor_id")
        score = data.get("score")
        total_questions = data.get("total_questions")

        try:
            score = int(score)
            total_questions = int(total_questions)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid quiz score data."
            }), 400

        if total_questions <= 0:

            return jsonify({
                "success": False,
                "message": "Total questions must be greater than zero."
            }), 400

        if score < 0 or score > total_questions:

            return jsonify({
                "success": False,
                "message": "Invalid quiz score."
            }), 400

        percentage = round(
            (score / total_questions) * 100,
            2
        )

        if visitor_id in [None, "", "null"]:

            visitor_id = None

        else:

            try:
                visitor_id = int(visitor_id)

            except (ValueError, TypeError):

                return jsonify({
                    "success": False,
                    "message": "Invalid visitor ID."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM visitors WHERE id = %s",
                (visitor_id,)
            )

            visitor = cursor.fetchone()

            cursor.close()
            conn.close()

            if not visitor:
                visitor_id = None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO quiz_attempts
            (
                visitor_id,
                score,
                total_questions,
                percentage
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            visitor_id,
            score,
            total_questions,
            percentage
        ))

        quiz_id = cursor.fetchone()[0]

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Quiz attempt saved successfully.",
            "quiz_id": quiz_id,
            "percentage": percentage
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Quiz save failed: {str(e)}"
        }), 500


# ----------------------------------------
# QUIZ STATS
# ----------------------------------------

@app.route("/api/quiz-stats", methods=["GET"])
def quiz_stats():

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS attempts,
                COALESCE(AVG(percentage), 0) AS average_percentage
            FROM quiz_attempts
        """)

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "attempts": result[0],
            "average_score": round(float(result[1]), 1)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# SAVE FEEDBACK
# ----------------------------------------

@app.route("/api/feedback", methods=["POST"])
def save_feedback():

    try:

        data = request.get_json(silent=True) or {}

        visitor_id = data.get("visitor_id")
        rating = data.get("rating")
        message = str(
            data.get("message", "")
        ).strip()

        try:
            rating = int(rating)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Please select a valid rating."
            }), 400

        if rating < 1 or rating > 5:

            return jsonify({
                "success": False,
                "message": "Rating must be between 1 and 5."
            }), 400

        if not message:

            return jsonify({
                "success": False,
                "message": "Please write your feedback."
            }), 400

        if visitor_id in [None, "", "null"]:

            visitor_id = None

        else:

            try:
                visitor_id = int(visitor_id)

            except (ValueError, TypeError):

                visitor_id = None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO feedback
            (
                visitor_id,
                rating,
                message
            )
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            visitor_id,
            rating,
            message
        ))

        feedback_id = cursor.fetchone()[0]

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Feedback saved successfully.",
            "feedback_id": feedback_id
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": f"Feedback save failed: {str(e)}"
        }), 500


# ----------------------------------------
# GET FEEDBACK
# ----------------------------------------

@app.route("/api/feedback", methods=["GET"])
def get_feedback():

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute("""
            SELECT
                id,
                visitor_id,
                rating,
                message,
                created_at
            FROM feedback
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "feedback": rows
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# DASHBOARD
# ----------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def dashboard():

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # Visitors
        cursor.execute("""
            SELECT
                id,
                name,
                age,
                student_status,
                education_level,
                year,
                branch,
                sub_branch,
                occupation,
                created_at
            FROM visitors
            ORDER BY id DESC
        """)

        visitors = cursor.fetchall()

        # Feedback
        cursor.execute("""
            SELECT
                id,
                visitor_id,
                rating,
                message,
                created_at
            FROM feedback
            ORDER BY id DESC
        """)

        feedback = cursor.fetchall()

        # Quiz statistics
        cursor.execute("""
            SELECT
                COUNT(*) AS attempts,
                COALESCE(AVG(percentage), 0)
                AS average_percentage
            FROM quiz_attempts
        """)

        quiz = cursor.fetchone()

        # Students
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE student_status = 'Yes'
        """)

        students = cursor.fetchone()

        # Non-students
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE student_status = 'No'
        """)

        non_students = cursor.fetchone()

        # Average rating
        cursor.execute("""
            SELECT
                COALESCE(AVG(rating), 0)
                AS average_rating
            FROM feedback
        """)

        rating = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({

            "success": True,

            "visitor_count": len(visitors),

            "quiz_attempts": quiz["attempts"],

            "average_score": round(
                float(quiz["average_percentage"]),
                1
            ),

            "students": students["total"],

            "non_students": non_students["total"],

            "average_rating": round(
                float(rating["average_rating"]),
                1
            ),

            "visitors": visitors,

            "feedback": feedback
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ----------------------------------------
# INITIALIZE DATABASE
# ----------------------------------------

init_database()


# ----------------------------------------
# START SERVER
# ----------------------------------------

if __name__ == "__main__":

    print()
    print("======================================")
    print("       CyberShield Server Started")
    print("======================================")
    print("Database : PostgreSQL")
    print("======================================")
    print()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
