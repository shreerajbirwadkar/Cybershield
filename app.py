from flask import Flask, send_file, jsonify, request
import sqlite3
import os

app = Flask(__name__)

# =====================================================
# DATABASE PATH
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_FOLDER = os.path.join(
    BASE_DIR,
    "database"
)

DATABASE = os.path.join(
    DATABASE_FOLDER,
    "cybershield.db"
)

os.makedirs(
    DATABASE_FOLDER,
    exist_ok=True
)


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    # Enable foreign key support
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_database():

    conn = get_db_connection()

    # =================================================
    # VISITORS TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS visitors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            age INTEGER,

            student_status TEXT,

            education_level TEXT,

            year TEXT,

            branch TEXT,

            sub_branch TEXT,

            occupation TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =================================================
    # OLD DATABASE MIGRATION
    # =================================================

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(visitors)"
        ).fetchall()
    }

    if "education_level" not in columns:

        conn.execute("""
            ALTER TABLE visitors
            ADD COLUMN education_level TEXT
        """)

    if "sub_branch" not in columns:

        conn.execute("""
            ALTER TABLE visitors
            ADD COLUMN sub_branch TEXT
        """)

    # =================================================
    # QUIZ ATTEMPTS TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            visitor_id INTEGER,

            score INTEGER NOT NULL,

            total_questions INTEGER NOT NULL,

            percentage REAL NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(visitor_id)
                REFERENCES visitors(id)
        )
    """)

    # =================================================
    # FEEDBACK TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            visitor_id INTEGER,

            rating INTEGER NOT NULL,

            message TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(visitor_id)
                REFERENCES visitors(id)
        )
    """)

    # =================================================
    # ADMINS TABLE
    # =================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    return send_file(
        os.path.join(
            BASE_DIR,
            "index.html"
        )
    )


# =====================================================
# DATABASE TEST
# =====================================================

