# sa-education-analytics-pipeline
Automated Education Analytics Pipeline for Limpopo Province - AWS Serverless ETL with S3, Lambda, RDS, and SES
# 📊 South Africa Education Analytics Pipeline

> Automated serverless ETL pipeline for analyzing student performance data from Limpopo province schools.

![AWS Architecture](docs/architecture.png)

## 🎯 Project Overview

This project processes **27,858 student records** from 18 districts in Limpopo province, South Africa. It implements South African National Senior Certificate (NSC) promotion logic to identify at-risk students and provides automated daily performance reports.

### Key Features
- ✅ Serverless ETL pipeline (S3 → Lambda → RDS)
- ✅ South African NSC promotion logic implementation
- ✅ Automated daily email reports (SES)
- ✅ Data anonymization for privacy compliance
- ✅ SAS quality control integration
- ✅ Interactive dashboards (Power BI/Looker Studio)

## 🏗️ Architecture
┌─────────────────────────────────────────────────────────────────────────────┐
│ SA EDUCATION ANALYTICS PIPELINE │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ 📁 Local CSV Files │
│ ↓ │
│ ☁️ S3 Bucket (edu-data-raw-*) │
│ ↓ (S3 Trigger) │
│ ⚡ Lambda: load_education_data_to_rds │
│ ↓ │
│ 🗄️ RDS PostgreSQL (education_analytics) │
│ ├── student_performance (27,858 records) │
│ └── student_term_summary (27,858 records) │
│ ↓ │
│ ⚡ Lambda: send_daily_education_report │
│ ↓ (EventBridge: Daily at 8 AM) │
│ 📧 SES: Daily Email Report │
│ ↓ │
│ 📬 Stakeholder Inbox │
│ │
└─────────────────────────────────────────────────────────────────────────────┘


## 📈 Key Insights

| Metric | Value |
|--------|-------|
| **Total Students** | 27,858 |
| **Districts** | 18 |
| **Subjects** | 50+ |
| **Term 2 Pass Rate (40%)** | 42.82% |
| **Term 2 Pass Rate (30%)** | 76.88% |
| **At-Risk Students** | 15,922 |

### Top Performing Districts (Term 2)

| District | Avg Score | Pass Rate |
|----------|-----------|-----------|
| Polokwane | 50.96% | 55.56% |
| Palala/Waterberg | 52.00% | 52.27% |
| Capricorn | 45.58% | 42.19% |

### Bottom Performing Districts (Need Support)

| District | Avg Score | Pass Rate |
|----------|-----------|-----------|
| Mopani | 36.59% | 23.64% |
| Waterberg 2 | 37.54% | 26.32% |
| Mopani East | 40.36% | 33.85% |

## 🛠️ Technologies Used

| Category | Technologies |
|----------|--------------|
| **Cloud** | AWS (S3, Lambda, RDS, SES, EventBridge, VPC, IAM) |
| **Data Processing** | Python (Pandas, pg8000), PostgreSQL |
| **Analytics** | SAS (Quality Control), SQL |
| **Orchestration** | EventBridge (Scheduled Events) |
| **Infrastructure** | Serverless Architecture |
| **Version Control** | Git, GitHub |

## 📁 Project Structure
sa-education-analytics-pipeline/
├── scripts/
│ ├── explore_data.py # Initial data exploration
│ ├── preprocess_data.py # Data cleaning & anonymization
│ ├── clean_districts.py # District name standardization
│ ├── create_schema.py # RDS schema creation
│ ├── check_rds_data.py # Data verification
│ └── verify_rds.py # RDS validation script
├── sas/
│ └── 01_initial_analysis.sas # SAS quality control
├── lambda/
│ ├── load_education_data_to_rds.py
│ └── send_daily_education_report.py
├── reports/
│ ├── district_performance.csv
│ ├── subject_performance.csv
│ └── quality_control_report.txt
├── viz/
│ ├── initial_distribution.png
│ └── district_ranking.png
├── .gitignore
├── README.md
└── requirements.txt

## 🚀 Deployment

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS CLI
aws configure

Steps
1. Create S3 buckets
2. Deploy Lambda functions
3. Set up RDS PostgreSQL
4. Configure EventBridge schedule
5. Verify email in SES

🧪 Data Quality
- SAS Quality Control: Generated statistical reports for data validation
- Anonymization: SHA-256 hashing for student privacy
- Standardization: District name mapping across 18 variations

👥 Use Cases
- Education Officials: Monitor district and school performance
- School Principals: Track student progress and identify at-risk students
- Teachers: Understand subject difficulty patterns
- Policy Makers: Evaluate education policy effectiveness

📬 Automated Reports
Daily email reports include:
- Overall pass rates (40% and 30% thresholds)
- Top and bottom performing districts
- At-risk student counts
- Most difficult subjects

🔒 Security
- Data anonymization (no PII in cloud)
- IAM role-based access control
- VPC configuration for RDS
- SES sandbox protection

🎓 South African NSC Promotion Requirements
The pipeline implements the official SA promotion requirements:
- Pass 6 out of 7 subjects (at 40%)
- At least 40% in Home Language
- Pass Life Orientation
- At least 30% in two other subjects
- At least 30% in three additional subjects

📄 License
MIT License - see LICENSE file for details.

👨‍💻 Author
Ndumiso Nkosi - NdNkosi

🙏 Acknowledgments
- Limpopo Department of Education
- AWS Community Builders
- SAS Academic Program



