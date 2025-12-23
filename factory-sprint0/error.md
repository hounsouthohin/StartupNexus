PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> docker compose logs factory-worker 
factory-worker  | Port 7233 on host temporal is now available.
factory-worker  |  * Serving Flask app 'worker'
factory-worker  |  * Debug mode: off
factory-worker  | WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
factory-worker  |  * Running on all addresses (0.0.0.0)
factory-worker  |  * Running on http://127.0.0.1:5000
factory-worker  |  * Running on http://172.18.0.9:5000
factory-worker  | Press CTRL+C to quit
factory-worker  | 2025-12-23T16:52:00.722804Z  WARN temporalio_sdk_core::worker::heartbeat: Worker heartbeating configured for runtime, but server version does not support it.
factory-worker  | 172.18.0.5 - - [23/Dec/2025 16:53:47] "POST /start-saas HTTP/1.1" 200 -
factory-worker  | Could not create 'dev' branch (it might already exist): Reference already exists: 422 {"message": "Reference already exists", "documentation_url": "https://docs.github.com/rest/git/refs#create-a-reference", "status": "422"} ({'activity_id': '4', 'activity_type': 'github_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-queue', 'workflow_id': 'saas-factory-6707', 'workflow_run_id': '085d90ff-2ca7-4862-8e73-572815508c8d', 'workflow_type': 'SaaSFactoryWorkflow'})
factory-worker  | Failed to create Pull Request (it might already exist): Validation Failed: 422 {"message": "Validation Failed", "errors": [{"resource": "PullRequest", "code": "custom", "message": "A pull request already exists for hounsouthohin:dev."}], "documentation_url": "https://docs.github.com/rest/pulls/pulls#create-a-pull-request", "status": "422"} ({'activity_id': '4', 'activity_type': 'github_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-queue', 'workflow_id': 'saas-factory-6707', 'workflow_run_id': '085d90ff-2ca7-4862-8e73-572815508c8d', 'workflow_type': 'SaaSFactoryWorkflow'})
PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> 





