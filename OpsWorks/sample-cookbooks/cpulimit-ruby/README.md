Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS"
BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under the License.

# cpulimit-ruby

In the case of CPU-critical workloads running on OpsWorks Stacks instances, the CPU consumption by Ruby processes during lifecycle events can affect the performance of applications running on instances. In stacks with many layers and instances, it is possible for a large series of Configure events to consume CPU resources for an extended period of time.

As this is a built in component of how Chef runs are performed; there is little that can be done by OpsWorks to limit the amount of CPU consumed by Ruby. However, we do have the ability to monitor and limit this on instances using a custom cookbook.

Specifically, we make use of a tool to control the CPU amount using SIGSTOP and SIGCONT POSIX signals. The benefit to using this tool is that child processes and threads are affected by this limit as well.

If you would like to instead configure this as a service to run on instances, continually checking for Ruby processes to limit, the attached cookbook will perform the following configuration tasks:

- Create the /opt/cpulimit directory to store any needed files.
- Create a file, /opt/cpulimit/cpulimit.sh, which acts in a similar manner to the script above, continuously checking for the existence of Ruby processes on the instance.
- Create a file, /etc/init.d/cpulimit, which registers cpulimit as a service on the instance.
- Starts and enables the new cpulimit service.

Once this is started on instances, any Ruby processes caught by the script cpulimit.sh will be throttled to less than 20% CPU for their duration. The percentage to throttle can be configured by adjusting the attribute default['cpulimit']['cpu-limit'], which can be found in attributes.rb in the provided cookbook.