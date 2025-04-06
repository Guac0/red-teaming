#!/bin/bash
cat << 'EOF' > /bin/redd
#!/bin/bash
echo "Smash won't believe this!" >> /var/log/goudapot

log() {
    echo "$SSH_CLIENT $(date +"%A %r") -- $i" >> /var/log/goudapot
}

ri(){
    current_directory=$(pwd)
    echo -n "root@$HOSTNAME:$current_directory# "
    read -r i

    if [ -n "$i" ]; then
        case "$i" in 
            cd*)
                directory="${i#cd }"
                cd "$directory" 2>/dev/null
                log
                ;;
            whoami*)
                echo "root"
                log
                ;;
            touch*)
                echo "Too many open files"
                echo "Why are you touching my banana?"
                log
                ;;
            sed*)
                echo "sed: Couldn't re-allocate memory"
                log
                ;;
            cat*)
                echo "cat: No such file or directory ~meow"
                log
                ;;
            vim*)
                echo "vim: File not found/could not be created"
                log
                ;;
            nano*)
                echo "nano: File not found/could not be created"
                log
                ;;
            sudo*)
                echo "sudo: timestamp too far in the future"
                log
                ;;
            su*)
                echo "su: cannot set user id: Resource temporarily unavailable"
                log
                ;;
            ping*)
                echo "ping: Network unreachable"
                log
                ;;
            nc*)
                echo "nc: Address already in use"
                log
                ;;
            ls*)
                echo "ls: too many arguments"
                log
                ;;
            pwd*)
                pwd
                log
                ;;
            mkdir*)
                echo "mkdir: Failed to re-allocate memory"
                log
                ;;
            rmdir*)
                # It won't do anything. They will just be confused why it isn't
                # working :p
                log
                ;;
            mv*)
                # It won't do anything. They will just be confused why it isn't
                # working :p
                log
                ;;
            cp*)
                # It won't do anything. They will just be confused why it isn't
                # working :p
                log
                ;;
            rm*)
                # It won't do anything. They will just be confused why it isn't
                # working :p
                log
                ;;
            find*)
                echo "find: Segmentation fault (core dumped)"
                log
                ;;
            curl*)
                echo "curl: Destination unreachable"
                log
                ;;
            wget*)
                echo "wget: Destination unreachable"
                log
                ;;
            man*)
                $i
                log
                ;;
            iptables*)
                echo "iptables: firewall is locked"
                log
                ;;
            ip*)
                $i 2>/dev/null
                log
                ;;
            id*)
                ID=($(id | sed "s/$USER/root/g"))
                echo "uid=0(root) gid=0(root) groups=0(root)"
                log
                ;;
            echo*)
                $i 2>/dev/null

                log
                ;;
            chmod*)
                echo "chmod: arg1 arg2 banana"
                log
                ;;
            chown*)
                echo "chown: arg1 arg2 banana"
                log
                ;;
            grep*)
                echo "grep: banana"
                echo "Why are you grepping my banana?"
                log
                ;;
            which*)
                echo "which: a person who wields magic"
                log
                ;;
            exit*)
                log
                exit
                ;;
            *)
                echo "-bash: command not found: $i"
                logger "Honey - $i" 
                log
                ;;
        esac
    fi; 
    ri # Recursive call to continue reading commands
}
trap "ri" SIGINT SIGTSTP exit; 
ri
EOF


cp `which sh` /bin/newsh
cp `which bash` /bin/newbash

echo '#!/bin/newsh
echo "[$PPID `cat /proc/$PPID/comm`] /bin/bash -c $@" >> /var/log/gouda_bash
/bin/newbash "$@"' > /bin/bash
cp /bin/bash /usr/bin/bash

echo '#!/bin/newsh
echo "[$PPID `cat /proc/$PPID/comm`] /bin/sh -c $@" >> /var/log/gouda_bash
/bin/newsh "$@"' > /bin/sh
cp /bin/sh /usr/bin/sh

chattr +i /bin/bash
chattr +i /bin/sh

touch /var/log/gouda_bash
chmod 622 /var/log/gouda_bash

chmod +x /bin/redd
touch /var/log/goudapot
chmod 722 /var/log/goudapot
