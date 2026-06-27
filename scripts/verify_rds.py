import psycopg2
import pandas as pd

RDS_HOST = 'edu-analytics-db.ct8qe8s802j3.af-south-1.rds.amazonaws.com'
RDS_USER = 'postgres'
RDS_PASSWORD = 'CNSPass4180'
RDS_DATABASE = 'education_analytics'
RDS_PORT = 5432

print("="*60)
print("RDS DATA VERIFICATION")
print("="*60)

try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DATABASE,
        user=RDS_USER,
        password=RDS_PASSWORD,
        port=RDS_PORT
    )
    print("✅ Connected to RDS successfully!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

cursor = conn.cursor()

# 1. Check record counts
cursor.execute("SELECT COUNT(*) FROM student_performance")
count1 = cursor.fetchone()[0]
print(f"\n📊 student_performance: {count1:,} records")

cursor.execute("SELECT COUNT(*) FROM student_term_summary")
count2 = cursor.fetchone()[0]
print(f"📊 student_term_summary: {count2:,} records")

# 2. Check districts
cursor.execute("""
    SELECT district, COUNT(*) as records
    FROM student_performance
    GROUP BY district
    ORDER BY records DESC
    LIMIT 5
""")
print("\n🏫 Top 5 Districts by Records:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,} records")

# 3. Check pass rates (Term 2) - Fixed boolean casting
cursor.execute("""
    SELECT 
        COUNT(*) as total_students,
        SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) as passing_40,
        ROUND(100.0 * SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate_40,
        SUM(CASE WHEN percentage >= 30 THEN 1 ELSE 0 END) as passing_30,
        ROUND(100.0 * SUM(CASE WHEN percentage >= 30 THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate_30
    FROM student_performance
    WHERE term = 2
""")
row = cursor.fetchone()
print(f"\n📈 Term 2 Performance:")
print(f"  Total records: {row[0]:,}")
print(f"  Pass rate (40%): {row[2]}% ({row[1]:,} students)")
print(f"  Pass rate (30%): {row[4]}% ({row[3]:,} students)")

# 4. Check summary table - Fixed boolean casting
cursor.execute("""
    SELECT 
        AVG(avg_percentage) as avg_score,
        SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) as passing_students,
        COUNT(*) as total_students,
        ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
    FROM student_term_summary
    WHERE term = 2
""")
row = cursor.fetchone()
if row:
    print(f"\n📊 Student Summary (Term 2):")
    print(f"  Average score: {row[0]:.2f}%")
    print(f"  Meeting basic pass: {row[1]:,}/{row[2]:,}")
    print(f"  Pass rate: {row[3]}%")

# 5. Check district-level summary - Fixed boolean casting
cursor.execute("""
    SELECT 
        district,
        COUNT(DISTINCT student_id) as students,
        ROUND(AVG(avg_percentage), 2) as avg_score,
        ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
    FROM student_term_summary
    WHERE term = 2
    GROUP BY district
    ORDER BY avg_score DESC
    LIMIT 5
""")
print("\n🏆 Top 5 Districts (Term 2):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} students, {row[2]}% avg, {row[3]}% pass rate")

# 6. Check subject difficulty (if subject column exists)
try:
    cursor.execute("""
        SELECT 
            subject,
            COUNT(*) as total_records,
            ROUND(AVG(percentage), 2) as avg_score,
            ROUND(100.0 * SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
        FROM student_performance
        WHERE term = 2
        GROUP BY subject
        ORDER BY avg_score ASC
        LIMIT 5
    """)
    print("\n📚 5 Most Difficult Subjects (Term 2):")
    for row in cursor.fetchall():
        if row[0]:
            print(f"  {row[0]}: {row[1]} records, {row[2]}% avg, {row[3]}% pass rate")
except Exception as e:
    print(f"\n⚠️ Subject data not available: {e}")

cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ Verification complete!")