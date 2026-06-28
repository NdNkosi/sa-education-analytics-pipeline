import boto3
import pg8000
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# RDS Connection Details 
RDS_HOST = os.environ.get('RDS_HOST')
RDS_USER = os.environ.get('RDS_USER')
RDS_PASSWORD = os.environ.get('RDS_PASSWORD')
RDS_DATABASE = os.environ.get('RDS_DATABASE')
RDS_PORT = int(os.environ.get('RDS_PORT', 5432))

# SES Configuration
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'nkosindumis@gmail.com')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'nkosindumis@gmail.com')

ses_client = boto3.client('ses', region_name='af-south-1')

def connect_to_rds():
    try:
        conn = pg8000.connect(
            host=RDS_HOST,
            database=RDS_DATABASE,
            user=RDS_USER,
            password=RDS_PASSWORD,
            port=RDS_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"❌ RDS connection failed: {e}")
        return None

def get_summary_data():
    """Fetch summary data from RDS"""
    conn = connect_to_rds()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    # 1. Overall pass rates (Term 2)
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
    pass_data = cursor.fetchone()
    
    # 2. Basic pass rate from summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_students,
            SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) as passing,
            ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
        FROM student_term_summary
        WHERE term = 2
    """)
    summary_data = cursor.fetchone()
    
    # 3. Top 3 districts
    cursor.execute("""
        SELECT 
            district,
            ROUND(AVG(avg_percentage), 2) as avg_score,
            ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
        FROM student_term_summary
        WHERE term = 2
        GROUP BY district
        ORDER BY pass_rate DESC
        LIMIT 3
    """)
    top_districts = cursor.fetchall()
    
    # 4. Bottom 3 districts
    cursor.execute("""
        SELECT 
            district,
            ROUND(AVG(avg_percentage), 2) as avg_score,
            ROUND(100.0 * SUM(CASE WHEN meets_basic_pass THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
        FROM student_term_summary
        WHERE term = 2
        GROUP BY district
        ORDER BY pass_rate ASC
        LIMIT 3
    """)
    bottom_districts = cursor.fetchall()
    
    # 5. At-risk student count
    cursor.execute("""
        SELECT COUNT(DISTINCT student_id) as at_risk
        FROM student_term_summary
        WHERE term = 2
          AND meets_basic_pass = FALSE
    """)
    at_risk = cursor.fetchone()[0]
    
    # 6. Top 5 difficult subjects
    cursor.execute("""
        SELECT 
            subject,
            ROUND(AVG(percentage), 2) as avg_score,
            ROUND(100.0 * SUM(CASE WHEN percentage >= 40 THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
        FROM student_performance
        WHERE term = 2 AND subject != 'Unknown_Subject'
        GROUP BY subject
        ORDER BY avg_score ASC
        LIMIT 5
    """)
    difficult_subjects = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        'pass_data': pass_data,
        'summary_data': summary_data,
        'top_districts': top_districts,
        'bottom_districts': bottom_districts,
        'at_risk': at_risk,
        'difficult_subjects': difficult_subjects
    }

def generate_html_email(data):
    """Generate HTML email content"""
    
    pass_data = data['pass_data']
    summary_data = data['summary_data']
    top_districts = data['top_districts']
    bottom_districts = data['bottom_districts']
    at_risk = data['at_risk']
    difficult_subjects = data['difficult_subjects']
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a5276; border-bottom: 3px solid #2980b9; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 25px; }}
            .summary-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            .alert {{ background: #fdf2e9; border-left: 4px solid #e67e22; padding: 10px 15px; margin: 15px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Education Performance Daily Summary</h1>
            <p><strong>{today}</strong></p>
            
            <div class="summary-box">
                <h2>📈 Overall Performance (Term 2)</h2>
                <div class="metric">
                    <div class="metric-value">{pass_data[0]:,}</div>
                    <div class="metric-label">Total Students</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{pass_data[1]:,}</div>
                    <div class="metric-label">Passed (40%)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{pass_data[2]}%</div>
                    <div class="metric-label">Pass Rate (40%)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{pass_data[3]:,}</div>
                    <div class="metric-label">Passed (30%)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{pass_data[4]}%</div>
                    <div class="metric-label">Pass Rate (30%)</div>
                </div>
            </div>
            
            <h2>🎯 Basic Pass Rate</h2>
            <div class="summary-box">
                <div class="metric">
                    <div class="metric-value">{summary_data[1]:,}/{summary_data[0]:,}</div>
                    <div class="metric-label">Meeting Basic Pass Requirements</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary_data[2]}%</div>
                    <div class="metric-label">Basic Pass Rate</div>
                </div>
            </div>
            
            <h2>🏆 Top 3 Districts</h2>
            <table>
                <tr>
                    <th>District</th>
                    <th>Average Score</th>
                    <th>Pass Rate</th>
                </tr>
    """
    
    for district in top_districts:
        html += f"""
                <tr>
                    <td><strong>{district[0]}</strong></td>
                    <td>{district[1]}%</td>
                    <td>{district[2]}%</td>
                </tr>
        """
    
    html += """
            </table>
            
            <h2>⚠️ Bottom 3 Districts (Need Support)</h2>
            <table>
                <tr>
                    <th>District</th>
                    <th>Average Score</th>
                    <th>Pass Rate</th>
                </tr>
    """
    
    for district in bottom_districts:
        html += f"""
                <tr>
                    <td><strong>{district[0]}</strong></td>
                    <td>{district[1]}%</td>
                    <td>{district[2]}%</td>
                </tr>
        """
    
    html += f"""
            </table>
            
            <div class="alert">
                <h3>🚨 At-Risk Students</h3>
                <p><strong>{at_risk:,} students</strong> are currently at risk of not meeting promotion requirements.</p>
                <p style="font-size: 14px; color: #7f8c8d;">These students need immediate intervention support.</p>
            </div>
    """
    
    if difficult_subjects:
        html += """
            <h2>📚 5 Most Difficult Subjects</h2>
            <table>
                <tr>
                    <th>Subject</th>
                    <th>Average Score</th>
                    <th>Pass Rate</th>
                </tr>
        """
        
        for subject in difficult_subjects:
            html += f"""
                <tr>
                    <td>{subject[0]}</td>
                    <td>{subject[1]}%</td>
                    <td>{subject[2]}%</td>
                </tr>
            """
        
        html += """
            </table>
        """
    
    html += f"""
            <div class="footer">
                <p>This is an automated report generated from the Education Analytics Pipeline.</p>
                <p>Data includes {pass_data[0]:,} student records from Limpopo province.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(html_body):
    """Send email via SES"""
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [RECIPIENT_EMAIL]
            },
            Message={
                'Subject': {
                    'Data': f'📊 Education Performance Summary - {datetime.now().strftime("%Y-%m-%d")}'
                },
                'Body': {
                    'Html': {
                        'Data': html_body
                    }
                }
            }
        )
        logger.info(f"✅ Email sent successfully! Message ID: {response['MessageId']}")
        return response
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return None

def lambda_handler(event, context):
    """Main Lambda handler - handles both S3 triggers and manual tests"""
    logger.info("🚀 Generating daily education report")
    
    # Check if this is an S3 event or manual test
    if 'Records' in event:
        # This is an S3 event - we can ignore the S3 part and just run the report
        logger.info("📁 Triggered by S3 event - generating report")
    else:
        # This is a manual test or scheduled event
        logger.info("📝 Manual or scheduled trigger - generating report")
    
    # Get data from RDS
    data = get_summary_data()
    if not data:
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to fetch data from RDS')
        }
    
    # Generate HTML email
    html_body = generate_html_email(data)
    
    # Send email
    response = send_email(html_body)
    
    if response:
        return {
            'statusCode': 200,
            'body': json.dumps('✅ Daily report sent successfully!')
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps('❌ Failed to send email')
        }