# red-teaming

A collection of tools that I use for red teaming.

ideas
* iptables-uwu https://github.com/benjojo/iptables-uwu
* requestor
* teatime
* nyancat https://github.com/klange/nyancat
* doubletap (aka alarm-clock)
* write down breaks

Setup - main
apt update
apt install -y python3 python3-pip sshpass pwgen openjdk-8-jdk
pip3 install ansible argcomplete
activate-global-python-argcomplete
git clone https://github.com/Guac0/red-teaming
cd red-teaming
ansible-galaxy install -r requirements.yml

Setup - opensearch. This needs to be separate because its stupid.
git clone https://github.com/opensearch-project/ansible-playbook
Configure the node properties in the inventories/opensearch/hosts file:
* ansible_host=<Public IP address> ansible_user=root ansible_password=root ip=0.0.0.0
* where ansible_host is the IP address of the target node that you want the Ansible playbook to install OpenSearch and OpenSearch DashBoards on.
* ip is the IP address that you want OpenSearch and OpenSearch DashBoards to bind to. You can specify the private IP of the target node, or localhost, or 0.0.0.0.
* remove all other hosts
Configure inventories/opensearch/group_vars/all/all.yml changes:
* cluster_type: single-node
* xms_value: 8
* xmx_value: 8
* os_version: "2.15.0"
* os_dashboards_version: "2.15.0"
ansible-playbook -i inventories/opensearch/hosts opensearch.yml --extra-vars "admin_password=TestStrong@123 kibanaserver_password=TestStrong@123 logstash_password=TestStrong@123"
curl https://localhost:9200 -u 'admin:TestStrong@123' --insecure

ansible -c to check - https://docs.ansible.com/ansible/latest/community/other_tools_and_programs.html#validate-playbook-tools
ansible-lint verify-apache.yml

ansible -i inventory.yaml playbook.yaml -c -t tag -vv
ansible-playbook -i inventory/ -f 200 -l {team_numbers} -t {role_tag} -vv windows.yaml