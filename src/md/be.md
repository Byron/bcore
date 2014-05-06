## A universal commandline tool (UTC)

![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

In order to prevent everyone to be forced to do her *very own thing*™, it's vital to provide an official place into which to hook in functionality. That way, IT will be happy as they just have to put a single command in the executable search PATH, and the user will be happy as all he has to know is a single tool to get started.

**The context** if the command is extremely important, as it defines its startup environment. After all, it is likely to be installed in a central and 'blank' location that doesn't do much by itself. Its context will provide it with the information about which plugins to load, and essentially what its functionality will look like.

As *graphical environments* are fundamental different in requirements from a standard commandline application, a separately configurable variant of the *UCT* exists in the form of the [beg](link to bgui docs).

The default UCT should be launched through the standard python interpreter, yet it must be trivially easy to make it launch through another interpreter.


# FEATURES (DRAFT)

* sub-commands can have their own subcommands, and use the plugin system/base implementation to deal with it. That way (applause), you can take a previous main command, and make it a sub-command, therefore combine multiple commands into one if you are inclined to do so.
* thanks to be, departments can write a plugin that integrates their own subcommand into `be`, but only if they are within their own department context. That way, not everyone will see custom tools, whereas departments still get to see their own stuff through the company's main command. However, this would mean they have their own assembly, which could easily be the case for IT for instance.
