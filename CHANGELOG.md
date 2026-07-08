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
