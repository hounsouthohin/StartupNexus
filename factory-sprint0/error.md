PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> docker compose logs factory-worker
factory-worker  | Port 6333 on host qdrant is now available.
factory-worker  | ✅ Connexion à Qdrant réussie !
factory-worker  | La collection 'factory_standards' existe déjà.
factory-worker  | Début de l'embedding et de l'upload des standards...
factory-worker  | ✅ 19 standards ont été injectés/mis à jour dans Qdrant ! 🚀
factory-worker  |    L'Agent Architecte peut maintenant utiliser le RAG pour des specs et diagrammes de haute qualité.
factory-worker  | Port 7233 on host temporal is now available.
factory-worker  |  * Serving Flask app 'worker'
factory-worker  |  * Debug mode: off
factory-worker  | WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
factory-worker  |  * Running on all addresses (0.0.0.0)
factory-worker  |  * Running on http://127.0.0.1:5000
factory-worker  |  * Running on http://172.18.0.8:5000
factory-worker  | Press CTRL+C to quit
factory-worker  | 2025-12-29T07:05:40.909910Z  WARN temporalio_sdk_core::worker::heartbeat: Worker heartbeating configured for runtime, but server version does not support it.
factory-worker  | 172.18.0.4 - - [29/Dec/2025 07:06:27] "POST /start-saas HTTP/1.1" 200 -
factory-worker  | 2025-12-29T07:08:23.038816Z  WARN temporalio_sdk_core::worker::workflow: Query not found when attempting to respond to it error=Status { code: NotFound, message: "query task not found, or already expired", details: b"\x08\x05\x12(query task not found, or already expired\x1aB\n@type.googleapis.com/temporal.api.errordetails.v1.NotFoundFailure", metadata: MetadataMap { headers: {"content-type": "application/grpc"} }, source: None }
factory-worker  | 2025-12-29T07:08:23.043903Z  WARN temporalio_sdk_core::worker::workflow: Query not found when attempting to respond to it error=Status { code: NotFound, message: "query task not found, or already expired", details: b"\x08\x05\x12(query task not found, or already expired\x1aB\n@type.googleapis.com/temporal.api.errordetails.v1.NotFoundFailure", metadata: MetadataMap { headers: {"content-type": "application/grpc"} }, source: None }
factory-worker  | Completing activity as failed ({'activity_id': '3', 'activity_type': 'test_coverage_activity', 'attempt': 1, 'namespace': 'default', 'task_queue': 'factory-queue', 'workflow_id': 'saas-factory-14462', 'workflow_run_id': '019b68ee-0244-7b45-a2e3-fef0c0f21094', 'workflow_type': 'SaaSFactoryWorkflow'})
factory-worker  | Traceback (most recent call last):
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 316, in _handle_start_activity_task
factory-worker  |     result = await self._execute_activity(
factory-worker  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 628, in _execute_activity
factory-worker  |     return await impl.execute_activity(input)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 823, in execute_activity
factory-worker  |     return await input.fn(*input.args)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/workflows/activities/test_coverage_activity.py", line 15, in test_coverage_activity
factory-worker  |     test_agent_output = test_coverage_agent(dev_result_files)
factory-worker  |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 134, in test_coverage_agent
factory-worker  |     final_state = app.invoke(
factory-worker  |                   ^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 3068, in invoke
factory-worker  |     for chunk in self.stream(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 2643, in stream
factory-worker  |     for _ in runner.tick(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_runner.py", line 167, in tick
factory-worker  |     run_with_retry(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_retry.py", line 42, in run_with_retry
factory-worker  |     return task.proc.invoke(task.input, config)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 656, in invoke
factory-worker  |     input = context.run(step.invoke, input, config, **kwargs)
factory-worker  |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 400, in invoke
factory-worker  |     ret = self.func(*args, **kwargs)
factory-worker  |           ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 81, in test_runner_node
factory-worker  |     test_results = run_tests(project_dir='.')
factory-worker  |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  | TypeError: 'StructuredTool' object is not callable
factory-worker  | During task with name 'run_tests' and id '4cdd0362-f974-6b9d-c31d-717887a7182d'
factory-worker  | Completing activity as failed ({'activity_id': '3', 'activity_type': 'test_coverage_activity', 'attempt': 2, 'namespace': 'default', 'task_queue': 'factory-queue', 'workflow_id': 'saas-factory-14462', 'workflow_run_id': '019b68ee-0244-7b45-a2e3-fef0c0f21094', 'workflow_type': 'SaaSFactoryWorkflow'})
factory-worker  | Traceback (most recent call last):
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 316, in _handle_start_activity_task
factory-worker  |     result = await self._execute_activity(
factory-worker  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 628, in _execute_activity
factory-worker  |     return await impl.execute_activity(input)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 823, in execute_activity
factory-worker  |     return await input.fn(*input.args)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/workflows/activities/test_coverage_activity.py", line 15, in test_coverage_activity
factory-worker  |     test_agent_output = test_coverage_agent(dev_result_files)
factory-worker  |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 134, in test_coverage_agent
factory-worker  |     final_state = app.invoke(
factory-worker  |                   ^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 3068, in invoke
factory-worker  |     for chunk in self.stream(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 2643, in stream
factory-worker  |     for _ in runner.tick(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_runner.py", line 167, in tick
factory-worker  |     run_with_retry(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_retry.py", line 42, in run_with_retry
factory-worker  |     return task.proc.invoke(task.input, config)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 656, in invoke
factory-worker  |     input = context.run(step.invoke, input, config, **kwargs)
factory-worker  |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 400, in invoke
factory-worker  |     ret = self.func(*args, **kwargs)
factory-worker  |           ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 81, in test_runner_node
factory-worker  |     test_results = run_tests(project_dir='.')
factory-worker  |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  | TypeError: 'StructuredTool' object is not callable
factory-worker  | During task with name 'run_tests' and id '4d194345-ba1d-008e-0706-8ea060f7a8b7'
factory-worker  | Completing activity as failed ({'activity_id': '3', 'activity_type': 'test_coverage_activity', 'attempt': 3, 'namespace': 'default', 'task_queue': 'factory-queue', 'workflow_id': 'saas-factory-14462', 'workflow_run_id': '019b68ee-0244-7b45-a2e3-fef0c0f21094', 'workflow_type': 'SaaSFactoryWorkflow'})
factory-worker  | Traceback (most recent call last):
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 316, in _handle_start_activity_task
factory-worker  |     result = await self._execute_activity(
factory-worker  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 628, in _execute_activity
factory-worker  |     return await impl.execute_activity(input)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/temporalio/worker/_activity.py", line 823, in execute_activity
factory-worker  |     return await input.fn(*input.args)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/workflows/activities/test_coverage_activity.py", line 15, in test_coverage_activity
factory-worker  |     test_agent_output = test_coverage_agent(dev_result_files)
factory-worker  |                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 134, in test_coverage_agent
factory-worker  |     final_state = app.invoke(
factory-worker  |                   ^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 3068, in invoke
factory-worker  |     for chunk in self.stream(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/main.py", line 2643, in stream
factory-worker  |     for _ in runner.tick(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_runner.py", line 167, in tick
factory-worker  |     run_with_retry(
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/pregel/_retry.py", line 42, in run_with_retry
factory-worker  |     return task.proc.invoke(task.input, config)
factory-worker  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 656, in invoke
factory-worker  |     input = context.run(step.invoke, input, config, **kwargs)
factory-worker  |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/usr/local/lib/python3.11/site-packages/langgraph/_internal/_runnable.py", line 400, in invoke
factory-worker  |     ret = self.func(*args, **kwargs)
factory-worker  |           ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  |   File "/app/agents/test_coverage.py", line 81, in test_runner_node
factory-worker  |     test_results = run_tests(project_dir='.')
factory-worker  |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^
factory-worker  | TypeError: 'StructuredTool' object is not callable
factory-worker  | During task with name 'run_tests' and id '55a2b584-3a6f-43af-d5d3-bda83a93d017'
PS C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0> 