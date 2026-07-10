## [v1.6.0] - 2026-07-10

### Removed
- `SES/SESReports/` folder. This CloudFormation-deployed Lambda tool targets end-of-life runtimes (Node.js aws-sdk v2 removed from Lambda, Python 2 syntax) and has not been maintained since 2019. For SES bounce/complaint reporting, use [Amazon Pinpoint email dashboards](https://docs.aws.amazon.com/pinpoint/latest/userguide/analytics-transactional-email.html). These scripts remain available at tag [v1.5.0](https://github.com/awslabs/aws-support-tools/tree/v1.5.0/SES/SESReports) for anyone who still needs them.

## [v1.5.0] - 2026-07-09

### Fixed
- **EC2/NitroInstanceChecks**: Replace fragile `cat /etc/os-release` with portable sourcing pattern; fixes error on RHEL 5/6 and silent failure on distros with unquoted ID values (#124)
- **Lambda/CheckFunctionConcurrency**: Paginate `list_functions` results (was silently capped at 50); replace `get_function` with lighter `get_function_concurrency` API; fix STS credential inconsistency in manual-key path; add exponential backoff for throttling (#207)
- **Lambda/FindEniMappings**: Detect non-Lambda ENIs (Grafana, ECS, RDS, ElastiCache, EFS) and warn the user before running Lambda-specific lookups (#215)
- **EBS/VolumeLimitCalculator**: Correct io2 Block Express throughput calculation; split io1/io2 into separate handlers with proper limits (256K IOPS, 4,000 MiB/s, 256 KiB I/O at all levels) (#228)

### Added
- **Lambda/FindEniMappings**: `--profile` flag for named AWS CLI profiles; fix infinite loop on unknown arguments; document CloudTrail permission requirement (#166)


# Changelog

All notable changes to this repository will be documented in this file.

## [v1.4.0] - 2026-07-08

### Removed
- 10 empty stub folders (CloudFront, CloudSearch, ElasticTranscoder, Glacier, IoT, MobileAnalytics, MobileHub, SQS, Snowball, StorageGateway). Each contained only a title-only README unchanged since the 2016 repo seed. Available at tag [v1.3.1](https://github.com/awslabs/aws-support-tools/tree/v1.3.1) if needed.

### Added
- Cross-reference READMEs for DRS/, MGN/, and MGNDRS/ explaining what each folder covers and linking to related folders

## [v1.3.1] - 2026-07-08

### Security
- Fixed clear-text logging of OneLogin access token in Cognito identity-pool-integrator (CodeQL HIGH)
- Added subresource integrity (SRI) hashes to CDN resources in SES/SESReports HTML templates (CodeQL MEDIUM x2)

## [v1.3.0] - 2026-07-08

### Added
- `EC2/NitroInstanceChecks/` - NVMe io_timeout kernel parameter check and grub configuration (PR #210, @iitggithub)

### Fixed
- `MWAA/verify_env/` - S3 client reference bug and missing json import (PR #247, @eason1128)
- `MWAA/tests/` - Test region list corrections, typo fix, added mock_s3control (PR #212, @ivica-k)
- `EMR/Assign_Private_IP/` - Python 3 compatibility (bytes decode, print syntax) (PR #241, @yiranwang0996)
- `EBS/VolumeLimitCalculator/` - Added throughput unit (MiB/s) to prompt, fixed gp2/gp3 comment (PR #219, @wafuwafu13)

### Changed
- `EC2/AutomateDnsmasq/` - Added Amazon Linux 2023 support, removed retired EC2-Classic references (PR #240, @sattyagrah)
- `Cognito/decode-verify-jwt/` - Rewrote TypeScript implementation to use official `aws-jwt-verify` library (PR #190, @ottokruse)
- `APIGateway/Tools/curl_for_latency/` - Refactored to accept CLI arguments, reuse TCP connections between requests (PR #227, @neilferreira)

### Closed (not merged)
- PR #251 (duplicate of #247), PR #201 (superseded by #190), PR #114 (incorrect semantic change), PR #125 (outdated Node.js/jose APIs), PR #200 (code issues, no go.mod)
- 11 conflicting PRs closed with invitation to resubmit (#173, #175, #183, #196, #202, #206, #213, #214, #221, #223, #244)

## [v1.2.0] - 2026-07-08

### Added
- `EKS/subnet-fragmentation/` - Diagnose /28 block fragmentation in VPC subnets for EKS prefix delegation (contributed by @SelimSkhiri, PR #257)
- `area: eks` label

## [v1.1.0] - 2026-07-08

### Added
- `CONTRIBUTING.md` with acceptance criteria, contribution paths for new and existing tools, testing and review expectations
- `SECURITY.md` (AWS vulnerability disclosure process via HackerOne)
- `CODE_OF_CONDUCT.md` (Amazon Open Source Code of Conduct)
- `.github/pull_request_template.md` with PR checklist and Apache 2.0 contribution statement
- `.github/ISSUE_TEMPLATE/` (bug report, feature request, question)
- `.github/LABELS.md` reference for the type/status/area label taxonomy
- `CHANGELOG.md`
- Root `README.md` rewritten with a full catalog of available tools organized by service

### Removed
- `DataPipeline/` folder. AWS Data Pipeline is in long-term maintenance mode. These scripts remain available at tag [v1.0.0](https://github.com/awslabs/aws-support-tools/tree/v1.0.0/DataPipeline) for anyone who still needs them.

## [v1.0.0] - 2026-07-08

Baseline tag marking the first release under active governance. No content changes from the prior state, only the addition of contributor guidelines, security policy, and templates.
