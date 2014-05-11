## Command Framework

![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

* WHY
    - With `bcmd` it is already easy to create complex, plugin-based commands whose parsers can form arbitrary trees, and who are truly decoupled from each other thanks to [argparse's](https://docs.python.org/2/howto/argparse.html) awsomeness.
    - facilitate building plugin-based sub-commands with arbitrary hierarchies
    - write about nestable subcommand plugins, and the difference between the auto-version and maunal creation of sub-parsers


The command framework allows you to build commandline tools easily and in a unified way. 


## A simple command

This is how you define a simple command:

@snippet test_examples.py ExampleCommand

Provided you have wrapped your command using the \ref integration "Process Control Framework", you can
make calls like so:

```bash
./example
# prints nothing

./example -v
# prints something

./example -vvv
# prints a lot more

./example --version
# displays the version

./example -h
# displays usage information and detailed help
```

## A simple SubCommand

SubCommands allow you to create complex commands yet modularize that functionality nicely.
If we wanted to upgrade our example command with subcommands, we would just have to adjust it as follows

@snippet test_examples.py ExampleCommandWithSubcommands

Now you can call your master command as follows:

```bash
./master 
# prints usage

./master example --help
# displays 'example' mode specific help

./master example
# runs the example command, similarly to the standalone tool above

./master example -vvv
# run example in verbose mode
```

You can imagine that it is very easy to extend your command at runtime with plugins using the plugin system
inherent to the framework.

## Integration with Process Control

To make any command usable with the process control framework, all you have to do is to

- Symlink your command to the wrapper.py bootstrapper
- place a configuration yaml file in an ./etc folder to setup your process

In this example, we have a structure as follows:

```bash
hello_program/
├── bin
│   └── hello -> ../../../../bin/wrapper.py
├── etc
│   └── packages.yaml
└── lib
    └── hello.py
```

The file etc/packages.yaml would contain the following

@include hello_program/etc/packages.yaml

And the actual implementation looks like this:

@include hello_program/lib/hello.py
