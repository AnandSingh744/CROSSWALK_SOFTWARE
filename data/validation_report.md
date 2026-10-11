# CROSSWALK synthetic data - validation report

## Row counts
- users.csv: 70 rows
- students.csv: 60 rows
- education.csv: 60 rows
- employment.csv: 80 rows
- skills.csv: 69 rows
- careers.csv: 54 rows
- career_skills.csv: 451 rows
- courses.csv: 66 rows
- curriculum.csv: 68 rows
- label_mappings.csv: 67 rows
- data_quality_test.csv: 36 rows

## Uniques / primary keys
- unique skills 69 (technical 53, soft 16); unique careers 54; unique courses 66; unique curriculum subjects 68; unique students 60; users 70
- duplicate primary IDs in any main dataset: NONE (asserted)

## Relationship checks
- broken foreign keys / vocabulary errors: 0 (none)
- skills not used by any career: none
- skills not covered by any learning course: none
- skills never taught by any curriculum subject (curriculum-gap material): 14 of 69
- roles: {'Student': 60, 'College/University': 5, 'Curriculum Designer': 5}

## Intended-defect inventory (main datasets)
- Incomplete student profiles (blank required education field, Profile_Status=Incomplete): 8 -> ['STU005', 'STU013', 'STU019', 'STU027', 'STU033', 'STU042', 'STU050', 'STU058']
- Raw degree variants in education.csv: 7; in employment.csv: 5
- Raw job-title variants in employment.csv: 10; raw industry variants: 1
- Seeking Employment rows (Job_Title and Industry blank BY DESIGN): 6
- data_quality_test.csv cases: 36

## Alignment spread (check only - NOT stored in any CSV; first career preference)
- bands (complete profiles): {'Low<0.40': 14, 'Medium 0.40-0.69': 22, 'High>=0.70': 16}
- design tier high: n=16 min=0.78 max=1.00 mean=0.92
- design tier medium: n=22 min=0.41 max=0.63 mean=0.51
- design tier low: n=14 min=0.08 max=0.25 mean=0.13

## Employment sanity: status {'Employed': 69, 'Seeking Employment': 6, 'Self-Employed': 5}; top titles [('Web Developer', 8), ('Data Analyst', 6), ('Financial Analyst', 5), ('Cybersecurity Analyst', 5), ('Cloud Engineer', 4)]