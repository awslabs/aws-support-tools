=Purpose=

This tool downloads the test's output (e.g. logs, videos, artifacts) from a given AWS Device Farm console URL.

The downloaded output file can be shared to AWS support for troubleshooting issues occurred while the test was executed on Device Farm.

It works with these types of URLs from AWS Device Farm console:

  - Andorid and iOS device tests, i.e. the console URL of a run, a job, a suite or a specific test.
  - Browser/test-grid tests

=Usage=

 $ test-output-downloader.sh <console-URL>

 e.g.
 $ test-output-downloader.sh 'https://us-west-2.console.aws.amazon.com/devicefarm/home?#/projects/12345678-abcd-abcd-abcd-1234567890ab/runsselenium/logs/1234567890abcdefghijklmnopqrstuv'

=Platform=

Tested working on the following systems (with AWSCLI preinstalled installed):
  - MacOS
  - Amazon Linux
  - Windows (using Git for Windows, Reference[1])

=How it works=

1. The tool takes only one parameter: the URL of a test run, a test job, a test suite, or a specific test from AWS Device Farm console.

2. The tool has the following logic:

  A: Verify the input URL to ensure it is a valid Device Farm console URL.
  B: Check if AWSCLI is installed, if not, prompt to install, then exit (To install AWSCLI, refer to Reference[2]).
  C: Check if the AWSCLI default profile has access to Device Farm service. If not, prompt the user to fix the permission/profile then exit.
  D: Parse the URL to retrieve the following data from it:
     1. For Device tests: run ID, job ID, suite ID, test ID, then print it on the screen.
     2. For Browser/test-grid tests: project ID, session ID.
  E: Download all the test output (logs, screenshots, videos, artifacts) using the above IDs to the current user folder.
  F: Compress the downloaded files into a .tgz file, then print out the .tgz file's path and name for retrieval.
  G: Delete the downloaded files from the current folder.

=Limitations=

Some known limitations:

A: Only default AWSCLI profile is used to access Device Farm service
B: Use the platform's pre-installed tool: bash, curl, sed, grep as well as AWSCLI
C: Currently does not provide an option to specify the type of test output to download

=Known Issues=

N/A

=References=
[1] https://git-scm.com/download/win
[2] https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html
