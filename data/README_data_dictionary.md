# CROSSWALK synthetic datasets - data dictionary

All data is **synthetic prototype data** (fictional people, emails, colleges). It does not represent real students or real employment statistics.
Multi-value fields use `|`. Passwords are stored as unsalted SHA-256 hashes of demo passwords (prototype only):
Student@123 / College@123 / Designer@123.

## Fields taken from the CROSSWALK spec (as pasted)
Student: Student_Id, Degree, Course, Specialization, College, Technical_Skills, Soft_Skills, Certifications, Areas_Of_Interest, Preferred_Industries, Career_Preferences, Profile_Status.
Education: Education_Id, Degree, Course, Specialization, College. Employment: Occupation_Id, Job_Title, Industry (+ added analytics fields).
Skills: Skill_Id, Skill_Name, Category, Demand_Trend. Users: User_Id, Name, Email, Password, Role.

## IMPLEMENTATION CHOICES (not stated in the pasted spec)
- `career_skills.csv` link table (Career/Job relationship for skills); `Requirement_Type` Required/Preferred.
- `students.User_Id` (links a profile to a login); `Password_Hash` instead of plain `Password`.
- Student skills / career preferences are stored as **names** (as a profile form would collect them); IDs are resolved by joining on name.
- `label_mappings.csv` (raw -> standard labels) for Module 3 StandardizeLabels.
- Education sub-score weights 0.4 degree / 0.3 course / 0.3 specialization; interest sub-score 0.5 areas-of-interest overlap + 0.5 preferred-industry match; skill sub-score = share of Required career skills the student has. Only the 40/40/20 split comes from the spec.
- Fuzzy-match thresholds in data_quality_test.csv (>=0.90 auto, 0.60-0.89 review, <0.60 unmapped).
- No alignment score is stored anywhere; compute it in the app.

## Files
| File | Columns |
|---|---|
| skills.csv | Skill_Id, Skill_Name, Category (Technical/Soft), Domain, Demand_Trend (Rising/Stable/Declining) |
| careers.csv | Career_Id, Career_Name, Industry, Min_Education_Level, Required_Degrees, Preferred_Courses, Preferred_Specializations, Related_Interest_Areas, Short_Description |
| career_skills.csv | Career_Id, Skill_Id, Requirement_Type |
| courses.csv | Course_Id, Course_Name, Skills_Covered (skill names), Level, Duration_Weeks - learning courses for recommendations |
| curriculum.csv | Subject_Id, Subject_Name, Degree, Course, Semester, Credits, Subject_Type, Skills_Taught (skill names) |
| education.csv | Education_Id, Degree, Course, Specialization, College - 7 rows use raw degree variants on purpose |
| employment.csv | Occupation_Id, Job_Title, Industry, Degree, Course, Specialization, College, Graduation_Year, Employment_Status, Experience_Level, Previous_Job_Title |
| students.csv | Student_Id, User_Id + the 12 spec fields |
| users.csv | User_Id, Name, Email, Password_Hash, Role (Student / College/University / Curriculum Designer) |
| label_mappings.csv | Mapping_Id, Label_Type (Degree/Job_Title/Skill/Industry), Raw_Label, Standard_Label |
| data_quality_test.csv | Test_Id, Category, Module, Target_Dataset, Input_Record (key=value;...), Issue_Description, Expected_System_Behavior, Review_Log_Expected, Match_Confidence |

## Intentional irregularities in the MAIN files (everything else is clean)
- students.csv: 8 Incomplete profiles - STU005, STU013, STU019, STU027, STU033, STU042, STU050, STU058 (one required education field blank).
- education.csv: 7 rows with raw degree labels (B.Sc, BSc, B.Tech, BTech, B.Com, MSc, MBA, ...).
- employment.csv: ~5 raw degree labels, ~10 raw job-title variants, a few raw industry labels, and 6 `Seeking Employment` rows where Job_Title/Industry are blank by design (these are valid outcomes, not defects).
- data_quality_test.csv holds all Module 11 test inputs; those records are NOT in the main files.

## Alignment demo
Alignment is designed so that, for each student's first Career_Preferences entry, roughly 16 students score High (>=0.70), 22 Medium (0.40-0.69), 14 Low (<0.40), and 8 are Incomplete.
