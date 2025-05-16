# Fix Scenarios Stuck in Pending/Running State

## Description
This PR fixes the issue where scenarios get stuck in pending/running state and fail to create model.lp files. The changes ensure proper connection between the Streamlit frontend and the VRP solver backend so users can successfully run scenarios and view results.

## Changes
- Fixed the `st.rerun()` call in scenario_builder.py that was interrupting the solver execution
- Updated the subprocess call to use `sys.executable` instead of "python" to ensure the correct Python interpreter is used
- Added proper output directory structure with explicit checks for model.lp file creation
- Implemented file checking in both scenario and output directories to handle inconsistent file locations
- Added robust error handling and logging for better debugging
- Created test scripts to verify the VRP solver integration and Streamlit application functionality

## Testing
- Tested the VRP solver integration directly using test_integration.py
- Verified the Streamlit application works correctly with the changes using test_app.py
- Confirmed scenarios can be created, run, and viewed successfully

Link to Devin run: https://app.devin.ai/sessions/c76719696c314393ba103cebd8643429
Requested by: Aman Kumar
