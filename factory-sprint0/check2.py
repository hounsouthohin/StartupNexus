
import json
data = json.load(open('/app/logs/shadow/learner_shadow_log.json'))
events = [e for e in data.get('suggested_standards', []) if e.get('metric') == 'dev_test_run']
recent = events[-6:]
for e in recent:
    v = e.get('value', {})
    if not v.get('build_success'):
        print('PROJECT:', e.get('project_name'))
        print('ERROR:', v.get('last_build_error', 'ABSENT')[:200])
        print('COMMAND:', v.get('last_failed_command', 'ABSENT'))
        print()
