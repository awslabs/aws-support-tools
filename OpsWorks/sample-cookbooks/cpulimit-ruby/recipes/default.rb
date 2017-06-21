#
# Cookbook:: cpulimit-ruby
# Recipe:: default
#
# Copyright:: 2017, The Authors, All Rights Reserved.

# Needed for make.
package 'gcc'

# Create the directory to hold:
#  - cpulimit.sh script
#  - cpulimit-master package
directory '/opt/cpulimit' do
  owner 'root'
  group 'root'
  mode '0755'
  action :create
end

# Create the script from the template.
# This is run by the cpulimit service.
template '/opt/cpulimit/cpulimit.sh' do
  source 'cpulimit.sh.erb'
  owner 'root'
  group 'root'
  mode '0755'
end

# Create the service from the template
template '/etc/init.d/cpulimit' do
  source 'cpulimit.erb'
  owner 'root'
  group 'root'
  mode '0755'
end

# Copy the compiled binary to /usr/bin.
execute 'cp' do
  command '[ -f /usr/bin/cpulimit ] && echo "cpulimit exists in /usr/bin" || cp ./src/cpulimit /usr/bin'
  cwd '/opt/cpulimit/cpulimit-master'
  action :nothing
end

# Compile cpulimit.
execute 'make' do
  command '[ -f /opt/cpulimit/cpulimit-master/cpulimit ] && echo "Make already completed." || make'
  cwd '/opt/cpulimit/cpulimit-master'
  action :nothing
  notifies :run, 'execute[cp]', :immediate
end

# Copy the cpulimit-master files.
remote_directory '/opt/cpulimit/cpulimit-master' do
  source 'cpulimit-master'
  owner 'root'
  group 'root'
  mode '0755'
  action :create_if_missing
  overwrite false
  notifies :run, 'execute[make]', :immediate
end

# Stop and start cpulimit.
service 'cpulimit' do
  action [ :enable, :start ]
  subscribes :restart, 'template[/etc/init.d/cpulimit]', :delayed
  subscribes :restart, 'template[/opt/cpulimit/cpulimit.sh]', :delayed
end