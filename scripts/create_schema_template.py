import psycopg2
import psycopg2.extensions

# ============================================================
# UPDATE THESE WITH YOUR ACTUAL RDS DETAILS
# ============================================================
RDS_HOST = 'YOUR_RDS_ENDPOINT_HERE'
RDS_USER = 'YOUR_USERNAME_HERE'
RDS_PASSWORD = 'YOUR_PASSWORD_HERE'
RDS_DATABASE = 'YOUR_DATABASE_HERE'
RDS_PORT = 5432

def connect_to_rds():
    try:
        conn = psycopg2.connect(
            host=RDS_HOST,
            database=RDS_DATABASE,
            user=RDS_USER,
            password=RDS_PASSWORD,
            port=RDS_PORT
        )
        print("✅ Connected to RDS successfully!")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None
    
def create_database():
    """Create the education_analytics database if it doesn't exist"""
    conn = connect_to_rds('postgres')  # Connect to default 'postgres' database
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'education_analytics'")
    exists = cursor.fetchone()
    
    if not exists:
        print("Creating database: education_analytics...")
        cursor.execute("CREATE DATABASE education_analytics;")
        print("✅ Database 'education_analytics' created successfully!")
    else:
        print("✅ Database 'education_analytics' already exists")
    
    cursor.close()
    conn.close()
    return True

def create_schema():
    """Create schema in education_analytics database"""
    conn = connect_to_rds('education_analytics')
    if not conn:
        return False
    
    # Turn off autocommit for schema creation (we want transactions)
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        print("Creating tables...")
        
        # Create main table for subject-level data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_performance (
                id SERIAL PRIMARY KEY,
                emis_code BIGINT,
                district VARCHAR(100),
                circuit VARCHAR(100),
                datayear INTEGER,
                term INTEGER,
                subject VARCHAR(200),
                subject_grade INTEGER,
                marks INTEGER,
                total_marks INTEGER,
                percentage DECIMAL(5,2),
                student_id VARCHAR(12),
                is_passing_40 BOOLEAN,
                is_passing_30 BOOLEAN,
                is_home_language BOOLEAN,
                is_life_orientation BOOLEAN,
                processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create aggregated student-term summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_term_summary (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(12),
                district VARCHAR(100),
                emis_code BIGINT,
                year INTEGER,
                term INTEGER,
                avg_percentage DECIMAL(5,2),
                subjects_passed_40 INTEGER,
                subjects_passed_30 INTEGER,
                total_subjects INTEGER,
                passes_home_language BOOLEAN,
                passes_life_orientation BOOLEAN,
                meets_basic_pass BOOLEAN,
                term_over_term_change DECIMAL(5,2),
                improvement_category VARCHAR(20),
                processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, year, term)
            )
        """)
        
        print("Creating indexes...")
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_district ON student_performance(district)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subject ON student_performance(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student ON student_term_summary(student_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pass ON student_term_summary(meets_basic_pass)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year_term ON student_term_summary(year, term)")
        
        print("Creating views...")
        
        # Create view for district dashboard
        cursor.execute("""
            CREATE OR REPLACE VIEW district_dashboard AS
            SELECT 
                district,
                year,
                term,
                COUNT(DISTINCT student_id) as total_students,
                ROUND(AVG(avg_percentage), 2) as avg_score,
                SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) as passing_students,
                ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / 
                      NULLIF(COUNT(DISTINCT student_id), 0), 2) as pass_rate
            FROM student_term_summary
            GROUP BY district, year, term
            ORDER BY district, year, term
        """)
        
        # Create view for subject performance
        cursor.execute("""
            CREATE OR REPLACE VIEW subject_performance AS
            SELECT 
                subject,
                COUNT(*) as total_records,
                ROUND(AVG(percentage), 2) as avg_score,
                ROUND(STDDEV(percentage), 2) as std_dev,
                SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) as passing_count,
                ROUND(100.0 * SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) / 
                      COUNT(*), 2) as pass_rate
            FROM student_performance
            GROUP BY subject
            ORDER BY avg_score DESC
        """)
        
        conn.commit()
        print("✅ Database schema created successfully!")
        print("   Tables: student_performance, student_term_summary")
        print("   Views: district_dashboard, subject_performance")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating schema: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    print("="*50)
    print("RDS SETUP")
    print("="*50)
    
    # Step 1: Create database if it doesn't exist
    if create_database():
        print("\n" + "="*50)
        print("CREATING SCHEMA")
        print("="*50)
        # Step 2: Create schema
        if create_schema():
            print("\n✅ Setup complete!")
        else:
            print("\n❌ Schema creation failed.")
    else:
        print("\n❌ Failed to create database. Please check your credentials.")