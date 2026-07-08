# Label taxonomy

Not a file GitHub reads automatically. This documents the labels to be created on the
repo (via `gh label create` or the GitHub UI) so the taxonomy is versioned somewhere.

## type
- `type: bug`
- `type: feature-request`
- `type: question`
- `type: documentation`

## status
- `status: needs-triage`
- `status: needs-more-info`
- `status: stale`
- `status: duplicate`
- `status: wontfix`
- `status: accepted`

## area (one per active top-level folder)
`area: apigateway`, `area: cloudformation`, `area: cognito`, `area: connect`,
`area: devicefarm`, `area: ebs`, `area: ec2`,
`area: ec2-auto-scaling`, `area: emr`, `area: elasticsearch`, `area: fsx-netapp-ontap`,
`area: lambda`, `area: mgn`, `area: mgndrs`, `area: drs`, `area: mwaa`, `area: opsworks`,
`area: rds`, `area: s3`, `area: ses`, `area: sns`, `area: systems-manager`, `area: waf`

Excludes the 10 top-level folders that currently have no content.

## other
- `good first issue`
