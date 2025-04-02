# red-teaming

A collection of tools that I use for red teaming.

ideas
* iptables-uwu https://github.com/benjojo/iptables-uwu
* requestor
* teatime
* nyancat https://github.com/klange/nyancat
* doubletap (aka alarm-clock)
* write down breaks

Setup
apt update
apt install -y python3 python3-pip sshpass pwgen
pip3 install ansible argcomplete
activate-global-python-argcomplete

ansible -c to check - https://docs.ansible.com/ansible/latest/community/other_tools_and_programs.html#validate-playbook-tools
ansible-lint verify-apache.yml

ansible -i inventory.yaml playbook.yaml -c -t tag -vv
ansible-playbook -i inventory/ -f 200 -l {team_numbers} -t {role_tag} -vv windows.yaml