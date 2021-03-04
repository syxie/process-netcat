Process Netcat
==============

Flexible program to send process lists between servers.
```
Usage: Process Netcat

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -c CLIENT, --client=CLIENT
                        Address to connect to (client mode)
  -p PORT, --port=PORT  Port to connect to (client mode) or listen on (server
                        mode)
  -w WHITELIST, --whitelist=WHITELIST
                        Whitelist of addresses to allow (server mode)
  -s, --send            We will send the PS output
  -f FILE, --file=FILE  File to store JSON from tasks into
```

  When run without arguments, this script will listen on port 1876 and accept connections from anywhere:
  ```
» ./main.py
[-] Starting up in server mode on port 1876
```

We can limit this with a whitelist:
```
» ./main.py -w 127.0.0.1
[-] Starting up in server mode on port 1876
```
This will only allow connections from `127.0.0.1`.

To connect, let's run this in another pane, or on another machine (changing the IPs):
```
» ./main.py -c 127.0.0.1 -s
[-] Starting up in client mode to 127.0.0.1
[-] Connection: 127.0.0.1
[-] Received OK from server
[-] Starting PS transmission
[-] Sent tasks
```

As you can see, you will need to specify the `-s` flag if you would like to send the task output.

If you omit it, both the server and the client will alert you to either both sides, or neither side sending the tasks output:

Server side messages:
```
[-] Neither side is sending PS output, please configure the -s flag on one side
--
[-] We're both sending PS output, please configure the -s flag only on one side
```

Client side messages:
```
[-] Error from the other side: Neither side is sending PS output, please configure the -s flag on one side
--
[-] Error from the other side: We're both sending PS output, please configure the -s flag only on one side
```

When run successfully, here is the output on the server side:
```
» ./main.py
[-] Starting up in server mode on port 1876
[-] Connection: 127.0.0.1
[-] OK: They are sending PS
[-] Received tasks from 127.0.0.1
[-] Received tasks from 127.0.0.1
[-] Received tasks from 127.0.0.1
```

And the client side:
```
» ./main.py -c 127.0.0.1 -s
[-] Starting up in client mode to 127.0.0.1
[-] Connection: 127.0.0.1
[-] Received OK from server
[-] Starting PS transmission
[-] Sent tasks
[-] Sent tasks
[-] Sent tasks
```

You can control the file the tasks get stored with by setting the `-f` parameter.
The default is `tasks.json`. The format is like this:
```
{
    "1": {
        "name": "runit",
        "status": "sleeping",
        "created": 1614352697.01
    },
    "2": {
        "name": "kthreadd",
        "status": "sleeping",
        "created": 1614352697.01
    },
    "3": {
        "name": "rcu_gp",
        "status": "idle",
        "created": 1614352697.12
    },
    "4": {
        "name": "rcu_par_gp",
        "status": "idle",
        "created": 1614352697.12
    },
    "6": {
        "name": "kworker/0:0H-kblockd",
        "status": "idle",
        "created": 1614352697.12
    },
    "8": {
        "name": "mm_percpu_wq",
        "status": "idle",
        "created": 1614352697.12
    },
    "9": {
        "name": "rcu_tasks_kthre",
        "status": "sleeping",
        "created": 1614352697.12
    },
    "10": {
        "name": "rcu_tasks_rude_",
        "status": "sleeping",
        "created": 1614352697.12
    },
```

