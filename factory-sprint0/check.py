
import json
data = json.load(open('/app/logs/shadow/learner_shadow_log.json'))
events = [e for e in data.get('suggested_standards', []) if e.get('metric') == 'dev_test_run']
recent = events[-6:]
for e in recent:
    v = e.get('value', {})
    print(e.get('project_name'), 'build=', v.get('build_success'), 'files=', v.get('files_count'))
