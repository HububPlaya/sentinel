---
name: debug-pipeline
description: Trigger and debug a real run of the snack-recommender CodePipeline/CodeBuild/Elastic Beanstalk pipeline in this repo — poll to completion, identify the failed stage, and pull a clean CodeBuild or EB log without the Windows Git Bash path/encoding traps that make this slow by hand.
---

# Debug Pipeline

Use this whenever a change needs verifying against a *real* deploy in this repo (per CLAUDE.md's
"Verifying infra/pipeline fixes" — `cdk deploy` is not the same as a fix being merged, and CI
passing is not evidence for a bug that's specifically a CI-vs-real-deploy gap). Built out of the
real debugging session that fixed #346, where this exact loop ran a dozen times by hand.

## 0. Before triggering anything

If you're verifying a source-level fix (app code, `requirements.txt`, `.platform/hooks/`,
buildspec logic), **confirm it's actually merged to `main`** first — the pipeline's
`GitHubSourceAction` only ever builds from `main` on GitHub, regardless of what's deployed locally
via `cdk deploy`. `cdk deploy` updates the live CodeBuild project / IAM roles / CodeArtifact
resources immediately and independently of git, which is exactly what made several rounds of
#346 look like a failure when the real fix just hadn't reached `main` yet.

```bash
git checkout main && git pull --ff-only
```

## 1. Trigger and poll

```bash
aws codepipeline start-pipeline-execution --name snack-recommender-app-pipeline
```

Poll in the background rather than sleeping inline (use the Bash tool's `run_in_background`):

```bash
for i in $(seq 1 30); do
  status=$(aws codepipeline get-pipeline-execution --pipeline-name snack-recommender-app-pipeline \
    --pipeline-execution-id <EXECUTION_ID> --query 'pipelineExecution.status' --output text 2>&1)
  echo "$(date +%H:%M:%S) status=$status"
  if [ "$status" != "InProgress" ]; then break; fi
  sleep 20
done
```

## 2. Find what actually failed

```bash
aws codepipeline get-pipeline-state --name snack-recommender-app-pipeline 2>&1 | python -c "
import json,sys
d=json.load(sys.stdin)
for s in d['stageStates']:
    le = s.get('latestExecution', {})
    print(s['stageName'], le.get('status'))
    for a in s.get('actionStates', []):
        le2 = a.get('latestExecution', {})
        print('  ', a['actionName'], le2.get('status'), le2.get('errorDetails',{}).get('message','')[:400])
"
```

This tells you which stage failed (`Build` → CodeBuild log; `Deploy_<env>` → EB instance log) and
usually enough of the error message to know which of the two to pull.

## 3. Pull the real log — Windows Git Bash gotchas handled

See `.claude/rules/windows-dev-environment.md` for why `MSYS_NO_PATHCONV=1` and
`PYTHONIOENCODING=utf-8`/`PYTHONUTF8=1` matter here. Set both on the same line as the `aws` call
below — exports don't persist across separate Bash tool invocations.

### CodeBuild log (Build stage failed)

```bash
# Get the build id from the failed action
aws codepipeline get-pipeline-state --name snack-recommender-app-pipeline \
  --query "stageStates[?stageName=='Build'].actionStates[0].latestExecution.externalExecutionId" --output text

export MSYS_NO_PATHCONV=1
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
LOGFILE="<scratchpad>/buildlog.json"
OUTFILE="<scratchpad>/buildlog.txt"
aws logs get-log-events --log-group-name "/aws/codebuild/<ProjectLogicalId>" \
  --log-stream-name "<build-id-after-the-colon>" --start-from-head --limit 10000 \
  --output json > "$LOGFILE" 2>&1
# wc -l "$LOGFILE" -- if it's only ~5 lines, the fetch itself crashed; retry, it's transient.

python -c "
import json
d = json.load(open(r'$LOGFILE', encoding='utf-8'))
with open(r'$OUTFILE', 'w', encoding='utf-8') as f:
    for e in d['events']:
        f.write(e['message'] + chr(10))
"
grep -n -i "error\|fail\|exit status" "$OUTFILE" | tail -60
```

Write the parsed output with `f.write(..., encoding='utf-8')`, never `print()` — `print()` still
routes through the Windows console codepage even when stdout is redirected to a file, and will
hit the same charmap crash downstream.

### EB instance log (a `Deploy_<env>` stage failed)

```bash
aws elasticbeanstalk request-environment-info --environment-name snack-recommender-<env> --info-type tail
sleep 15
URL=$(aws elasticbeanstalk retrieve-environment-info --environment-name snack-recommender-<env> \
  --info-type tail --query 'EnvironmentInfo[0].Message' --output text)

export MSYS_NO_PATHCONV=1
curl -s "$URL" -o "<scratchpad>/eb_tail.log"
grep -n -i "error\|codeartifact\|prebuild\|hook\|ModuleNotFound\|AccessDenied\|unbound" "<scratchpad>/eb_tail.log" | tail -60
```

The tail log concatenates *all* recent deploy attempts, not just the latest — match on timestamp
(the `[Container] <timestamp>` lines) to find the attempt that corresponds to the execution you
just triggered, not an older one.

To confirm a fix actually runs on the live instance (not just that the deploy succeeded), hit the
app directly and re-pull the log:

```bash
curl -s "http://$(aws elasticbeanstalk describe-environments --environment-names snack-recommender-<env> \
  --query 'Environments[0].CNAME' --output text)/health"
```

## 4. IAM AccessDenied / exit-254-type failures

Don't trust memory or docs for which resource type (domain vs. repository vs. package, for
CodeArtifact specifically — see CLAUDE.md) an IAM action actually needs. Settle it empirically
against the real deployed role:

```bash
ROLE_ARN=$(aws codebuild batch-get-projects --names <ProjectLogicalId> --query 'projects[0].serviceRole' --output text)
aws iam simulate-principal-policy --policy-source-arn "$ROLE_ARN" \
  --action-names <the-action> --resource-arns "<candidate-resource-arn>" \
  --query 'EvaluationResults[0].EvalDecision' --output text
```

`implicitDeny` with no matching statement means that resource type is wrong for that action, not
that the grant itself is missing — try other resource-type shapes (domain / repository / package)
before assuming the policy needs broadening.

## 5. Common root causes already found once (check these first)

- **Fix verified "failing" that actually isn't merged to `main` yet** — see step 0.
- **IAM resource-type mismatch** — step 4.
- **A missing permission masked by a `2>/dev/null || echo 0` fallback** — if a script treats "the
  check command failed" the same as "the check returned a negative answer," an AccessDenied looks
  identical to "not found." Don't swallow stderr on a command whose exit code feeds logic.
- **Shell state not surviving across separate buildspec `commands` entries** — CodeBuild runs each
  line with persistent `cwd`, but plain variable assignments aren't guaranteed to carry over to
  the next entry. Chain dependent steps with `&&` in one command string instead.
- **EB prebuild hooks (`.platform/hooks/prebuild/`) running before EB has materialized "Software:
  environment properties" into the shell** — a custom env var that works fine in a predeploy/
  postdeploy hook can be genuinely unset in a prebuild hook. Hardcode truly static values instead
  of threading them through EB env vars if this bites.
