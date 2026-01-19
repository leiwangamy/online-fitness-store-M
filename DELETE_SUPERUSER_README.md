# Delete Superuser Scripts

This directory contains scripts to delete superusers from the Django database.

## Available Scripts

### 1. `delete_superuser.py` - Delete a Specific Superuser

Deletes a single superuser by email address.

**Usage:**
1. Open the file `delete_superuser.py` in a text editor
2. Change the `EMAIL` variable (line 21) to the email of the superuser you want to delete
3. Run the script:

```bash
# On Windows (PowerShell or Command Prompt)
python delete_superuser.py

# Or if you have a virtual environment:
venv\Scripts\Activate.ps1  # PowerShell
# or
venv\Scripts\activate.bat  # Command Prompt
python delete_superuser.py
```

**What it does:**
- Shows the current database connection details
- Finds the user by email address
- Displays user information (username, email, superuser status, related objects)
- Deletes the user and all related objects (cascading delete)
- Verifies the deletion
- Lists remaining superusers

**Example:**
```python
# In delete_superuser.py, line 21:
EMAIL = 'user@example.com'  # Change this to the email you want to delete
```

---

### 2. `delete_all_superusers.py` - Delete All Superusers

Deletes **ALL** superusers from the database.

⚠️ **WARNING:** This will delete all superusers. Use with caution!

**Usage:**
```bash
# On Windows (PowerShell or Command Prompt)
python delete_all_superusers.py

# Or if you have a virtual environment:
venv\Scripts\Activate.ps1  # PowerShell
# or
venv\Scripts\activate.bat  # Command Prompt
python delete_all_superusers.py
```

**What it does:**
- Shows the current database connection details
- Lists all superusers found in the database
- Deletes all superusers
- Verifies deletion
- Shows instructions to create a new superuser

---

## Prerequisites

1. **Python 3.x** installed
2. **Django** installed (or available in your virtual environment)
3. **Database connection** configured in your `.env` file
4. **Project directory**: Make sure you're in the project root directory when running scripts

## Step-by-Step Instructions

### To Delete a Specific Superuser:

1. **Open a terminal/command prompt:**
   - PowerShell or Command Prompt on Windows
   - Or use the terminal in VS Code

2. **Navigate to the project directory:**
   ```powershell
   cd "C:\Users\Lei\Documents\VS Code Projects\online-fitness-store M"
   ```

3. **Activate your virtual environment (if you have one):**
   ```powershell
   # If you have a venv in the project:
   venv\Scripts\Activate.ps1
   ```
   If you don't have a virtual environment, skip this step.

4. **Edit the script to set the email:**
   - Open `delete_superuser.py` in your text editor
   - Change line 21: `EMAIL = 'leiwasoc@gmail.com'` to the email you want to delete
   - Save the file

5. **Run the script:**
   ```powershell
   python delete_superuser.py
   ```

6. **Check the output:**
   - The script will show database connection info
   - Display user details
   - Confirm deletion
   - List remaining superusers

### To Delete All Superusers:

1. **Open a terminal/command prompt**
2. **Navigate to the project directory**
3. **Activate virtual environment (if needed)**
4. **Run the script:**
   ```powershell
   python delete_all_superusers.py
   ```
5. **Create a new superuser after deletion:**
   ```powershell
   python manage.py createsuperuser
   ```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'django'"

**Solution:** Activate your virtual environment first, or install Django:
```bash
pip install django
```

### Error: "User with email 'xxx' not found"

**Solution:** 
- Double-check the email address in the script
- Make sure the user exists in the database
- The script will list all current superusers for reference

### Error: "could not connect to server"

**Solution:**
- Check your `.env` file has correct database credentials
- Ensure your database server is running
- Verify database connection settings in `settings.py`

## Notes

- These scripts delete users **permanently** from the database
- Related objects (Seller profiles, EmailAddress records) will be deleted if foreign keys are set to CASCADE
- Always verify the database connection before running deletion scripts
- It's recommended to back up your database before deleting users

## Alternative: Django Management Command

You can also use the Django management command:

```bash
python manage.py delete_superuser user@example.com
```

This requires the `core/management/commands/delete_superuser.py` file to be present.

## Related Files

- `delete_superuser.py` - Delete a specific superuser by email
- `delete_all_superusers.py` - Delete all superusers
- `cleanup_superusers.py` - Interactive version to delete all superusers (requires confirmation)
- `core/management/commands/delete_superuser.py` - Django management command version

