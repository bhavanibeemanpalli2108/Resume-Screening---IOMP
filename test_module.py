# test_module.py

from core.feedback_service.py import generate_feedback, extract_projects_with_ai

def test_feedback():
    print("\n===== TESTING FEEDBACK =====\n")

    resume_text = """
    Python developer with experience in Machine Learning, NLP, and web development.
    Built projects using Flask, React, and TensorFlow.
    """

    job_title = "Software Engineer"
    job_description = "Looking for Python, Machine Learning, and Docker skills."

    result = generate_feedback(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
        score=0.72,
        skills_matched=["Python", "Machine Learning", "Flask"],
        skills_missing=["Docker"],
        outcome="rejected"
    )

    print("Feedback Output:\n")
    print(result)


def test_project_extraction():
    print("\n===== TESTING PROJECT EXTRACTION =====\n")

    resume_text = """
    PROJECTS
    - Built a chatbot using Python and NLP techniques
    - Developed an e-commerce web app using React and Node.js
    - Created a recommendation system using Machine Learning
    """

    projects = extract_projects_with_ai(resume_text)

    print("Extracted Projects:\n")
    for p in projects:
        print(f"Name: {p['name']}")
        print(f"Description: {p['description']}")
        print("-" * 40)


if __name__ == "__main__":
    test_feedback()
    test_project_extraction()