@app.route(
    "/api/database-test",
    methods=["GET"]
)
def database_test():

    try:

        conn = get_db_connection()

        conn.execute(
            "SELECT 1"
        ).fetchone()

        conn.close()

        return jsonify({

            "success": True,

            "message":
                "SQLite database is connected!"

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# REGISTER VISITOR
# =====================================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No registration data received."

            }), 400

        # -------------------------------------------------
        # GET DATA
        # -------------------------------------------------

        name = str(
            data.get(
                "name",
                ""
            )
        ).strip()

        age = data.get("age")

        student_status = str(
            data.get(
                "student_status",
                ""
            )
        ).strip()

        education_level = str(
            data.get(
                "education_level",
                ""
            )
        ).strip()

        year = str(
            data.get(
                "year",
                ""
            )
        ).strip()

        branch = str(
            data.get(
                "branch",
                ""
            )
        ).strip()

        sub_branch = str(
            data.get(
                "sub_branch",
                ""
            )
        ).strip()

        occupation = str(
            data.get(
                "occupation",
                ""
            )
        ).strip()

        # -------------------------------------------------
        # NAME VALIDATION
        # -------------------------------------------------

        if not name:

            return jsonify({

                "success": False,

                "message":
                    "Full name is required."

            }), 400

        # -------------------------------------------------
        # AGE VALIDATION
        # -------------------------------------------------

        if age is None or age == "":

            return jsonify({

                "success": False,

                "message":
                    "Age is required."

            }), 400

        try:

            age = int(age)

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "success": False,

                "message":
                    "Age must be a valid number."

            }), 400

        if age < 10 or age > 100:

            return jsonify({

                "success": False,

                "message":
                    "Age must be between 10 and 100."

            }), 400

        # -------------------------------------------------
        # STUDENT STATUS VALIDATION
        # -------------------------------------------------

        if student_status not in [
            "Yes",
            "No"
        ]:

            return jsonify({

                "success": False,

                "message":
                    "Please select whether you are a student."

            }), 400

        # -------------------------------------------------
        # STUDENT VALIDATION
        # -------------------------------------------------

        if student_status == "Yes":

            if not education_level:

                return jsonify({

                    "success": False,

                    "message":
                        "Please select your education level."

                }), 400

            if not year:

                return jsonify({

                    "success": False,

                    "message":
                        "Please select your year."

                }), 400

            if not branch:

                return jsonify({

                    "success": False,

                    "message":
                        "Please select your branch/course."

                }), 400

        # -------------------------------------------------
        # NON-STUDENT VALIDATION
        # -------------------------------------------------

        if student_status == "No":

            if not occupation:

                return jsonify({

                    "success": False,

                    "message":
                        "Please select your occupation."

                }), 400

            education_level = ""
            year = ""
            branch = ""
            sub_branch = ""

        # -------------------------------------------------
        # SAVE VISITOR
        # -------------------------------------------------

        conn = get_db_connection()

        cursor = conn.execute("""
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

        visitor_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({

            "success": True,

            "message":
                "Registration successful! Data saved to SQLite.",

            "visitor_id":
                visitor_id

        }), 201

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Registration failed: {str(e)}"

        }), 500


# =====================================================
# GET ALL VISITORS
# =====================================================

@app.route(
    "/api/visitors",
    methods=["GET"]
)
def get_visitors():

    try:

        conn = get_db_connection()

        rows = conn.execute("""
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
        """).fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "visitors":
                [dict(row) for row in rows]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# VISITOR COUNT
# =====================================================

@app.route(
    "/api/visitors/count",
    methods=["GET"]
)
def visitor_count():

    try:

        conn = get_db_connection()

        result = conn.execute("""
            SELECT COUNT(*) AS total
            FROM visitors
        """).fetchone()

        conn.close()

        return jsonify({

            "success": True,

            "total":
                result["total"]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# SAVE QUIZ ATTEMPT
# =====================================================

@app.route(
    "/api/quiz-attempt",
    methods=["POST"]
)
def save_quiz_attempt():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        visitor_id = data.get(
            "visitor_id"
        )

        score = data.get(
            "score"
        )

        total_questions = data.get(
            "total_questions"
        )

        # -------------------------------------------------
        # SCORE VALIDATION
        # -------------------------------------------------

        try:

            score = int(score)

            total_questions = int(
                total_questions
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "success": False,

                "message":
                    "Invalid quiz score data."

            }), 400

        if total_questions <= 0:

            return jsonify({

                "success": False,

                "message":
                    "Total questions must be greater than zero."

            }), 400

        if score < 0 or score > total_questions:

            return jsonify({

                "success": False,

                "message":
                    "Invalid quiz score."

            }), 400

        # -------------------------------------------------
        # CALCULATE PERCENTAGE
        # -------------------------------------------------

        percentage = round(
            (
                score /
                total_questions
            ) * 100,
            2
        )

        # -------------------------------------------------
        # VALIDATE VISITOR ID
        # -------------------------------------------------

        if visitor_id in [
            None,
            "",
            "null"
        ]:

            visitor_id = None

        else:

            try:

                visitor_id = int(
                    visitor_id
                )

            except (
                ValueError,
                TypeError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Invalid visitor ID."

                }), 400

            conn = get_db_connection()

            visitor = conn.execute("""
                SELECT id
                FROM visitors
                WHERE id = ?
            """, (
                visitor_id,
            )).fetchone()

            conn.close()

            if not visitor:

                visitor_id = None

        # -------------------------------------------------
        # SAVE QUIZ
        # -------------------------------------------------

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO quiz_attempts
            (
                visitor_id,
                score,
                total_questions,
                percentage
            )
            VALUES (?, ?, ?, ?)
        """, (

            visitor_id,
            score,
            total_questions,
            percentage

        ))

        quiz_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({

            "success": True,

            "message":
                "Quiz attempt saved successfully.",

            "quiz_id":
                quiz_id,

            "percentage":
                percentage

        }), 201

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Quiz save failed: {str(e)}"

        }), 500


# =====================================================
# QUIZ STATISTICS
# =====================================================

