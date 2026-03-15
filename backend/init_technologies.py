from backend.database import SessionLocal
from backend.models import Technology

# Default technologies list
DEFAULT_TECHNOLOGIES = [
    # Programming Languages
    ("Python", "Language"),
    ("JavaScript", "Language"),
    ("TypeScript", "Language"),
    ("Java", "Language"),
    ("C++", "Language"),
    ("Rust", "Language"),
    ("Go", "Language"),
    ("Ruby", "Language"),
    ("PHP", "Language"),
    ("Kotlin", "Language"),
    ("Swift", "Language"),
    ("C#", "Language"),

    # Frameworks & Libraries
    ("React", "Framework"),
    ("Vue.js", "Framework"),
    ("Angular", "Framework"),
    ("Django", "Framework"),
    ("FastAPI", "Framework"),
    ("Flask", "Framework"),
    ("Spring Boot", "Framework"),
    ("Express.js", "Framework"),
    ("Next.js", "Framework"),
    ("NestJS", "Framework"),

    # Databases
    ("PostgreSQL", "Database"),
    ("MongoDB", "Database"),
    ("MySQL", "Database"),
    ("Redis", "Database"),
    ("Firebase", "Database"),
    ("DynamoDB", "Database"),
    ("SQLite", "Database"),

    # AI/ML
    ("Machine Learning", "AI"),
    ("Deep Learning", "AI"),
    ("TensorFlow", "AI"),
    ("PyTorch", "AI"),
    ("Scikit-learn", "AI"),
    ("NLP", "AI"),
    ("Computer Vision", "AI"),
    ("Qwen2", "AI"),
    ("LLM", "AI"),

    # Cloud & DevOps
    ("AWS", "Cloud"),
    ("Google Cloud", "Cloud"),
    ("Azure", "Cloud"),
    ("Docker", "DevOps"),
    ("Kubernetes", "DevOps"),
    ("CI/CD", "DevOps"),

    # Mobile
    ("React Native", "Mobile"),
    ("Flutter", "Mobile"),
    ("iOS", "Mobile"),
    ("Android", "Mobile"),

    # Other
    ("Web3", "Technology"),
    ("Blockchain", "Technology"),
    ("IoT", "Technology"),
    ("AR/VR", "Technology"),
    ("GraphQL", "Technology"),
    ("REST API", "Technology"),
]


def init_technologies():
    """Initialize default technologies in the database"""
    db = SessionLocal()
    try:
        for name, category in DEFAULT_TECHNOLOGIES:
            # Check if technology already exists
            existing = db.query(Technology).filter(Technology.name == name).first()
            if not existing:
                tech = Technology(name=name, category=category)
                db.add(tech)

        db.commit()
        print(f"Initialized {len(DEFAULT_TECHNOLOGIES)} technologies")
    except Exception as e:
        db.rollback()
        print(f"Error initializing technologies: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_technologies()
