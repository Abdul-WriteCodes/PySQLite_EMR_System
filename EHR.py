import sqlite3
from datetime import datetime

# Create or connect to the database
conn = sqlite3.connect('ehr_system.db')
cursor = conn.cursor()

# Step 1: Create tables
def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS Company_Info (
                        company_id INTEGER PRIMARY KEY,
                        company_name TEXT,
                        company_address TEXT,
                        contact_number TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Patient (
                        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT,
                        last_name TEXT,
                        date_of_birth TEXT,
                        gender TEXT,
                        address TEXT,
                        contact_number TEXT
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Consultation_Record (
                        consultation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER,
                        complaints TEXT,
                        consultation_date TEXT,
                        FOREIGN KEY (patient_id) REFERENCES Patient(patient_id)
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Medical_Service (
                        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        consultation_id INTEGER,
                        service_description TEXT,
                        prescribed_medication TEXT,
                        FOREIGN KEY (consultation_id) REFERENCES Consultation_Record(consultation_id)
                    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Patient_Consultation_History (
                        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER,
                        consultation_id INTEGER,
                        timestamp TEXT,
                        FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
                        FOREIGN KEY (consultation_id) REFERENCES Consultation_Record(consultation_id)
                    )''')
    
    conn.commit()

# Step 2: Register a new patient interactively
def register_patient():
    print("\n--- Register New Patient ---")
    first_name = input("Enter patient's first name: ")
    last_name = input("Enter patient's last name: ")
    date_of_birth = input("Enter patient's date of birth (YYYY-MM-DD): ")
    gender = input("Enter patient's gender (Male | Female): ")
    address = input("Enter patient's address: ")
    contact_number = input("Enter patient's contact number: ")
    
    # Insert patient data into the database
    cursor.execute('''INSERT INTO Patient (first_name, last_name, date_of_birth, gender, address, contact_number)
                      VALUES (?, ?, ?, ?, ?, ?)''', 
                   (first_name, last_name, date_of_birth, gender, address, contact_number))
    conn.commit()
    
    # Get the patient ID for the newly registered patient
    patient_id = cursor.lastrowid
    print(f"\nPatient Registered Successfully! The Card ID of the patient with name {first_name} {last_name} is: {patient_id}")
    
    return patient_id

# Step 3: Record a consultation with health complaints interactively
def record_consultation(patient_id):
    print("\n--- Record New Consultation ---")
    complaints = input("Enter the health complaints discussed with the physician: ")
    consultation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Insert consultation data into the database
    cursor.execute('''INSERT INTO Consultation_Record (patient_id, complaints, consultation_date)
                      VALUES (?, ?, ?)''', 
                   (patient_id, complaints, consultation_date))
    conn.commit()
    
    # Get the consultation ID for the newly recorded consultation
    consultation_id = cursor.lastrowid
    print(f"\nConsultation recorded successfully! The latest consultation ID is: {consultation_id}")
    
    return consultation_id

# Step 4: Record medical services provided interactively
def record_medical_service(consultation_id):
    print("\n--- Record Medical Service ---")
    service_description = input("Enter the service description provided by the physician: ")
    prescribed_medication = input("Enter the prescribed medication (if any): ")
    
    # Insert medical service data into the database
    cursor.execute('''INSERT INTO Medical_Service (consultation_id, service_description, prescribed_medication)
                      VALUES (?, ?, ?)''', 
                   (consultation_id, service_description, prescribed_medication))
    conn.commit()
    
    print("\nMedical service recorded successfully!")

# Step 5: Retrieve and display the consultation history of a patient
def get_patient_history(patient_id):
    print(f"\n--- Consultation History for Patient ID {patient_id}---")
    
    cursor.execute('''SELECT c.consultation_id, c.complaints, c.consultation_date, m.service_description, m.prescribed_medication 
                      FROM Consultation_Record c
                      LEFT JOIN Medical_Service m ON c.consultation_id = m.consultation_id
                      WHERE c.patient_id = ? ORDER BY c.consultation_date DESC''', (patient_id,))
    
    consultations = cursor.fetchall()
    
    if consultations:
        for consultation in consultations:
            print(f"Consultation ID: {consultation[0]}")
            print(f"Complaints: {consultation[1]}")
            print(f"Consultation Date: {consultation[2]}")
            print(f"Medical Service: {consultation[3]}")
            print(f"Prescribed Medication: {consultation[4]}")
            print('-' * 40)
    else:
        print("No consultation history found for this patient.")

# Step 6: Main interactive program loop
def main():
    create_tables()  # Ensure the tables are created
    
    while True:
        print("\n--- Welcome to the Electronic Health Record (EHR) System ---")
        print("1. Register New Patient")
        print("2. Record Consultation and Health Complaints")
        print("3. Record Medical Services Provided")
        print("4. View Patient's Consultation History")
        print("5. Exit")
        
        choice = input("Select an operation to perform [1] [2] [3] [4] [5]: ")
        
        if choice == '1':
            patient_id = register_patient()
        elif choice == '2':
            patient_id = int(input("Enter the patient ID: "))
            record_consultation(patient_id)
        elif choice == '3':
            consultation_id = int(input("Enter the consultation ID: "))
            record_medical_service(consultation_id)
        elif choice == '4':
            patient_id = int(input("Enter the patient ID: "))
            get_patient_history(patient_id)
        elif choice == '5':
            print("Exiting the system. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

# Run the interactive program
if __name__ == "__main__":
    main()

# Close the database connection after use
conn.close()