@app.route(
    "/api/quiz-stats",
    methods=["GET"]
)
def quiz_stats():

    try:

        conn = get_db_connection()

        result = conn.execute("""
            SELECT

                COUNT(*) AS attempts,

                COALESCE(
                    AVG(score),
                    0
                ) AS average_score,

                COALESCE(
                    AVG(percentage),
                    0
                ) AS average_percentage

            FROM quiz_attempts
        """).fetchone()

        conn.close()

        return jsonify({

            "success": True,

            "attempts":
                result["attempts"],

            "average_score":
                round(
                    result["average_percentage"],
                    1
                )

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# SAVE FEEDBACK
# =====================================================

@app.route(
    "/api/feedback",
    methods=["POST"]
)
def save_feedback():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        visitor_id = data.get(
            "visitor_id"
        )

        rating = data.get(
            "rating"
        )

        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()

        # -------------------------------------------------
        # RATING VALIDATION
        # -------------------------------------------------

        try:

            rating = int(rating)

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please select a valid rating."

            }), 400

        if rating < 1 or rating > 5:

            return jsonify({

                "success": False,

                "message":
                    "Rating must be between 1 and 5."

            }), 400

        # -------------------------------------------------
        # MESSAGE VALIDATION
        # -------------------------------------------------

        if not message:

            return jsonify({

                "success": False,

                "message":
                    "Please write your feedback."

            }), 400

        # -------------------------------------------------
        # VISITOR ID
        # -------------------------------------------------

        if visitor_id in [
            None,
            "",
            "null"
        ]:

            visitor_id = None

        else:

            try:

                visitor_id = int(
                    visitor_id
                )

            except (
                ValueError,
                TypeError
            ):

                visitor_id = None

        # -------------------------------------------------
        # IF VISITOR ID EXISTS, CHECK IT
        # -------------------------------------------------

        if visitor_id is not None:

            conn = get_db_connection()

            visitor = conn.execute("""
                SELECT id
                FROM visitors
                WHERE id = ?
            """, (
                visitor_id,
            )).fetchone()

            conn.close()

            if not visitor:

                visitor_id = None

        # -------------------------------------------------
        # SAVE FEEDBACK
        # -------------------------------------------------

        conn = get_db_connection()

        cursor = conn.execute("""
            INSERT INTO feedback
            (
                visitor_id,
                rating,
                message
            )
            VALUES (?, ?, ?)
        """, (

            visitor_id,
            rating,
            message

        ))

        feedback_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({

            "success": True,

            "message":
                "Feedback saved successfully.",

            "feedback_id":
                feedback_id

        }), 201

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Feedback save failed: {str(e)}"

        }), 500


# =====================================================
# GET FEEDBACK
# =====================================================

@app.route(
    "/api/feedback",
    methods=["GET"]
)
def get_feedback():

    try:

        conn = get_db_connection()

        rows = conn.execute("""
            SELECT
                id,
                visitor_id,
                rating,
                message,
                created_at
            FROM feedback
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        return jsonify({

            "success": True,

            "feedback":
                [dict(row) for row in rows]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500


# =====================================================
# COMPLETE DASHBOARD
# =====================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    try:

        conn = get_db_connection()

        # =================================================
        # VISITORS
        # =================================================

        visitors = conn.execute("""
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
        """).fetchall()

        # =================================================
        # FEEDBACK
        # =================================================

        feedback = conn.execute("""
            SELECT
                id,
                visitor_id,
                rating,
                message,
                created_at
            FROM feedback
            ORDER BY id DESC
        """).fetchall()

        # =================================================
        # QUIZ STATISTICS
        # =================================================

        quiz = conn.execute("""
            SELECT

                COUNT(*) AS attempts,

                COALESCE(
                    AVG(percentage),
                    0
                ) AS average_percentage

            FROM quiz_attempts
        """).fetchone()

        # =================================================
        # STUDENT COUNT
        # =================================================

        students = conn.execute("""
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE student_status = 'Yes'
        """).fetchone()

        # =================================================
        # NON-STUDENT COUNT
        # =================================================

        non_students = conn.execute("""
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE student_status = 'No'
        """).fetchone()

        # =================================================
        # AVERAGE FEEDBACK RATING
        # =================================================

        rating = conn.execute("""
            SELECT

                COALESCE(
                    AVG(rating),
                    0
                ) AS average_rating

            FROM feedback
        """).fetchone()

        conn.close()

        # =================================================
        # RESPONSE
        # =================================================

        return jsonify({

            "success": True,

            "visitor_count":
                len(visitors),

            "quiz_attempts":
                quiz["attempts"],

            "average_score":
                round(
                    quiz["average_percentage"],
                    1
                ),

            "students":
                students["total"],

            "non_students":
                non_students["total"],

            "average_rating":
                round(
                    rating["average_rating"],
                    1
                ),

            "visitors":
                [dict(row) for row in visitors],

            "feedback":
                [dict(row) for row in feedback]

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "message":
                f"Dashboard error: {str(e)}"

        }), 500


# =====================================================
# INITIALIZE DATABASE
# =====================================================

init_database()


# =====================================================
# START FLASK SERVER
# =====================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("       CyberShield Server Started")
    print("======================================")
    print(
        f"Database : {DATABASE}"
    )
    print(
        "URL      : http://127.0.0.1:5000"
    )
    print("======================================")
    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )